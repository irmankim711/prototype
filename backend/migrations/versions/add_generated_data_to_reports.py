"""Add generated_data column to reports table

Revision ID: add_generated_data_001
Revises:
Create Date: 2025-11-12

This migration adds the generated_data JSON column to the reports table
to store structured extracted data from Excel/Google Forms for preview functionality.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'add_generated_data_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add generated_data column to reports table"""
    # Add generated_data JSON column
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('generated_data', sa.JSON(), nullable=True))


def downgrade():
    """Remove generated_data column from reports table"""
    # Remove generated_data column
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_column('generated_data')
