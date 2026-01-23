-- Migration: Add category column to documents table
-- Version: 001
-- Description: Adds category column to support document categorization
--              (e.g., 'general', 'interview_results', 'operational', etc.)

-- Add category column with default value
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'general';

-- Create index for category column
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);

-- Update existing documents to have 'general' category (if NULL)
UPDATE documents SET category = 'general' WHERE category IS NULL;
