"""
Table partitioning strategies for large tables.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.utils.datetime_utils import utc_now

try:
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

from app.performance.database.connection_pool import db_manager

logger = logging.getLogger(__name__)


class PartitionStrategy:
    """Base class for partition strategies."""
    pass


class RangePartition(PartitionStrategy):
    """Range-based partitioning (typically by date)."""

    def __init__(
        self,
        table_name: str,
        partition_column: str,
        interval: str = 'month'
    ):
        self.table_name = table_name
        self.partition_column = partition_column
        self.interval = interval


class PartitionManager:
    """
    Manager for table partitioning.

    Supported strategies:
    - Range partitioning by date (monthly/yearly)
    - List partitioning by tenant
    - Hash partitioning for even distribution
    """

    async def create_partitioned_table(
        self,
        table_name: str,
        columns_definition: str,
        partition_by: str,
        partition_column: str
    ) -> bool:
        """
        Create a partitioned table.

        Args:
            table_name: Name of the table
            columns_definition: SQL column definitions
            partition_by: Partition type (RANGE, LIST, HASH)
            partition_column: Column to partition by
        """
        if not db_manager.is_available:
            return False

        try:
            from sqlalchemy import text
        except ImportError:
            return False

        try:
            async with db_manager.write_session() as session:
                await session.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {columns_definition}
                    ) PARTITION BY {partition_by} ({partition_column})
                """))
                await session.commit()

            logger.info(f"Created partitioned table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create partitioned table {table_name}: {e}")
            return False

    async def create_monthly_partitions(
        self,
        table_name: str,
        start_date: datetime,
        months_ahead: int = 3,
        months_behind: int = 12
    ) -> List[str]:
        """
        Create monthly partitions for a date-partitioned table.

        Args:
            table_name: Base table name
            start_date: Starting date for partitions
            months_ahead: Number of future months to create
            months_behind: Number of past months to create
        """
        if not DATEUTIL_AVAILABLE:
            logger.warning("dateutil not available for partition creation")
            return []

        if not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        created_partitions = []

        start = start_date - relativedelta(months=months_behind)
        end = start_date + relativedelta(months=months_ahead)

        current = start.replace(day=1)

        async with db_manager.write_session() as session:
            while current <= end:
                partition_name = f"{table_name}_{current.strftime('%Y_%m')}"
                partition_start = current
                partition_end = current + relativedelta(months=1)

                try:
                    await session.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {table_name}
                        FOR VALUES FROM ('{partition_start.strftime('%Y-%m-%d')}')
                        TO ('{partition_end.strftime('%Y-%m-%d')}')
                    """))
                    created_partitions.append(partition_name)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.error(f"Failed to create partition {partition_name}: {e}")

                current = partition_end

            await session.commit()

        logger.info(f"Created {len(created_partitions)} partitions for {table_name}")
        return created_partitions

    async def create_tenant_partitions(
        self,
        table_name: str,
        tenant_ids: List[str]
    ) -> List[str]:
        """
        Create list partitions by tenant.

        Args:
            table_name: Base table name
            tenant_ids: List of tenant IDs to create partitions for
        """
        if not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        created_partitions = []

        async with db_manager.write_session() as session:
            for tenant_id in tenant_ids:
                partition_name = f"{table_name}_tenant_{tenant_id[:8]}"

                try:
                    await session.execute(text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {table_name}
                        FOR VALUES IN ('{tenant_id}')
                    """))
                    created_partitions.append(partition_name)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.error(f"Failed to create partition {partition_name}: {e}")

            await session.commit()

        return created_partitions

    async def drop_old_partitions(
        self,
        table_name: str,
        retention_months: int = 24
    ) -> List[str]:
        """
        Drop partitions older than retention period.

        Args:
            table_name: Base table name
            retention_months: Number of months to retain
        """
        if not DATEUTIL_AVAILABLE or not db_manager.is_available:
            return []

        try:
            from sqlalchemy import text
        except ImportError:
            return []

        dropped_partitions = []
        cutoff_date = utc_now() - relativedelta(months=retention_months)

        async with db_manager.write_session() as session:
            result = await session.execute(text(f"""
                SELECT child.relname as partition_name
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname = '{table_name}'
            """))

            partitions = result.fetchall()

            for (partition_name,) in partitions:
                try:
                    parts = partition_name.split('_')
                    if len(parts) >= 2:
                        date_str = parts[-2] + '_' + parts[-1]
                        partition_date = datetime.strptime(date_str, '%Y_%m')

                        if partition_date < cutoff_date:
                            await session.execute(
                                text(f"DROP TABLE IF EXISTS {partition_name}")
                            )
                            dropped_partitions.append(partition_name)
                            logger.info(f"Dropped old partition: {partition_name}")
                except (ValueError, IndexError):
                    continue

            await session.commit()

        return dropped_partitions

    async def get_partition_stats(self, table_name: str) -> dict:
        """Get statistics for table partitions."""
        if not db_manager.is_available:
            return {"error": "Database not available"}

        try:
            from sqlalchemy import text
        except ImportError:
            return {"error": "SQLAlchemy not available"}

        async with db_manager.read_session() as session:
            result = await session.execute(text(f"""
                SELECT
                    child.relname as partition_name,
                    pg_total_relation_size(child.oid) as size_bytes,
                    child.reltuples::bigint as row_count
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname = '{table_name}'
                ORDER BY child.relname
            """))

            partitions = []
            total_size = 0
            total_rows = 0

            for row in result.fetchall():
                partition = {
                    'name': row[0],
                    'size_bytes': row[1],
                    'size_mb': round(row[1] / 1024 / 1024, 2),
                    'row_count': row[2]
                }
                partitions.append(partition)
                total_size += row[1]
                total_rows += row[2]

            return {
                'table': table_name,
                'partition_count': len(partitions),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'total_rows': total_rows,
                'partitions': partitions
            }


partition_manager = PartitionManager()


PARTITION_MIGRATION_SQL = """
-- Transactions table partitioning by date
-- Step 1: Create new partitioned table
CREATE TABLE transactions_partitioned (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    invoice_id UUID,
    project_id UUID,
    client_id UUID,
    created_by UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Step 2: Create partitions for current and future months
-- (Run partition_manager.create_monthly_partitions())

-- Step 3: Copy data from old table
INSERT INTO transactions_partitioned
SELECT * FROM transactions;

-- Step 4: Rename tables
ALTER TABLE transactions RENAME TO transactions_old;
ALTER TABLE transactions_partitioned RENAME TO transactions;

-- Step 5: Recreate indexes on partitions
CREATE INDEX idx_transactions_tenant_date ON transactions (tenant_id, created_at DESC);
CREATE INDEX idx_transactions_project ON transactions (project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_transactions_invoice ON transactions (invoice_id) WHERE invoice_id IS NOT NULL;

-- Step 6: Verify and drop old table
-- DROP TABLE transactions_old;


-- Audit logs partitioning
CREATE TABLE audit_logs_partitioned (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
"""
