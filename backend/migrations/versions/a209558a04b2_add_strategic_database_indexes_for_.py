"""Add strategic database indexes for performance optimization

Revision ID: a209558a04b2
Revises: 9550c5faf615
Create Date: 2025-09-12 03:57:30.243442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a209558a04b2'
down_revision = '9550c5faf615'
branch_labels = None
depends_on = None


def upgrade():
    # Add strategic indexes for forms table
    with op.batch_alter_table('forms', schema=None) as batch_op:
        batch_op.create_index('idx_forms_creator_id', ['creator_id'], unique=False)
        batch_op.create_index('idx_forms_is_active', ['is_active'], unique=False)
        batch_op.create_index('idx_forms_is_public', ['is_public'], unique=False)
        batch_op.create_index('idx_forms_created_at', ['created_at'], unique=False)
    
    # Add strategic indexes for form_submissions table
    with op.batch_alter_table('form_submissions', schema=None) as batch_op:
        batch_op.create_index('idx_form_submissions_form_id', ['form_id'], unique=False)
        batch_op.create_index('idx_form_submissions_submitted_at', ['submitted_at'], unique=False)
        batch_op.create_index('idx_form_submissions_status', ['status'], unique=False)
        batch_op.create_index('idx_form_submissions_submitter_id', ['submitter_id'], unique=False)
        # Composite index for common query combinations
        batch_op.create_index('idx_form_submissions_form_submitted', ['form_id', 'submitted_at'], unique=False)
    
    # Add strategic indexes for reports table
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.create_index('idx_reports_created_by', ['created_by'], unique=False)
        batch_op.create_index('idx_reports_generation_status', ['generation_status'], unique=False)
        batch_op.create_index('idx_reports_created_at', ['created_at'], unique=False)
        batch_op.create_index('idx_reports_template_id', ['template_id'], unique=False)
        # Composite index for common query combinations
        batch_op.create_index('idx_reports_user_status', ['created_by', 'generation_status'], unique=False)
    
    # Add strategic indexes for user table (if it exists)
    # Note: The table name might be 'user' instead of 'users' based on the database analysis
    try:
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.create_index('idx_user_email', ['email'], unique=False)
            batch_op.create_index('idx_user_role', ['role'], unique=False)
            batch_op.create_index('idx_user_is_active', ['is_active'], unique=False)
    except Exception:
        # If 'user' table doesn't exist, try 'users'
        try:
            with op.batch_alter_table('users', schema=None) as batch_op:
                batch_op.create_index('idx_users_email', ['email'], unique=False)
                batch_op.create_index('idx_users_role', ['role'], unique=False)
                batch_op.create_index('idx_users_is_active', ['is_active'], unique=False)
        except Exception:
            pass  # Skip if neither table exists


def downgrade():
    # Remove strategic indexes for reports table
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_index('idx_reports_user_status')
        batch_op.drop_index('idx_reports_template_id')
        batch_op.drop_index('idx_reports_created_at')
        batch_op.drop_index('idx_reports_generation_status')
        batch_op.drop_index('idx_reports_created_by')
    
    # Remove strategic indexes for form_submissions table
    with op.batch_alter_table('form_submissions', schema=None) as batch_op:
        batch_op.drop_index('idx_form_submissions_form_submitted')
        batch_op.drop_index('idx_form_submissions_submitter_id')
        batch_op.drop_index('idx_form_submissions_status')
        batch_op.drop_index('idx_form_submissions_submitted_at')
        batch_op.drop_index('idx_form_submissions_form_id')
    
    # Remove strategic indexes for forms table
    with op.batch_alter_table('forms', schema=None) as batch_op:
        batch_op.drop_index('idx_forms_created_at')
        batch_op.drop_index('idx_forms_is_public')
        batch_op.drop_index('idx_forms_is_active')
        batch_op.drop_index('idx_forms_creator_id')
    
    # Remove strategic indexes for user table
    try:
        with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.drop_index('idx_user_is_active')
            batch_op.drop_index('idx_user_role')
            batch_op.drop_index('idx_user_email')
    except Exception:
        try:
            with op.batch_alter_table('users', schema=None) as batch_op:
                batch_op.drop_index('idx_users_is_active')
                batch_op.drop_index('idx_users_role')
                batch_op.drop_index('idx_users_email')
        except Exception:
            pass
