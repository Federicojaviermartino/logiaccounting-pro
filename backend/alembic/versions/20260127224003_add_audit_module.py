"""Add audit module tables

Revision ID: 20260127224003
Revises: 
Create Date: 2026-01-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '20260127224003'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Audit Action Enum
    op.execute("""
        CREATE TYPE audit_action AS ENUM (
            'create', 'read', 'update', 'delete', 'login', 'logout', 
            'login_failed', 'password_change', 'export', 'import',
            'approve', 'reject', 'submit', 'void', 'archive', 'restore', 'download'
        )
    """)
    
    # Audit Severity Enum
    op.execute("""
        CREATE TYPE audit_severity AS ENUM ('low', 'medium', 'high', 'critical')
    """)
    
    # Compliance Standard Enum
    op.execute("""
        CREATE TYPE compliance_standard AS ENUM ('sox', 'gdpr', 'hipaa', 'pci_dss', 'soc2', 'custom')
    """)
    
    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('user_email', sa.String(255)),
        sa.Column('user_name', sa.String(200)),
        sa.Column('user_role', sa.String(50)),
        sa.Column('action', sa.Enum('create', 'read', 'update', 'delete', 'login', 'logout',
            'login_failed', 'password_change', 'export', 'import', 'approve', 'reject',
            'submit', 'void', 'archive', 'restore', 'download', name='audit_action'), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='audit_severity')),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(100)),
        sa.Column('resource_name', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('old_values', JSONB),
        sa.Column('new_values', JSONB),
        sa.Column('changed_fields', JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('request_id', sa.String(100)),
        sa.Column('session_id', sa.String(100)),
        sa.Column('endpoint', sa.String(255)),
        sa.Column('http_method', sa.String(10)),
        sa.Column('metadata', JSONB),
        sa.Column('is_sensitive', sa.Boolean, default=False)
    )
    op.create_index('idx_audit_logs_customer', 'audit_logs', ['customer_id'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_severity', 'audit_logs', ['severity'])
    
    # Data Change Logs
    op.create_table(
        'data_change_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('audit_log_id', UUID(as_uuid=True), sa.ForeignKey('audit_logs.id'), nullable=False),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.String(100), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('field_type', sa.String(50)),
        sa.Column('old_value', sa.Text),
        sa.Column('new_value', sa.Text),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_data_change_audit', 'data_change_logs', ['audit_log_id'])
    op.create_index('idx_data_change_customer', 'data_change_logs', ['customer_id'])
    
    # Entity Snapshots
    op.create_table(
        'entity_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('audit_log_id', UUID(as_uuid=True), sa.ForeignKey('audit_logs.id')),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('snapshot_data', JSONB, nullable=False),
        sa.Column('reason', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'))
    )
    op.create_index('idx_entity_snapshots_customer', 'entity_snapshots', ['customer_id'])
    op.create_index('idx_entity_snapshots_entity', 'entity_snapshots', ['entity_type', 'entity_id'])
    
    # Retention Policies
    op.create_table(
        'retention_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('retention_days', sa.Integer, nullable=False),
        sa.Column('archive_after_days', sa.Integer),
        sa.Column('action_on_expiry', sa.String(20), default='archive'),
        sa.Column('compliance_standard', sa.Enum('sox', 'gdpr', 'hipaa', 'pci_dss', 'soc2', 'custom', name='compliance_standard')),
        sa.Column('regulation_reference', sa.String(200)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_retention_policies_customer', 'retention_policies', ['customer_id'])
    
    # Compliance Rules
    op.create_table(
        'compliance_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id')),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('compliance_standard', sa.Enum('sox', 'gdpr', 'hipaa', 'pci_dss', 'soc2', 'custom', name='compliance_standard', create_type=False), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('rule_type', sa.String(30), nullable=False),
        sa.Column('rule_config', JSONB),
        sa.Column('severity', sa.String(20), default='medium'),
        sa.Column('alert_on_violation', sa.Boolean, default=True),
        sa.Column('block_on_violation', sa.Boolean, default=False),
        sa.Column('notify_users', JSONB),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'code', name='uq_compliance_rule_code')
    )
    op.create_index('idx_compliance_rules_customer', 'compliance_rules', ['customer_id'])
    
    # Compliance Violations
    op.create_table(
        'compliance_violations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('rule_id', UUID(as_uuid=True), sa.ForeignKey('compliance_rules.id'), nullable=False),
        sa.Column('violation_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('details', JSONB),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', sa.String(100)),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('audit_log_id', UUID(as_uuid=True), sa.ForeignKey('audit_logs.id')),
        sa.Column('status', sa.String(20), default='open'),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('resolved_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('detected_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_compliance_violations_customer', 'compliance_violations', ['customer_id'])
    op.create_index('idx_compliance_violations_status', 'compliance_violations', ['status'])
    
    # Access Logs
    op.create_table(
        'access_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=False),
        sa.Column('resource_name', sa.String(255)),
        sa.Column('access_type', sa.String(20), nullable=False),
        sa.Column('data_classification', sa.String(30), default='internal'),
        sa.Column('contains_pii', sa.Boolean, default=False),
        sa.Column('contains_financial', sa.Boolean, default=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('access_reason', sa.String(500)),
        sa.Column('accessed_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_access_logs_customer', 'access_logs', ['customer_id'])
    op.create_index('idx_access_logs_user', 'access_logs', ['user_id'])
    op.create_index('idx_access_logs_accessed', 'access_logs', ['accessed_at'])


def downgrade():
    op.drop_table('access_logs')
    op.drop_table('compliance_violations')
    op.drop_table('compliance_rules')
    op.drop_table('retention_policies')
    op.drop_table('entity_snapshots')
    op.drop_table('data_change_logs')
    op.drop_table('audit_logs')
    
    op.execute("DROP TYPE IF EXISTS compliance_standard")
    op.execute("DROP TYPE IF EXISTS audit_severity")
    op.execute("DROP TYPE IF EXISTS audit_action")
