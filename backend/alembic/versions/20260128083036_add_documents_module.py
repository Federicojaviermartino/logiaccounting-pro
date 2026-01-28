"""Add documents module tables

Revision ID: 20260128083036
Revises: 
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '20260128083036'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Document Type Enum
    op.execute("""
        CREATE TYPE document_type AS ENUM (
            'invoice', 'receipt', 'contract', 'purchase_order', 'delivery_note',
            'quote', 'report', 'statement', 'tax_document', 'legal', 'correspondence', 'other'
        )
    """)
    
    # Document Status Enum
    op.execute("""
        CREATE TYPE document_status AS ENUM (
            'draft', 'pending', 'approved', 'rejected', 'archived', 'deleted'
        )
    """)
    
    # Share Permission Enum
    op.execute("""
        CREATE TYPE share_permission AS ENUM ('view', 'download', 'edit', 'full')
    """)
    
    # Document Categories
    op.create_table(
        'document_categories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('color', sa.String(7)),
        sa.Column('icon', sa.String(50)),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('document_categories.id')),
        sa.Column('path', sa.String(500)),
        sa.Column('default_retention_days', sa.Integer),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'name', 'parent_id', name='uq_category_name')
    )
    op.create_index('idx_doc_categories_customer', 'document_categories', ['customer_id'])
    
    # Documents
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('document_number', sa.String(100)),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('document_type', sa.Enum('invoice', 'receipt', 'contract', 'purchase_order', 
            'delivery_note', 'quote', 'report', 'statement', 'tax_document', 'legal', 
            'correspondence', 'other', name='document_type'), nullable=False),
        sa.Column('status', sa.Enum('draft', 'pending', 'approved', 'rejected', 'archived', 
            'deleted', name='document_status'), default='draft'),
        sa.Column('category_id', UUID(as_uuid=True), sa.ForeignKey('document_categories.id')),
        sa.Column('tags', JSONB),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_hash', sa.String(64)),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('is_latest', sa.Boolean, default=True),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('documents.id')),
        sa.Column('related_entity_type', sa.String(100)),
        sa.Column('related_entity_id', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB),
        sa.Column('extracted_text', sa.Text),
        sa.Column('document_date', sa.DateTime),
        sa.Column('expiry_date', sa.DateTime),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('is_confidential', sa.Boolean, default=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'document_number', name='uq_document_number')
    )
    op.create_index('idx_documents_customer', 'documents', ['customer_id'])
    op.create_index('idx_documents_type', 'documents', ['document_type'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_documents_category', 'documents', ['category_id'])
    
    # Document Versions
    op.create_table(
        'document_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=False),
        sa.Column('file_hash', sa.String(64)),
        sa.Column('change_summary', sa.Text),
        sa.Column('changes', JSONB),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('document_id', 'version', name='uq_document_version')
    )
    op.create_index('idx_doc_versions_document', 'document_versions', ['document_id'])
    
    # Folders
    op.create_table(
        'folders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('folders.id')),
        sa.Column('path', sa.String(1000), nullable=False),
        sa.Column('depth', sa.Integer, default=0),
        sa.Column('color', sa.String(7)),
        sa.Column('icon', sa.String(50)),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('is_system', sa.Boolean, default=False),
        sa.Column('document_count', sa.Integer, default=0),
        sa.Column('total_size', sa.BigInteger, default=0),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'path', name='uq_folder_path')
    )
    op.create_index('idx_folders_customer', 'folders', ['customer_id'])
    op.create_index('idx_folders_parent', 'folders', ['parent_id'])
    
    # Document Folders (Many-to-Many)
    op.create_table(
        'document_folders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('folder_id', UUID(as_uuid=True), sa.ForeignKey('folders.id'), nullable=False),
        sa.Column('added_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('added_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('document_id', 'folder_id', name='uq_document_folder')
    )
    op.create_index('idx_doc_folders_document', 'document_folders', ['document_id'])
    op.create_index('idx_doc_folders_folder', 'document_folders', ['folder_id'])
    
    # Document Shares
    op.create_table(
        'document_shares',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('shared_with_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('shared_with_email', sa.String(255)),
        sa.Column('permission', sa.Enum('view', 'download', 'edit', 'full', name='share_permission'), default='view'),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('access_count', sa.Integer, default=0),
        sa.Column('last_accessed_at', sa.DateTime),
        sa.Column('requires_password', sa.Boolean, default=False),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('allow_download', sa.Boolean, default=True),
        sa.Column('shared_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('message', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_doc_shares_document', 'document_shares', ['document_id'])
    
    # Document Share Links
    op.create_table(
        'document_share_links',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('token', sa.String(100), unique=True, nullable=False),
        sa.Column('permission', sa.Enum('view', 'download', 'edit', 'full', name='share_permission', create_type=False), default='view'),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('max_uses', sa.Integer),
        sa.Column('use_count', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('requires_password', sa.Boolean, default=False),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_share_links_document', 'document_share_links', ['document_id'])
    op.create_index('idx_share_links_token', 'document_share_links', ['token'])
    
    # Document Access Logs
    op.create_table(
        'document_access_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('share_link_id', UUID(as_uuid=True), sa.ForeignKey('document_share_links.id')),
        sa.Column('access_type', sa.String(20), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('accessed_at', sa.DateTime, server_default=sa.func.now())
    )
    op.create_index('idx_doc_access_document', 'document_access_logs', ['document_id'])
    op.create_index('idx_doc_access_date', 'document_access_logs', ['accessed_at'])


def downgrade():
    op.drop_table('document_access_logs')
    op.drop_table('document_share_links')
    op.drop_table('document_shares')
    op.drop_table('document_folders')
    op.drop_table('folders')
    op.drop_table('document_versions')
    op.drop_table('documents')
    op.drop_table('document_categories')
    
    op.execute("DROP TYPE IF EXISTS share_permission")
    op.execute("DROP TYPE IF EXISTS document_status")
    op.execute("DROP TYPE IF EXISTS document_type")
