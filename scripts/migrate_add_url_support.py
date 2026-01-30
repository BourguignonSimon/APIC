#!/usr/bin/env python3
"""
Database Migration: Add URL Support to Documents Table

This script adds the source_type and source_url columns to the documents table
to support URL-based documents alongside file uploads.

Usage:
    python scripts/migrate_add_url_support.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import settings


def run_migration():
    """Run the database migration to add URL support."""

    print("🔄 Starting database migration: Add URL support to documents table")
    print(f"📊 Database URL: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials

    # Create database engine
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Start transaction
            with conn.begin():
                print("\n1️⃣ Adding source_type column...")
                conn.execute(text("""
                    ALTER TABLE documents
                    ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) DEFAULT 'file'
                """))
                print("   ✅ source_type column added")

                print("\n2️⃣ Adding source_url column...")
                conn.execute(text("""
                    ALTER TABLE documents
                    ADD COLUMN IF NOT EXISTS source_url VARCHAR(2000)
                """))
                print("   ✅ source_url column added")

                print("\n3️⃣ Making file_path nullable...")
                conn.execute(text("""
                    ALTER TABLE documents
                    ALTER COLUMN file_path DROP NOT NULL
                """))
                print("   ✅ file_path is now nullable")

                print("\n4️⃣ Setting default values for existing records...")
                conn.execute(text("""
                    UPDATE documents
                    SET source_type = 'file'
                    WHERE source_type IS NULL
                """))
                print("   ✅ Existing records updated with source_type='file'")

            # Verify the changes
            print("\n5️⃣ Verifying migration...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'documents'
                AND column_name IN ('source_type', 'source_url', 'file_path')
                ORDER BY column_name
            """))

            print("\n   Column Details:")
            for row in result:
                print(f"   - {row.column_name}: {row.data_type} (nullable: {row.is_nullable})")

        print("\n✅ Migration completed successfully!")
        print("\n🎉 You can now upload URLs as documents!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that PostgreSQL is running")
        print("2. Verify DATABASE_URL in .env file")
        print("3. Ensure you have database permissions")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE MIGRATION: Add URL Support")
    print("=" * 70)

    # Confirm before proceeding
    response = input("\n⚠️  This will modify the database schema. Continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        run_migration()
    else:
        print("\n❌ Migration cancelled")
        sys.exit(0)
