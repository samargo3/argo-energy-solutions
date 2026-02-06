#!/usr/bin/env python3
"""
Run database migration to convert TIMESTAMP to TIMESTAMPTZ
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# SQL migration commands
MIGRATION_SQL = """
-- Convert readings table (most important - 151K+ rows)
ALTER TABLE readings 
ALTER COLUMN timestamp TYPE TIMESTAMPTZ 
USING timestamp AT TIME ZONE 'America/New_York';

ALTER TABLE readings 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

-- Convert channels table
ALTER TABLE channels 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

ALTER TABLE channels 
ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
USING updated_at AT TIME ZONE 'America/New_York';

-- Convert devices table
ALTER TABLE devices 
ALTER COLUMN last_seen TYPE TIMESTAMPTZ 
USING last_seen AT TIME ZONE 'America/New_York';

ALTER TABLE devices 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

ALTER TABLE devices 
ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
USING updated_at AT TIME ZONE 'America/New_York';

-- Convert organizations table
ALTER TABLE organizations 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';

ALTER TABLE organizations 
ALTER COLUMN updated_at TYPE TIMESTAMPTZ 
USING updated_at AT TIME ZONE 'America/New_York';

-- Convert data_sync_status table
ALTER TABLE data_sync_status 
ALTER COLUMN last_sync_timestamp TYPE TIMESTAMPTZ 
USING last_sync_timestamp AT TIME ZONE 'America/New_York';

ALTER TABLE data_sync_status 
ALTER COLUMN last_reading_timestamp TYPE TIMESTAMPTZ 
USING last_reading_timestamp AT TIME ZONE 'America/New_York';

ALTER TABLE data_sync_status 
ALTER COLUMN created_at TYPE TIMESTAMPTZ 
USING created_at AT TIME ZONE 'America/New_York';
"""

def run_migration():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print("🚀 Starting TIMESTAMPTZ migration...\n")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False  # Use transaction
        cur = conn.cursor()
        
        # Get count before
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND data_type = 'timestamp without time zone'
        """)
        before_count = cur.fetchone()[0]
        print(f"📊 Before: {before_count} columns with TIMESTAMP (without TZ)")
        
        # Run migration
        print("\n🔄 Running migration...")
        statements = [s.strip() for s in MIGRATION_SQL.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            # Extract table/column for progress
            if 'ALTER TABLE' in statement:
                parts = statement.split()
                table_idx = parts.index('TABLE') + 1
                table = parts[table_idx]
                print(f"   [{i}/{len(statements)}] Migrating {table}...", end=' ')
                
            cur.execute(statement)
            print("✅")
        
        # Get count after
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND data_type = 'timestamp without time zone'
        """)
        after_count = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND data_type = 'timestamp with time zone'
        """)
        tz_count = cur.fetchone()[0]
        
        # Commit transaction
        conn.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"\n📊 Results:")
        print(f"   Remaining TIMESTAMP columns: {after_count}")
        print(f"   TIMESTAMPTZ columns: {tz_count}")
        print(f"   Columns migrated: {before_count - after_count}")
        
        if after_count > 0:
            print(f"\n⚠️  Note: {after_count} timestamp columns remain (may be intentional)")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
