#!/usr/bin/env python3
"""
Database Index Analysis Script
Analyzes current database structure and identifies missing indexes for performance optimization.
"""

from app import create_app, db
from app.models import *
import sqlalchemy as sa

def analyze_database_indexes():
    """Analyze current database indexes and identify missing ones."""
    app = create_app()
    with app.app_context():
        # Get all table names
        inspector = sa.inspect(db.engine)
        tables = inspector.get_table_names()
        print('Current tables:', tables)
        
        # Check indexes for key tables
        key_tables = ['users', 'forms', 'form_submissions', 'reports', 'form_data_sources', 'form_data_submissions']
        
        for table in key_tables:
            if table in tables:
                indexes = inspector.get_indexes(table)
                print(f'\n{table} indexes:')
                for idx in indexes:
                    print(f'  - {idx["name"]}: {idx["column_names"]} (unique: {idx["unique"]})')
                
                # Get columns for this table
                columns = inspector.get_columns(table)
                print(f'{table} columns:')
                for col in columns:
                    print(f'  - {col["name"]}: {col["type"]}')
        
        # Identify missing indexes based on common query patterns
        print('\n=== MISSING INDEXES ANALYSIS ===')
        
        missing_indexes = []
        
        # Users table - frequently queried by email
        if 'users' in tables:
            existing_user_indexes = [idx["column_names"] for idx in inspector.get_indexes('users')]
            if ['email'] not in existing_user_indexes:
                missing_indexes.append(('users', 'idx_users_email', ['email']))
            if ['role'] not in existing_user_indexes:
                missing_indexes.append(('users', 'idx_users_role', ['role']))
            if ['is_active'] not in existing_user_indexes:
                missing_indexes.append(('users', 'idx_users_active', ['is_active']))
        
        # Forms table - frequently queried by creator_id, is_active, is_public
        if 'forms' in tables:
            existing_form_indexes = [idx["column_names"] for idx in inspector.get_indexes('forms')]
            if ['creator_id'] not in existing_form_indexes:
                missing_indexes.append(('forms', 'idx_forms_creator_id', ['creator_id']))
            if ['is_active'] not in existing_form_indexes:
                missing_indexes.append(('forms', 'idx_forms_is_active', ['is_active']))
            if ['is_public'] not in existing_form_indexes:
                missing_indexes.append(('forms', 'idx_forms_is_public', ['is_public']))
            if ['created_at'] not in existing_form_indexes:
                missing_indexes.append(('forms', 'idx_forms_created_at', ['created_at']))
        
        # Form submissions - frequently queried by form_id, submitted_at, status
        if 'form_submissions' in tables:
            existing_submission_indexes = [idx["column_names"] for idx in inspector.get_indexes('form_submissions')]
            if ['form_id'] not in existing_submission_indexes:
                missing_indexes.append(('form_submissions', 'idx_form_submissions_form_id', ['form_id']))
            if ['submitted_at'] not in existing_submission_indexes:
                missing_indexes.append(('form_submissions', 'idx_form_submissions_submitted_at', ['submitted_at']))
            if ['status'] not in existing_submission_indexes:
                missing_indexes.append(('form_submissions', 'idx_form_submissions_status', ['status']))
            if ['submitter_id'] not in existing_submission_indexes:
                missing_indexes.append(('form_submissions', 'idx_form_submissions_submitter_id', ['submitter_id']))
            # Composite indexes for common query combinations
            if ['form_id', 'submitted_at'] not in existing_submission_indexes:
                missing_indexes.append(('form_submissions', 'idx_form_submissions_form_submitted', ['form_id', 'submitted_at']))
        
        # Reports table - frequently queried by user_id, status, created_at
        if 'reports' in tables:
            existing_report_indexes = [idx["column_names"] for idx in inspector.get_indexes('reports')]
            if ['created_by'] not in existing_report_indexes:
                missing_indexes.append(('reports', 'idx_reports_created_by', ['created_by']))
            if ['generation_status'] not in existing_report_indexes:
                missing_indexes.append(('reports', 'idx_reports_generation_status', ['generation_status']))
            if ['created_at'] not in existing_report_indexes:
                missing_indexes.append(('reports', 'idx_reports_created_at', ['created_at']))
            if ['template_id'] not in existing_report_indexes:
                missing_indexes.append(('reports', 'idx_reports_template_id', ['template_id']))
            # Composite indexes
            if ['created_by', 'generation_status'] not in existing_report_indexes:
                missing_indexes.append(('reports', 'idx_reports_user_status', ['created_by', 'generation_status']))
        
        # Form data sources - frequently queried by source_type, is_active
        if 'form_data_sources' in tables:
            existing_datasource_indexes = [idx["column_names"] for idx in inspector.get_indexes('form_data_sources')]
            if ['source_type'] not in existing_datasource_indexes:
                missing_indexes.append(('form_data_sources', 'idx_form_data_sources_type', ['source_type']))
            if ['is_active'] not in existing_datasource_indexes:
                missing_indexes.append(('form_data_sources', 'idx_form_data_sources_active', ['is_active']))
            if ['created_by'] not in existing_datasource_indexes:
                missing_indexes.append(('form_data_sources', 'idx_form_data_sources_created_by', ['created_by']))
        
        # Form data submissions - frequently queried by data_source_id, processing_status
        if 'form_data_submissions' in tables:
            existing_datasubmission_indexes = [idx["column_names"] for idx in inspector.get_indexes('form_data_submissions')]
            if ['data_source_id'] not in existing_datasubmission_indexes:
                missing_indexes.append(('form_data_submissions', 'idx_form_data_submissions_source', ['data_source_id']))
            if ['processing_status'] not in existing_datasubmission_indexes:
                missing_indexes.append(('form_data_submissions', 'idx_form_data_submissions_status', ['processing_status']))
            if ['submitted_at'] not in existing_datasubmission_indexes:
                missing_indexes.append(('form_data_submissions', 'idx_form_data_submissions_submitted_at', ['submitted_at']))
        
        print('\nMissing indexes to create:')
        for table, index_name, columns in missing_indexes:
            print(f'  - {table}.{index_name}: {columns}')
        
        return missing_indexes

if __name__ == '__main__':
    analyze_database_indexes()