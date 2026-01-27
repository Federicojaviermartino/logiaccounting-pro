"""
Database Optimization Module - Read replicas, connection pooling, and query optimization.

Components:
- connection_pool: Database connection manager with read replica support
- read_replica: Intelligent query routing
- materialized_views: MV definitions and refresh management
- partitioning: Table partitioning strategies
- query_optimizer: Query analysis and index recommendations
"""

from app.performance.database.connection_pool import (
    DatabaseManager,
    db_manager,
    DatabaseRole,
    get_db,
    get_read_db
)
from app.performance.database.read_replica import (
    QueryRouter,
    ReadReplicaSession,
    route_to_replica
)
from app.performance.database.materialized_views import (
    MaterializedViewManager,
    mv_manager
)
from app.performance.database.partitioning import (
    PartitionManager,
    partition_manager
)
from app.performance.database.query_optimizer import (
    QueryOptimizer,
    query_optimizer
)

__all__ = [
    "DatabaseManager",
    "db_manager",
    "DatabaseRole",
    "get_db",
    "get_read_db",
    "QueryRouter",
    "ReadReplicaSession",
    "route_to_replica",
    "MaterializedViewManager",
    "mv_manager",
    "PartitionManager",
    "partition_manager",
    "QueryOptimizer",
    "query_optimizer",
]
