"""Google Forms to Sheets Integration Models

Revision ID: google_forms_sheets_integration
Revises: a209558a04b2
Create Date: 2025-01-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'google_forms_sheets_integration'
down_revision = 'a209558a04b2'
branch_labels = None
depends_on = None


def upgrade():
    """Create integration management tables"""
    
    # Create integration_configs table
    op.create_table('integration_configs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('google_form_id', sa.String(255), nullable=False),
        sa.Column('google_form_title', sa.String(255), nullable=True),
        sa.Column('google_sheet_id', sa.String(255), nullable=True),
        sa.Column('google_sheet_title', sa.String(255), nullable=True),
        sa.Column('sheet_tab_name', sa.String(255), nullable=True),
        sa.Column('export_mode', sa.Enum('create_new', 'update_existing', 'append_only', name='export_mode_enum'), nullable=True),
        sa.Column('include_timestamps', sa.Boolean(), nullable=True),
        sa.Column('include_response_id', sa.Boolean(), nullable=True),
        sa.Column('transformation_rules', sa.JSON(), nullable=True),
        sa.Column('formatting_rules', sa.JSON(), nullable=True),
        sa.Column('custom_headers', sa.JSON(), nullable=True),
        sa.Column('schedule_enabled', sa.Boolean(), nullable=True),
        sa.Column('schedule_frequency', sa.Enum('hourly', 'daily', 'weekly', name='schedule_frequency_enum'), nullable=True),
        sa.Column('schedule_time', sa.Time(), nullable=True),
        sa.Column('last_export_at', sa.DateTime(), nullable=True),
        sa.Column('next_export_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'error', name='integration_status_enum'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create export_history table
    op.create_table('export_history',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('integration_id', sa.String(36), nullable=False),
        sa.Column('export_type', sa.Enum('manual', 'scheduled', name='export_type_enum'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', name='export_status_enum'), nullable=True),
        sa.Column('records_processed', sa.Integer(), nullable=True),
        sa.Column('records_exported', sa.Integer(), nullable=True),
        sa.Column('records_skipped', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('result_sheet_url', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integration_configs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create oauth_tokens table
    op.create_table('oauth_tokens',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(50), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('scopes', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_integration_configs_user_id', 'integration_configs', ['user_id'])
    op.create_index('idx_integration_configs_status', 'integration_configs', ['status'])
    op.create_index('idx_integration_configs_schedule_enabled', 'integration_configs', ['schedule_enabled'])
    op.create_index('idx_export_history_integration_id', 'export_history', ['integration_id'])
    op.create_index('idx_export_history_status', 'export_history', ['status'])
    op.create_index('idx_export_history_created_at', 'export_history', ['created_at'])
    op.create_index('idx_oauth_tokens_user_id', 'oauth_tokens', ['user_id'])
    op.create_index('idx_oauth_tokens_provider', 'oauth_tokens', ['provider'])
    op.create_index('idx_oauth_tokens_is_active', 'oauth_tokens', ['is_active'])


def downgrade():
    """Drop integration management tables"""
    
    # Drop indexes
    op.drop_index('idx_oauth_tokens_is_active', table_name='oauth_tokens')
    op.drop_index('idx_oauth_tokens_provider', table_name='oauth_tokens')
    op.drop_index('idx_oauth_tokens_user_id', table_name='oauth_tokens')
    op.drop_index('idx_export_history_created_at', table_name='export_history')
    op.drop_index('idx_export_history_status', table_name='export_history')
    op.drop_index('idx_export_history_integration_id', table_name='export_history')
    op.drop_index('idx_integration_configs_schedule_enabled', table_name='integration_configs')
    op.drop_index('idx_integration_configs_status', table_name='integration_configs')
    op.drop_index('idx_integration_configs_user_id', table_name='integration_configs')
    
    # Drop tables
    op.drop_table('oauth_tokens')
    op.drop_table('export_history')
    op.drop_table('integration_configs')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS export_status_enum')
    op.execute('DROP TYPE IF EXISTS export_type_enum')
    op.execute('DROP TYPE IF EXISTS integration_status_enum')
    op.execute('DROP TYPE IF EXISTS schedule_frequency_enum')
    op.execute('DROP TYPE IF EXISTS export_mode_enum')