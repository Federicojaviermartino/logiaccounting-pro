"""
Database connection manager with read replica support and connection pooling.
"""
import asyncio
import logging
from typing import Any, Optional, List, AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum

try:
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
        AsyncEngine
    )
    from sqlalchemy.pool import QueuePool, NullPool
    from sqlalchemy import event, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from app.performance.config import settings

logger = logging.getLogger(__name__)


class DatabaseRole(str, Enum):
    """Database connection roles."""
    PRIMARY = "primary"
    REPLICA = "replica"
    ANALYTICS = "analytics"


class DatabaseConfig:
    """Database configuration settings."""

    PRIMARY_URL: str = settings.DATABASE_URL
    REPLICA_URLS: List[str] = [
        settings.DATABASE_REPLICA_1_URL,
        settings.DATABASE_REPLICA_2_URL,
    ]

    POOL_SIZE: int = settings.DB_POOL_SIZE
    MAX_OVERFLOW: int = settings.DB_MAX_OVERFLOW
    POOL_TIMEOUT: int = settings.DB_POOL_TIMEOUT
    POOL_RECYCLE: int = settings.DB_POOL_RECYCLE
    POOL_PRE_PING: bool = True

    STATEMENT_TIMEOUT: int = 30000
    LOCK_TIMEOUT: int = 10000


