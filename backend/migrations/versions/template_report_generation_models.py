"""Add template-based report generation models

Revision ID: template_report_gen_001
Revises: a209558a04b2
Create Date: 2025-01-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'template_report_gen_001'
down_revision = 'a209558a04b2'
branch_labels = None
depends_on = None

def upgrade():
    # Create templates table
    op.create_table('templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('preview_image', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('supports_excel', sa.Boolean(), nullable=True),
        sa.Column('required_fields', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create data_mappings table
    op.create_table('data_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('excel_file_path', sa.String(length=500), nullable=True),
        sa.Column('sheet_name', sa.String(length=100), nullable=True),
        sa.Column('field_mappings', sa.JSON(), nullable=True),
        sa.Column('transformations', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True),
        sa.Column('validation_errors', sa.JSON(), nullable=True),
        sa.Column('last_validated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create generated_reports table
    op.create_table('generated_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('excel_file_path', sa.String(length=500), nullable=True),
        sa.Column('data_mapping_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'GENERATING', 'COMPLETED', 'FAILED', 'EDITING', name='reportstatus'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('generation_task_id', sa.String(length=255), nullable=True),
        sa.Column('generation_started_at', sa.DateTime(), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(), nullable=True),
        sa.Column('generation_duration', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('docx_path', sa.String(length=500), nullable=True),
        sa.Column('html_path', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['data_mapping_id'], ['data_mappings.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create excel_uploads table
    op.create_table('excel_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('sheet_names', sa.JSON(), nullable=True),
        sa.Column('column_headers', sa.JSON(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('processing_errors', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create report_versions table
    op.create_table('report_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('changes_summary', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['report_id'], ['generated_reports.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_templates_category', 'templates', ['category'])
    op.create_index('idx_templates_active', 'templates', ['is_active'])
    op.create_index('idx_generated_reports_status', 'generated_reports', ['status'])
    op.create_index('idx_generated_reports_template', 'generated_reports', ['template_id'])
    op.create_index('idx_data_mappings_template', 'data_mappings', ['template_id'])
    op.create_index('idx_report_versions_report', 'report_versions', ['report_id'])
    op.create_index('idx_report_versions_current', 'report_versions', ['is_current'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_report_versions_current', table_name='report_versions')
    op.drop_index('idx_report_versions_report', table_name='report_versions')
    op.drop_index('idx_data_mappings_template', table_name='data_mappings')
    op.drop_index('idx_generated_reports_template', table_name='generated_reports')
    op.drop_index('idx_generated_reports_status', table_name='generated_reports')
    op.drop_index('idx_templates_active', table_name='templates')
    op.drop_index('idx_templates_category', table_name='templates')
    
    # Drop tables
    op.drop_table('report_versions')
    op.drop_table('excel_uploads')
    op.drop_table('generated_reports')
    op.drop_table('data_mappings')
    op.drop_table('templates')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS reportstatus')