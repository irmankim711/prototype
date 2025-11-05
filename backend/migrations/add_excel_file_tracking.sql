-- Migration: Add Excel File Tracking for Multi-File Support
-- Created: 2025-01-05
-- Purpose: Enable users to upload and select from multiple Excel files

-- Create parsed_excel_files table
CREATE TABLE IF NOT EXISTS parsed_excel_files (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    status VARCHAR(50) DEFAULT 'completed',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Parsing metadata
    tables_count INTEGER DEFAULT 0,
    total_rows INTEGER DEFAULT 0,
    total_columns INTEGER DEFAULT 0,
    sheets_processed INTEGER DEFAULT 0,

    -- Additional metadata (JSON)
    metadata TEXT,

    -- Error tracking
    error_message TEXT
);

-- Create indexes for parsed_excel_files
CREATE INDEX IF NOT EXISTS idx_parsed_excel_user_id ON parsed_excel_files(user_id);
CREATE INDEX IF NOT EXISTS idx_parsed_excel_uploaded_at ON parsed_excel_files(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_parsed_excel_status ON parsed_excel_files(status);

-- Create excel_tables table
CREATE TABLE IF NOT EXISTS excel_tables (
    id VARCHAR(64) PRIMARY KEY,
    parsed_file_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    sheet_name VARCHAR(255),
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,

    -- Table structure (JSON)
    headers TEXT,
    data_types TEXT,
    table_range VARCHAR(50),

    -- Optional: Store preview data (JSON)
    data TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key
    FOREIGN KEY (parsed_file_id) REFERENCES parsed_excel_files(id) ON DELETE CASCADE
);

-- Create indexes for excel_tables
CREATE INDEX IF NOT EXISTS idx_excel_tables_parsed_file ON excel_tables(parsed_file_id);
CREATE INDEX IF NOT EXISTS idx_excel_tables_created_at ON excel_tables(created_at);

-- Verification queries
-- SELECT COUNT(*) FROM parsed_excel_files;
-- SELECT COUNT(*) FROM excel_tables;