class DatabaseManager:
    """
    Database connection manager with read/write splitting.

    Features:
    - Automatic read/write routing
    - Connection pooling
    - Health monitoring
    - Load balancing across replicas
    """

    _instance: Optional['DatabaseManager'] = None
    _primary_engine: Optional[Any] = None
    _replica_engines: List[Any] = []
    _replica_index: int = 0
    _primary_session_factory: Optional[Any] = None
    _replica_session_factory: Optional[Any] = None
    _initialized: bool = False

    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """Initialize database connections."""
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available for async database connections")
            return

        if self._initialized:
            return

        if "sqlite" in DatabaseConfig.PRIMARY_URL:
            logger.info("Using SQLite - skipping advanced connection pooling")
            self._initialized = True
            return

        try:
            self._primary_engine = self._create_engine(
                DatabaseConfig.PRIMARY_URL,
                pool_size=DatabaseConfig.POOL_SIZE,
                max_overflow=DatabaseConfig.MAX_OVERFLOW
            )

            self._primary_session_factory = async_sessionmaker(
                bind=self._primary_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )

            for url in DatabaseConfig.REPLICA_URLS:
                if url:
                    try:
                        engine = self._create_engine(
                            url,
                            pool_size=DatabaseConfig.POOL_SIZE // 2,
                            max_overflow=DatabaseConfig.MAX_OVERFLOW // 2
                        )
                        self._replica_engines.append(engine)
                    except Exception as e:
                        logger.warning(f"Failed to connect to replica: {e}")

            if not self._replica_engines:
                self._replica_engines = [self._primary_engine]
                logger.warning("No replicas available, using primary for reads")

            self._replica_session_factory = async_sessionmaker(
                bind=self._replica_engines[0],
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )

            self._setup_event_listeners()
            self._initialized = True

            logger.info(
                f"Database initialized: 1 primary, {len(self._replica_engines)} replicas"
            )

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _create_engine(
        self,
        url: str,
        pool_size: int,
        max_overflow: int
    ) -> Any:
        """Create SQLAlchemy async engine."""
        connect_args = {}

        if "postgresql" in url:
            connect_args = {
                "command_timeout": DatabaseConfig.STATEMENT_TIMEOUT // 1000,
            }

        return create_async_engine(
            url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=DatabaseConfig.POOL_TIMEOUT,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            pool_pre_ping=DatabaseConfig.POOL_PRE_PING,
            echo=settings.DEBUG,
            connect_args=connect_args
        )

    def _setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for monitoring."""
        if not self._primary_engine:
            return

        @event.listens_for(self._primary_engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = asyncio.get_event_loop().time()

        @event.listens_for(self._primary_engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total = asyncio.get_event_loop().time() - context._query_start_time
            if total > 1.0:
                logger.warning(
                    f"Slow query ({total:.2f}s): {statement[:200]}..."
                )

    @property
    def is_available(self) -> bool:
        """Check if database is available."""
        return SQLALCHEMY_AVAILABLE and self._initialized

    @property
    def primary(self) -> Any:
        """Get primary engine for writes."""
        if not self.is_available or self._primary_engine is None:
            raise RuntimeError("Database not initialized")
        return self._primary_engine

    @property
    def replica(self) -> Any:
        """Get replica engine for reads (round-robin)."""
        if not self._replica_engines:
            return self.primary

        self._replica_index = (self._replica_index + 1) % len(self._replica_engines)
        return self._replica_engines[self._replica_index]

    @asynccontextmanager
    async def session(
        self,
        role: DatabaseRole = DatabaseRole.PRIMARY
    ) -> AsyncGenerator[Any, None]:
        """
        Get database session based on role.

        Args:
            role: Database role (primary, replica, analytics)

        Yields:
            AsyncSession
        """
        if not self.is_available:
            raise RuntimeError("Database not initialized")

        if role == DatabaseRole.PRIMARY:
            engine = self.primary
        else:
            engine = self.replica

        async with async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @asynccontextmanager
    async def write_session(self) -> AsyncGenerator[Any, None]:
        """Get session for write operations."""
        async with self.session(DatabaseRole.PRIMARY) as session:
            yield session
            await session.commit()

    @asynccontextmanager
    async def read_session(self) -> AsyncGenerator[Any, None]:
        """Get session for read operations (from replica)."""
        async with self.session(DatabaseRole.REPLICA) as session:
            yield session

    async def execute_on_replica(self, query: str, params: dict = None):
        """Execute raw query on replica."""
        async with self.read_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()

    async def health_check(self) -> dict:
        """Check database health."""
        result = {
            "available": self.is_available,
            "primary": {"healthy": False, "latency_ms": None},
            "replicas": []
        }

        if not self.is_available:
            return result

        try:
            start = asyncio.get_event_loop().time()
            async with self.write_session() as session:
                await session.execute(text("SELECT 1"))
            result["primary"]["latency_ms"] = (
                asyncio.get_event_loop().time() - start
            ) * 1000
            result["primary"]["healthy"] = True
        except Exception as e:
            logger.error(f"Primary health check failed: {e}")

        for i, engine in enumerate(self._replica_engines):
            replica_result = {"index": i, "healthy": False, "latency_ms": None}
            try:
                start = asyncio.get_event_loop().time()
                async with async_sessionmaker(
                    bind=engine, class_=AsyncSession
                )() as session:
                    await session.execute(text("SELECT 1"))
                replica_result["latency_ms"] = (
                    asyncio.get_event_loop().time() - start
                ) * 1000
                replica_result["healthy"] = True
            except Exception as e:
                logger.error(f"Replica {i} health check failed: {e}")

            result["replicas"].append(replica_result)

        return result

    async def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if not self.is_available or not self._primary_engine:
            return {"error": "Database not initialized"}

        primary_pool = self._primary_engine.pool

        return {
            "primary": {
                "size": primary_pool.size(),
                "checked_in": primary_pool.checkedin(),
                "checked_out": primary_pool.checkedout(),
                "overflow": primary_pool.overflow(),
            },
            "replicas": [
                {
                    "index": i,
                    "size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                }
                for i, engine in enumerate(self._replica_engines)
            ]
        }

    async def close(self) -> None:
        """Close all database connections."""
        if self._primary_engine:
            await self._primary_engine.dispose()
            self._primary_engine = None

        for engine in self._replica_engines:
            await engine.dispose()
        self._replica_engines = []
        self._initialized = False

        logger.info("Database connections closed")


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[Any, None]:
    """FastAPI dependency for write operations."""
    async with db_manager.write_session() as session:
        yield session


async def get_read_db() -> AsyncGenerator[Any, None]:
    """FastAPI dependency for read operations (uses replica)."""
    async with db_manager.read_session() as session:
        yield session
