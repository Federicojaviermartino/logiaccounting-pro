"""Add reporting module tables

Revision ID: 20260127162106
Revises: 
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '20260127162106'
down_revision = None  # Update with previous migration
branch_labels = None
depends_on = None


def upgrade():
    # Report Type Enum
    op.execute("""
        CREATE TYPE report_type AS ENUM (
            'balance_sheet', 'income_statement', 'cash_flow', 'trial_balance',
            'ar_aging', 'ap_aging', 'budget_vs_actual', 'payroll_summary',
            'general_ledger', 'custom'
        )
    """)
    
    # Report Category Enum
    op.execute("""
        CREATE TYPE report_category AS ENUM (
            'financial', 'operational', 'payroll', 'tax', 'management', 'custom'
        )
    """)
    
    # Report Format Enum
    op.execute("""
        CREATE TYPE report_format AS ENUM ('pdf', 'excel', 'csv', 'json', 'html')
    """)
    
    # Statement Type Enum
    op.execute("""
        CREATE TYPE statement_type AS ENUM ('balance_sheet', 'income_statement', 'cash_flow')
    """)
    
    # Line Item Type Enum
    op.execute("""
        CREATE TYPE line_item_type AS ENUM ('header', 'account', 'subtotal', 'total', 'blank', 'calculated')
    """)
    
    # KPI Category Enum
    op.execute("""
        CREATE TYPE kpi_category AS ENUM (
            'liquidity', 'profitability', 'efficiency', 'leverage', 'growth', 'operational'
        )
    """)
    
    # Report Definitions
    op.create_table(
        'report_definitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('report_type', sa.Enum('balance_sheet', 'income_statement', 'cash_flow', 'trial_balance',
            'ar_aging', 'ap_aging', 'budget_vs_actual', 'payroll_summary', 'general_ledger', 'custom',
            name='report_type'), nullable=False),
        sa.Column('category', sa.Enum('financial', 'operational', 'payroll', 'tax', 'management', 'custom',
            name='report_category'), default='financial'),
        sa.Column('config', JSONB, nullable=True),
        sa.Column('layout', JSONB, nullable=True),
        sa.Column('default_params', JSONB, nullable=True),
        sa.Column('available_formats', JSONB, nullable=True),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('is_public', sa.Boolean, default=True),
        sa.Column('allowed_roles', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'code', name='uq_report_definition_code')
    )
    op.create_index('idx_report_definitions_customer', 'report_definitions', ['customer_id'])
    op.create_index('idx_report_definitions_type', 'report_definitions', ['report_type'])
    
    # Report Schedules
    op.create_table(
        'report_schedules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', UUID(as_uuid=True), sa.ForeignKey('report_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('day_of_week', sa.Integer, nullable=True),
        sa.Column('day_of_month', sa.Integer, nullable=True),
        sa.Column('time_of_day', sa.String(5), default='06:00'),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('params', JSONB, nullable=True),
        sa.Column('output_format', sa.Enum('pdf', 'excel', 'csv', 'json', 'html', name='report_format'), default='pdf'),
        sa.Column('email_recipients', JSONB, nullable=True),
        sa.Column('save_to_storage', sa.Boolean, default=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_run_at', sa.DateTime, nullable=True),
        sa.Column('next_run_at', sa.DateTime, nullable=True),
        sa.Column('last_error', sa.Text, nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_report_schedules_customer', 'report_schedules', ['customer_id'])
    
    # Generated Reports
    op.create_table(
        'generated_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('report_id', UUID(as_uuid=True), sa.ForeignKey('report_definitions.id'), nullable=False),
        sa.Column('schedule_id', UUID(as_uuid=True), sa.ForeignKey('report_schedules.id'), nullable=True),
        sa.Column('report_name', sa.String(200), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('params', JSONB, nullable=True),
        sa.Column('output_format', sa.String(10), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('generation_time_ms', sa.Integer, nullable=True),
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), default='completed'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('generated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('generated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True)
    )
    op.create_index('idx_generated_reports_customer', 'generated_reports', ['customer_id'])
    
    # Financial Statement Templates
    op.create_table(
        'financial_statement_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('statement_type', sa.Enum('balance_sheet', 'income_statement', 'cash_flow', name='statement_type'), nullable=False),
        sa.Column('show_zero_balances', sa.Boolean, default=False),
        sa.Column('show_account_numbers', sa.Boolean, default=True),
        sa.Column('comparative_periods', sa.Integer, default=1),
        sa.Column('accounting_standard', sa.String(20), default='GAAP'),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'code', name='uq_statement_template_code')
    )
    op.create_index('idx_statement_templates_customer', 'financial_statement_templates', ['customer_id'])
    
    # Statement Line Items
    op.create_table(
        'statement_line_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('financial_statement_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('line_type', sa.Enum('header', 'account', 'subtotal', 'total', 'blank', 'calculated', name='line_item_type'), default='account'),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('statement_line_items.id'), nullable=True),
        sa.Column('indent_level', sa.Integer, default=0),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('account_codes', JSONB, nullable=True),
        sa.Column('account_types', JSONB, nullable=True),
        sa.Column('account_range_start', sa.String(20), nullable=True),
        sa.Column('account_range_end', sa.String(20), nullable=True),
        sa.Column('calculation_formula', sa.Text, nullable=True),
        sa.Column('sum_children', sa.Boolean, default=False),
        sa.Column('bold', sa.Boolean, default=False),
        sa.Column('underline', sa.Boolean, default=False),
        sa.Column('double_underline', sa.Boolean, default=False),
        sa.Column('reverse_sign', sa.Boolean, default=False),
        sa.Column('hide_if_zero', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.UniqueConstraint('template_id', 'code', name='uq_statement_line_code')
    )
    op.create_index('idx_statement_line_items_template', 'statement_line_items', ['template_id'])
    
    # KPI Definitions
    op.create_table(
        'kpi_definitions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.Enum('liquidity', 'profitability', 'efficiency', 'leverage', 'growth', 'operational', name='kpi_category'), nullable=False),
        sa.Column('formula', sa.Text, nullable=False),
        sa.Column('formula_type', sa.String(20), default='sql'),
        sa.Column('format_type', sa.String(20), default='number'),
        sa.Column('decimal_places', sa.Integer, default=2),
        sa.Column('prefix', sa.String(10), nullable=True),
        sa.Column('suffix', sa.String(10), nullable=True),
        sa.Column('warning_threshold', sa.Numeric(18, 4), nullable=True),
        sa.Column('critical_threshold', sa.Numeric(18, 4), nullable=True),
        sa.Column('threshold_direction', sa.String(10), default='above'),
        sa.Column('target_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'code', name='uq_kpi_definition_code')
    )
    op.create_index('idx_kpi_definitions_customer', 'kpi_definitions', ['customer_id'])
    
    # KPI Snapshots
    op.create_table(
        'kpi_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('kpi_id', UUID(as_uuid=True), sa.ForeignKey('kpi_definitions.id'), nullable=False),
        sa.Column('period_year', sa.Integer, nullable=False),
        sa.Column('period_month', sa.Integer, nullable=False),
        sa.Column('value', sa.Numeric(18, 4), nullable=False),
        sa.Column('previous_value', sa.Numeric(18, 4), nullable=True),
        sa.Column('change_percent', sa.Numeric(8, 4), nullable=True),
        sa.Column('components', JSONB, nullable=True),
        sa.Column('calculated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'kpi_id', 'period_year', 'period_month', name='uq_kpi_snapshot')
    )
    op.create_index('idx_kpi_snapshots_customer', 'kpi_snapshots', ['customer_id'])
    op.create_index('idx_kpi_snapshots_period', 'kpi_snapshots', ['period_year', 'period_month'])


def downgrade():
    op.drop_table('kpi_snapshots')
    op.drop_table('kpi_definitions')
    op.drop_table('statement_line_items')
    op.drop_table('financial_statement_templates')
    op.drop_table('generated_reports')
    op.drop_table('report_schedules')
    op.drop_table('report_definitions')
    
    op.execute("DROP TYPE IF EXISTS kpi_category")
    op.execute("DROP TYPE IF EXISTS line_item_type")
    op.execute("DROP TYPE IF EXISTS statement_type")
    op.execute("DROP TYPE IF EXISTS report_format")
    op.execute("DROP TYPE IF EXISTS report_category")
    op.execute("DROP TYPE IF EXISTS report_type")
