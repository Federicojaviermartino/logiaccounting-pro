"""Add budgeting module

Revision ID: phase39_budgeting
Revises:
Create Date: 2025-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase39_budgeting'
down_revision = None  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Distribution Patterns table
    op.create_table(
        'distribution_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('jan_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('feb_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('mar_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('apr_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('may_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('jun_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('jul_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('aug_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('sep_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('oct_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('nov_percent', sa.Numeric(5, 2), default=8.33),
        sa.Column('dec_percent', sa.Numeric(5, 2), default=8.37),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'name', name='uq_distribution_pattern_name'),
    )
    op.create_index('idx_distribution_patterns_customer', 'distribution_patterns', ['customer_id'])

    # Budgets table
    op.create_table(
        'budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('budget_code', sa.String(30), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('budget_type', sa.Enum('annual', 'quarterly', 'monthly', 'project', 'departmental', name='budgettype'), default='annual'),
        sa.Column('fiscal_year', sa.Integer, nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True)),
        sa.Column('project_id', postgresql.UUID(as_uuid=True)),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True)),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('status', sa.Enum('draft', 'pending_approval', 'approved', 'active', 'closed', 'archived', name='budgetstatus'), default='draft'),
        sa.Column('active_version_id', postgresql.UUID(as_uuid=True)),
        sa.Column('requires_approval', sa.Boolean, default=True),
        sa.Column('allow_overspend', sa.Boolean, default=False),
        sa.Column('overspend_threshold_percent', sa.Numeric(5, 2), default=10),
        sa.Column('total_revenue', sa.Numeric(18, 4), default=0),
        sa.Column('total_expenses', sa.Numeric(18, 4), default=0),
        sa.Column('total_net_income', sa.Numeric(18, 4), default=0),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime),
        sa.UniqueConstraint('customer_id', 'budget_code', name='uq_budget_code'),
    )
    op.create_index('idx_budgets_customer', 'budgets', ['customer_id'])
    op.create_index('idx_budgets_fiscal_year', 'budgets', ['customer_id', 'fiscal_year'])
    op.create_index('idx_budgets_status', 'budgets', ['customer_id', 'status'])

    # Budget Versions table
    op.create_table(
        'budget_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('budget_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('budgets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('version_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('version_type', sa.String(30), default='original'),
        sa.Column('parent_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('budget_versions.id')),
        sa.Column('total_revenue', sa.Numeric(18, 4), default=0),
        sa.Column('total_expenses', sa.Numeric(18, 4), default=0),
        sa.Column('total_net_income', sa.Numeric(18, 4), default=0),
        sa.Column('status', sa.Enum('draft', 'submitted', 'approved', 'rejected', 'active', 'superseded', name='versionstatus'), default='draft'),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('is_locked', sa.Boolean, default=False),
        sa.Column('submitted_at', sa.DateTime),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('rejection_reason', sa.Text),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('budget_id', 'version_number', name='uq_budget_version_number'),
    )
    op.create_index('idx_budget_versions_budget', 'budget_versions', ['budget_id'])
    op.create_index('idx_budget_versions_active', 'budget_versions', ['budget_id', 'is_active'])

    # Budget Lines table
    op.create_table(
        'budget_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('budget_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chart_of_accounts.id'), nullable=False),
        sa.Column('account_code', sa.String(20), nullable=False),
        sa.Column('account_name', sa.String(200), nullable=False),
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('department_id', postgresql.UUID(as_uuid=True)),
        sa.Column('cost_center_id', postgresql.UUID(as_uuid=True)),
        sa.Column('project_id', postgresql.UUID(as_uuid=True)),
        sa.Column('annual_amount', sa.Numeric(18, 4), default=0),
        sa.Column('ytd_actual', sa.Numeric(18, 4), default=0),
        sa.Column('ytd_variance', sa.Numeric(18, 4), default=0),
        sa.Column('ytd_variance_percent', sa.Numeric(8, 4), default=0),
        sa.Column('distribution_method', sa.Enum('equal', 'seasonal', 'manual', 'historical', name='distributionmethod'), default='equal'),
        sa.Column('distribution_pattern_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('distribution_patterns.id')),
        sa.Column('notes', sa.Text),
        sa.Column('assumptions', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('version_id', 'account_id', 'department_id', 'cost_center_id', name='uq_budget_line_account'),
    )
    op.create_index('idx_budget_lines_version', 'budget_lines', ['version_id'])
    op.create_index('idx_budget_lines_account', 'budget_lines', ['account_id'])

    # Budget Periods table
    op.create_table(
        'budget_periods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('line_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('budget_lines.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_year', sa.Integer, nullable=False),
        sa.Column('period_month', sa.Integer, nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('budgeted_amount', sa.Numeric(18, 4), default=0),
        sa.Column('actual_amount', sa.Numeric(18, 4), default=0),
        sa.Column('committed_amount', sa.Numeric(18, 4), default=0),
        sa.Column('variance_amount', sa.Numeric(18, 4), default=0),
        sa.Column('variance_percent', sa.Numeric(8, 4), default=0),
        sa.Column('variance_type', sa.Enum('favorable', 'unfavorable', 'on_target', name='variancetype')),
        sa.Column('forecast_amount', sa.Numeric(18, 4)),
        sa.Column('is_locked', sa.Boolean, default=False),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('line_id', 'period_year', 'period_month', name='uq_budget_period'),
    )
    op.create_index('idx_budget_periods_line', 'budget_periods', ['line_id'])


def downgrade() -> None:
    op.drop_table('budget_periods')
    op.drop_table('budget_lines')
    op.drop_table('budget_versions')
    op.drop_table('budgets')
    op.drop_table('distribution_patterns')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS variancetype')
    op.execute('DROP TYPE IF EXISTS distributionmethod')
    op.execute('DROP TYPE IF EXISTS versionstatus')
    op.execute('DROP TYPE IF EXISTS budgetstatus')
    op.execute('DROP TYPE IF EXISTS budgettype')
