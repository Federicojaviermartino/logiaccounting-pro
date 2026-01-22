"""
Read replica routing and query optimization.
"""
import logging
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
import asyncio

from app.performance.database.connection_pool import db_manager, DatabaseRole

logger = logging.getLogger(__name__)

T = TypeVar('T')


def route_to_replica(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to route read queries to replica.

    Usage:
        @route_to_replica
        async def get_all_invoices(db: AsyncSession):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        if 'db' in kwargs:
            async with db_manager.read_session() as replica_session:
                kwargs['db'] = replica_session
                return await func(*args, **kwargs)
        return await func(*args, **kwargs)

    return wrapper


class QueryRouter:
    """
    Intelligent query router that decides primary vs replica.

    Routes to replica:
    - SELECT queries without FOR UPDATE
    - Aggregate queries
    - Queries marked as read-only

    Routes to primary:
    - INSERT, UPDATE, DELETE
    - SELECT FOR UPDATE
    - Queries in a transaction with writes
    """

    @staticmethod
    def should_use_replica(query: str) -> bool:
        """Determine if query should use replica."""
        query_upper = query.upper().strip()

        if any(query_upper.startswith(op) for op in ['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']):
            return False

        if 'FOR UPDATE' in query_upper or 'FOR SHARE' in query_upper:
            return False

        if any(query_upper.startswith(op) for op in ['CREATE', 'ALTER', 'DROP']):
            return False

        if query_upper.startswith('SELECT') or query_upper.startswith('WITH'):
            return True

        return False

    @staticmethod
    async def execute(
        query: str,
        params: dict = None,
        force_primary: bool = False
    ) -> Any:
        """
        Execute query with automatic routing.

        Args:
            query: SQL query string
            params: Query parameters
            force_primary: Force use of primary database
        """
        role = DatabaseRole.PRIMARY

        if not force_primary and QueryRouter.should_use_replica(query):
            role = DatabaseRole.REPLICA

        async with db_manager.session(role) as session:
            try:
                from sqlalchemy import text
            except ImportError:
                logger.error("SQLAlchemy not available")
                return None
            result = await session.execute(text(query), params or {})
            return result


class ReadReplicaSession:
    """
    Context manager for read-only sessions with replica preference.

    Usage:
        async with ReadReplicaSession() as session:
            result = await session.execute(query)
    """

    def __init__(self, max_lag_seconds: int = 5):
        """
        Args:
            max_lag_seconds: Maximum acceptable replication lag
        """
        self.max_lag_seconds = max_lag_seconds
        self._session: Optional[Any] = None
        self._context: Optional[Any] = None

    async def __aenter__(self) -> Any:
        lag = await self._get_replication_lag()

        if lag is not None and lag > self.max_lag_seconds:
            logger.warning(
                f"Replication lag ({lag}s) exceeds threshold, using primary"
            )
            self._context = db_manager.session(DatabaseRole.PRIMARY)
        else:
            self._context = db_manager.session(DatabaseRole.REPLICA)

        self._session = await self._context.__aenter__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            await self._context.__aexit__(exc_type, exc_val, exc_tb)

    async def _get_replication_lag(self) -> Optional[float]:
        """Get current replication lag in seconds."""
        if not db_manager.is_available:
            return None

        try:
            async with db_manager.session(DatabaseRole.REPLICA) as session:
                try:
                    from sqlalchemy import text
                except ImportError:
                    return None

                result = await session.execute(text("""
                    SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp()))
                    AS lag_seconds
                """))
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.warning(f"Failed to get replication lag: {e}")
            return None


class QueryHints:
    """
    Query hints for optimization.
    """

    @staticmethod
    def parallel_query(workers: int = 4) -> str:
        """Enable parallel query execution."""
        return f"/*+ Parallel({workers}) */"

    @staticmethod
    def index_hint(index_name: str) -> str:
        """Suggest using specific index."""
        return f"/*+ IndexScan({index_name}) */"

    @staticmethod
    def no_cache() -> str:
        """Disable query cache."""
        return "/*+ NoCache */"

    @staticmethod
    def timeout(seconds: int) -> str:
        """Set query timeout."""
        return f"SET statement_timeout = '{seconds}s';"
