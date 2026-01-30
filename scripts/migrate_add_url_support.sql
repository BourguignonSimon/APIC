-- Migration: Add URL support to documents table
-- This adds source_type and source_url columns to support URL-based documents

-- Add source_type column (default to "file" for existing records)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) DEFAULT 'file';

-- Add source_url column (nullable for file-based documents)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS source_url VARCHAR(2000);

-- Update file_path to be nullable (URLs don't have file paths)
ALTER TABLE documents
ALTER COLUMN file_path DROP NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN documents.source_type IS 'Type of document source: "file" or "url"';
COMMENT ON COLUMN documents.source_url IS 'Source URL if source_type is "url"';

-- Display result
SELECT 'Migration completed: URL support added to documents table' AS status;
