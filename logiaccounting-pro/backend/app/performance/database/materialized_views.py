"""
Materialized views for analytics and dashboard performance.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.performance.database.connection_pool import db_manager, DatabaseRole

logger = logging.getLogger(__name__)


class MaterializedViewDefinitions:
    """SQL definitions for materialized views."""

    MV_DAILY_REVENUE = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_revenue AS
    SELECT
        tenant_id,
        DATE(created_at) as date,
        type as transaction_type,
        SUM(amount) as total_amount,
        COUNT(*) as transaction_count,
        AVG(amount) as avg_amount
    FROM transactions
    WHERE deleted_at IS NULL
      AND created_at >= CURRENT_DATE - INTERVAL '365 days'
    GROUP BY tenant_id, DATE(created_at), type
    WITH DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_revenue_pk
    ON mv_daily_revenue (tenant_id, date, transaction_type);

    CREATE INDEX IF NOT EXISTS idx_mv_daily_revenue_tenant
    ON mv_daily_revenue (tenant_id, date DESC);
    """

    MV_INVOICE_AGING = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_invoice_aging AS
    SELECT
        i.tenant_id,
        i.client_id,
        c.name as client_name,
        COUNT(*) FILTER (WHERE i.status = 'pending' AND i.due_date >= CURRENT_DATE) as current_count,
        SUM(i.total_amount) FILTER (WHERE i.status = 'pending' AND i.due_date >= CURRENT_DATE) as current_amount,
        COUNT(*) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE AND i.due_date >= CURRENT_DATE - 30) as days_1_30_count,
        SUM(i.total_amount) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE AND i.due_date >= CURRENT_DATE - 30) as days_1_30_amount,
        COUNT(*) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE - 30 AND i.due_date >= CURRENT_DATE - 60) as days_31_60_count,
        SUM(i.total_amount) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE - 30 AND i.due_date >= CURRENT_DATE - 60) as days_31_60_amount,
        COUNT(*) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE - 60 AND i.due_date >= CURRENT_DATE - 90) as days_61_90_count,
        SUM(i.total_amount) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE - 60 AND i.due_date >= CURRENT_DATE - 90) as days_61_90_amount,
        COUNT(*) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE - 90) as over_90_count,
        SUM(i.total_amount) FILTER (WHERE i.status = 'pending' AND i.due_date < CURRENT_DATE - 90) as over_90_amount
    FROM invoices i
    JOIN clients c ON i.client_id = c.id
    WHERE i.deleted_at IS NULL
    GROUP BY i.tenant_id, i.client_id, c.name
    WITH DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_invoice_aging_pk
    ON mv_invoice_aging (tenant_id, client_id);
    """

    MV_PROJECT_PROFITABILITY = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_project_profitability AS
    SELECT
        p.tenant_id,
        p.id as project_id,
        p.name as project_name,
        p.status,
        p.budget,
        COALESCE(SUM(t.amount) FILTER (WHERE t.type = 'income'), 0) as total_revenue,
        COALESCE(SUM(t.amount) FILTER (WHERE t.type = 'expense'), 0) as total_expenses,
        COALESCE(SUM(t.amount) FILTER (WHERE t.type = 'income'), 0) -
        COALESCE(SUM(t.amount) FILTER (WHERE t.type = 'expense'), 0) as profit,
        CASE
            WHEN p.budget > 0 THEN
                ROUND((COALESCE(SUM(t.amount) FILTER (WHERE t.type = 'expense'), 0) / p.budget) * 100, 2)
            ELSE 0
        END as budget_utilization_pct,
        COUNT(DISTINCT t.id) as transaction_count,
        MIN(t.created_at) as first_transaction_date,
        MAX(t.created_at) as last_transaction_date
    FROM projects p
    LEFT JOIN transactions t ON p.id = t.project_id AND t.deleted_at IS NULL
    WHERE p.deleted_at IS NULL
    GROUP BY p.tenant_id, p.id, p.name, p.status, p.budget
    WITH DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_project_profit_pk
    ON mv_project_profitability (tenant_id, project_id);

    CREATE INDEX IF NOT EXISTS idx_mv_project_profit_status
    ON mv_project_profitability (tenant_id, status);
    """

    MV_CLIENT_STATS = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_client_stats AS
    SELECT
        c.tenant_id,
        c.id as client_id,
        c.name as client_name,
        COUNT(DISTINCT i.id) as total_invoices,
        COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'paid') as paid_invoices,
        COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'pending') as pending_invoices,
        COUNT(DISTINCT i.id) FILTER (WHERE i.status = 'overdue') as overdue_invoices,
        COALESCE(SUM(i.total_amount), 0) as total_billed,
        COALESCE(SUM(i.total_amount) FILTER (WHERE i.status = 'paid'), 0) as total_paid,
        COALESCE(SUM(i.total_amount) FILTER (WHERE i.status IN ('pending', 'overdue')), 0) as total_outstanding,
        MAX(i.created_at) as last_invoice_date
    FROM clients c
    LEFT JOIN invoices i ON c.id = i.client_id AND i.deleted_at IS NULL
    WHERE c.deleted_at IS NULL
    GROUP BY c.tenant_id, c.id, c.name
    WITH DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_client_stats_pk
    ON mv_client_stats (tenant_id, client_id);
    """

    MV_MONTHLY_SUMMARY = """
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_summary AS
    SELECT
        t.tenant_id,
        DATE_TRUNC('month', t.created_at) as month,
        SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END) as total_income,
        SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END) as total_expenses,
        SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END) -
        SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END) as net_income,
        COUNT(*) FILTER (WHERE t.type = 'income') as income_count,
        COUNT(*) FILTER (WHERE t.type = 'expense') as expense_count
    FROM transactions t
    WHERE t.deleted_at IS NULL
      AND t.created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '24 months')
    GROUP BY t.tenant_id, DATE_TRUNC('month', t.created_at)
    WITH DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_monthly_summary_pk
    ON mv_monthly_summary (tenant_id, month);
    """


class MaterializedViewManager:
    """
    Manager for materialized view lifecycle.

    Features:
    - Create/drop views
    - Concurrent refresh
    - Refresh scheduling
    - Health monitoring
    """

    VIEWS = [
        ('mv_daily_revenue', MaterializedViewDefinitions.MV_DAILY_REVENUE),
        ('mv_invoice_aging', MaterializedViewDefinitions.MV_INVOICE_AGING),
        ('mv_project_profitability', MaterializedViewDefinitions.MV_PROJECT_PROFITABILITY),
        ('mv_client_stats', MaterializedViewDefinitions.MV_CLIENT_STATS),
        ('mv_monthly_summary', MaterializedViewDefinitions.MV_MONTHLY_SUMMARY),
    ]

    REFRESH_INTERVALS = {
        'mv_daily_revenue': 15,
        'mv_invoice_aging': 30,
        'mv_project_profitability': 30,
        'mv_client_stats': 60,
        'mv_monthly_summary': 60,
    }

    async def create_all_views(self) -> dict:
        """Create all materialized views."""
        results = {}

        if not db_manager.is_available:
            return {"error": "Database not available"}

        try:
            from sqlalchemy import text
        except ImportError:
            return {"error": "SQLAlchemy not available"}

        async with db_manager.write_session() as session:
            for name, definition in self.VIEWS:
                try:
                    for statement in definition.split(';'):
                        if statement.strip():
                            await session.execute(text(statement))
                    await session.commit()
                    results[name] = {'status': 'created'}
                    logger.info(f"Created materialized view: {name}")
                except Exception as e:
                    results[name] = {'status': 'error', 'error': str(e)}
                    logger.error(f"Failed to create {name}: {e}")

        return results

    async def refresh_view(
        self,
        view_name: str,
        concurrently: bool = True
    ) -> dict:
        """
        Refresh a materialized view.

        Args:
            view_name: Name of the view to refresh
            concurrently: Use CONCURRENTLY (non-blocking)
        """
        start_time = datetime.utcnow()

        if not db_manager.is_available:
            return {"status": "error", "error": "Database not available"}

        try:
            from sqlalchemy import text
        except ImportError:
            return {"status": "error", "error": "SQLAlchemy not available"}

        try:
            async with db_manager.write_session() as session:
                concurrent_clause = "CONCURRENTLY" if concurrently else ""
                await session.execute(
                    text(f"REFRESH MATERIALIZED VIEW {concurrent_clause} {view_name}")
                )
                await session.commit()

            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Refreshed {view_name} in {duration:.2f}s")

            return {
                'status': 'success',
                'view': view_name,
                'duration_seconds': duration,
                'concurrent': concurrently
            }

        except Exception as e:
            logger.error(f"Failed to refresh {view_name}: {e}")
            return {
                'status': 'error',
                'view': view_name,
                'error': str(e)
            }

    async def refresh_all_views(self) -> dict:
        """Refresh all materialized views."""
        results = {}

        for name, _ in self.VIEWS:
            results[name] = await self.refresh_view(name)

        return results

    async def get_view_stats(self) -> dict:
        """Get statistics for all materialized views."""
        stats = {}

        if not db_manager.is_available:
            return {"error": "Database not available"}

        try:
            from sqlalchemy import text
        except ImportError:
            return {"error": "SQLAlchemy not available"}

        async with db_manager.read_session() as session:
            for name, _ in self.VIEWS:
                try:
                    result = await session.execute(text(f"""
                        SELECT
                            reltuples::bigint as row_count,
                            pg_total_relation_size('{name}') as size_bytes
                        FROM pg_class
                        WHERE relname = '{name}'
                    """))
                    row = result.fetchone()

                    if row:
                        stats[name] = {
                            'row_count': row[0],
                            'size_bytes': row[1],
                            'size_mb': round(row[1] / 1024 / 1024, 2),
                            'refresh_interval_minutes': self.REFRESH_INTERVALS.get(name)
                        }
                except Exception as e:
                    stats[name] = {'error': str(e)}

        return stats

    async def drop_view(self, view_name: str) -> bool:
        """Drop a materialized view."""
        if not db_manager.is_available:
            return False

        try:
            from sqlalchemy import text
        except ImportError:
            return False

        try:
            async with db_manager.write_session() as session:
                await session.execute(
                    text(f"DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE")
                )
                await session.commit()
            logger.info(f"Dropped materialized view: {view_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to drop {view_name}: {e}")
            return False


mv_manager = MaterializedViewManager()
