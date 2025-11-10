-- Migration: Create export_files table for tracking file ownership and preventing unauthorized access
-- Created: 2025-11-10
-- Purpose: Fix critical data leakage vulnerability by implementing file ownership tracking

CREATE TABLE IF NOT EXISTS export_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(128) NOT NULL,  -- Firebase UID
    file_type VARCHAR(50) NOT NULL,  -- 'google_forms_export', 'form_export', 'report_export'
    file_format VARCHAR(10) NOT NULL,  -- 'xlsx', 'csv', 'pdf', 'docx'
    file_size INTEGER,  -- Size in bytes
    file_path VARCHAR(512) NOT NULL,  -- Full file path

    -- Metadata
    related_id VARCHAR(128),  -- ID of related resource (form_id, report_id, etc.)
    related_type VARCHAR(50),  -- 'google_form', 'form', 'report'

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Optional expiration time
    last_downloaded_at TIMESTAMP,
    download_count INTEGER DEFAULT 0,

    -- Status
    is_deleted BOOLEAN DEFAULT FALSE,

    -- Indexes for performance
    CONSTRAINT idx_export_files_filename UNIQUE (filename),
    CONSTRAINT idx_export_files_user_id_created INDEX (user_id, created_at DESC),
    CONSTRAINT idx_export_files_created_at INDEX (created_at DESC)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_export_files_user_id ON export_files(user_id);
CREATE INDEX IF NOT EXISTS idx_export_files_filename ON export_files(filename);
CREATE INDEX IF NOT EXISTS idx_export_files_created_at ON export_files(created_at);
CREATE INDEX IF NOT EXISTS idx_export_files_expires_at ON export_files(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_export_files_user_created ON export_files(user_id, created_at DESC);

-- Add comment
COMMENT ON TABLE export_files IS 'Tracks exported files and their owners to prevent unauthorized access';
COMMENT ON COLUMN export_files.user_id IS 'Firebase UID of the file owner';
COMMENT ON COLUMN export_files.expires_at IS 'When the file access should expire (optional)';
COMMENT ON COLUMN export_files.download_count IS 'Number of times file has been downloaded';
COMMENT ON COLUMN export_files.is_deleted IS 'Soft delete flag - files marked as deleted cannot be accessed';
