"""
Query analysis and index optimization tools.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.performance.database.connection_pool import db_manager

logger = logging.getLogger(__name__)


@dataclass
class IndexRecommendation:
    """Recommended index based on query analysis."""
    table_name: str
    columns: List[str]
    index_type: str
    where_clause: Optional[str] = None
    include_columns: Optional[List[str]] = None
    reason: str = ""
    estimated_improvement: str = ""


@dataclass
class SlowQuery:
    """Slow query information."""
    query: str
    calls: int
    total_time_ms: float
    mean_time_ms: float
    rows: int
    shared_blks_hit: int
    shared_blks_read: int


class QueryOptimizer:
    """
    Query analysis and optimization tools.

    Features:
    - Slow query detection
    - Missing index identification
    - Index usage analysis
    - Query plan analysis
    """

    async def get_slow_queries(
        self,
        min_duration_ms: float = 100,
        limit: int = 20
    ) -> List[SlowQuery]:
        """
        Get slow queries from pg_stat_statements.

        Requires pg_stat_statements extension.
        """
        if not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        try:
            async with db_manager.read_session() as session:
                result = await session.execute(text(f"""
                    SELECT
                        query,
                        calls,
                        total_exec_time as total_time_ms,
                        mean_exec_time as mean_time_ms,
                        rows,
                        shared_blks_hit,
                        shared_blks_read
                    FROM pg_stat_statements
                    WHERE mean_exec_time > {min_duration_ms}
                      AND query NOT LIKE '%pg_stat%'
                    ORDER BY mean_exec_time DESC
                    LIMIT {limit}
                """))

                queries = []
                for row in result.fetchall():
                    queries.append(SlowQuery(
                        query=row[0][:500],
                        calls=row[1],
                        total_time_ms=row[2],
                        mean_time_ms=row[3],
                        rows=row[4],
                        shared_blks_hit=row[5],
                        shared_blks_read=row[6]
                    ))

                return queries
        except Exception as e:
            logger.warning(f"Failed to get slow queries: {e}")
            return []

    async def get_missing_indexes(self) -> List[Dict[str, Any]]:
        """
        Find tables that might benefit from additional indexes.

        Based on sequential scan vs index scan ratio.
        """
        if not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        try:
            async with db_manager.read_session() as session:
                result = await session.execute(text("""
                    SELECT
                        schemaname,
                        relname as table_name,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_live_tup as row_count,
                        CASE WHEN seq_scan > 0
                             THEN round(seq_tup_read::numeric / seq_scan, 2)
                             ELSE 0
                        END as avg_seq_tup_per_scan
                    FROM pg_stat_user_tables
                    WHERE seq_scan > 100
                      AND n_live_tup > 10000
                      AND (idx_scan IS NULL OR seq_scan > idx_scan * 10)
                    ORDER BY seq_tup_read DESC
                    LIMIT 20
                """))

                tables = []
                for row in result.fetchall():
                    tables.append({
                        'schema': row[0],
                        'table': row[1],
                        'seq_scans': row[2],
                        'seq_tuples_read': row[3],
                        'index_scans': row[4] or 0,
                        'index_tuples_fetched': row[5] or 0,
                        'row_count': row[6],
                        'avg_seq_tuples_per_scan': float(row[7]),
                        'recommendation': 'Consider adding index'
                    })

                return tables
        except Exception as e:
            logger.warning(f"Failed to get missing indexes: {e}")
            return []

    async def get_unused_indexes(self) -> List[Dict[str, Any]]:
        """Find indexes that are never or rarely used."""
        if not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        try:
            async with db_manager.read_session() as session:
                result = await session.execute(text("""
                    SELECT
                        schemaname,
                        relname as table_name,
                        indexrelname as index_name,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes
                    WHERE idx_scan < 50
                      AND indexrelname NOT LIKE '%_pkey'
                      AND indexrelname NOT LIKE '%_pk'
                    ORDER BY pg_relation_size(indexrelid) DESC
                    LIMIT 20
                """))

                indexes = []
                for row in result.fetchall():
                    indexes.append({
                        'schema': row[0],
                        'table': row[1],
                        'index': row[2],
                        'scans': row[3],
                        'tuples_read': row[4],
                        'tuples_fetched': row[5],
                        'size': row[6],
                        'recommendation': 'Consider dropping if not needed for constraints'
                    })

                return indexes
        except Exception as e:
            logger.warning(f"Failed to get unused indexes: {e}")
            return []

    async def get_index_bloat(self) -> List[Dict[str, Any]]:
        """Find bloated indexes that might need reindexing."""
        if not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        try:
            async with db_manager.read_session() as session:
                result = await session.execute(text("""
                    WITH btree_index_atts AS (
                        SELECT
                            nspname,
                            indexrelname as index_name,
                            relname as table_name,
                            reltuples,
                            relpages,
                            indrelid,
                            pg_relation_size(indexrelid) as index_size
                        FROM pg_index
                        JOIN pg_class ON pg_class.oid = pg_index.indexrelid
                        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
                        JOIN pg_stat_user_indexes ON pg_stat_user_indexes.indexrelid = pg_index.indexrelid
                        WHERE pg_class.relam = (SELECT oid FROM pg_am WHERE amname = 'btree')
                    )
                    SELECT
                        nspname as schema,
                        table_name,
                        index_name,
                        pg_size_pretty(index_size) as size,
                        CASE WHEN reltuples > 0
                             THEN round((index_size / (reltuples * 32))::numeric, 2)
                             ELSE 0
                        END as bloat_ratio
                    FROM btree_index_atts
                    WHERE index_size > 10485760
                    ORDER BY index_size DESC
                    LIMIT 20
                """))

                indexes = []
                for row in result.fetchall():
                    bloat_ratio = float(row[4]) if row[4] else 0
                    indexes.append({
                        'schema': row[0],
                        'table': row[1],
                        'index': row[2],
                        'size': row[3],
                        'bloat_ratio': bloat_ratio,
                        'recommendation': 'REINDEX' if bloat_ratio > 2 else 'OK'
                    })

                return indexes
        except Exception as e:
            logger.warning(f"Failed to get index bloat: {e}")
            return []

    async def explain_query(
        self,
        query: str,
        analyze: bool = False
    ) -> Dict[str, Any]:
        """
        Get query execution plan.

        Args:
            query: SQL query to analyze
            analyze: Actually execute the query (more accurate but slower)
        """
        if not db_manager.is_available:
            return {"error": "Database not available"}

        try:
            from sqlalchemy import text
        except ImportError:
            return {"error": "SQLAlchemy not available"}

        explain_type = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)" if analyze else "EXPLAIN (FORMAT JSON)"

        try:
            async with db_manager.read_session() as session:
                result = await session.execute(
                    text(f"{explain_type} {query}")
                )
                plan = result.fetchone()[0]

                return {
                    'query': query[:500],
                    'plan': plan,
                    'total_cost': plan[0].get('Plan', {}).get('Total Cost') if plan else None,
                    'planning_time': plan[0].get('Planning Time') if analyze and plan else None,
                    'execution_time': plan[0].get('Execution Time') if analyze and plan else None
                }
        except Exception as e:
            return {"error": str(e)}

    async def generate_index_recommendations(
        self,
        table_name: str
    ) -> List[IndexRecommendation]:
        """Generate index recommendations for a specific table."""
        recommendations = []

        if not db_manager.is_available:
            return recommendations

        try:
            from sqlalchemy import text
        except ImportError:
            return recommendations

        try:
            async with db_manager.read_session() as session:
                result = await session.execute(text(f"""
                    SELECT
                        attname as column_name,
                        n_distinct,
                        correlation
                    FROM pg_stats
                    WHERE tablename = '{table_name}'
                    ORDER BY n_distinct DESC
                """))

                columns = result.fetchall()

                for col in columns:
                    col_name = col[0]
                    n_distinct = col[1]
                    correlation = col[2] or 0

                    if n_distinct and (n_distinct > 100 or n_distinct == -1):
                        recommendations.append(IndexRecommendation(
                            table_name=table_name,
                            columns=[col_name],
                            index_type='btree',
                            reason=f'High cardinality column (distinct={n_distinct})',
                            estimated_improvement='Potentially significant for lookups'
                        ))

                    if abs(correlation) > 0.9 and n_distinct and n_distinct > 1000:
                        recommendations.append(IndexRecommendation(
                            table_name=table_name,
                            columns=[col_name],
                            index_type='brin',
                            reason=f'High correlation ({correlation:.2f}), suitable for BRIN',
                            estimated_improvement='Good for range queries, small storage'
                        ))

        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")

        return recommendations


query_optimizer = QueryOptimizer()


RECOMMENDED_INDEXES_SQL = """
-- Partial indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_pending_due
ON invoices (tenant_id, due_date)
WHERE status = 'pending' AND deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_recent
ON transactions (tenant_id, created_at DESC)
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Covering indexes to avoid table lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_list_covering
ON invoices (tenant_id, status, created_at DESC)
INCLUDE (invoice_number, total_amount, client_id, due_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_search
ON clients (tenant_id, name)
INCLUDE (email, phone, status);

-- BRIN indexes for time-series data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_brin
ON audit_logs USING BRIN (created_at) WITH (pages_per_range = 128);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_created_brin
ON transactions USING BRIN (created_at) WITH (pages_per_range = 128);

-- GIN indexes for JSONB columns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_documents_metadata_gin
ON documents USING GIN (metadata);

-- Expression indexes for case-insensitive search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clients_name_lower
ON clients (tenant_id, LOWER(name));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower
ON users (LOWER(email));

-- Multi-column indexes for common joins
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_project_type
ON transactions (project_id, type)
WHERE project_id IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoice_items_invoice
ON invoice_items (invoice_id, item_order);
"""
