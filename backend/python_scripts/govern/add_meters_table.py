#!/usr/bin/env python3
"""
Add Meters Table Migration
Creates meters table to capture device-level metadata from /meters endpoint.

Following Argo Energy governance: Stage 2 (Govern - Schema Management)
"""
import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

def run_migration():
    """Create meters table and add meter_id to channels."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not configured")
        sys.exit(1)

    print("🔧 METERS TABLE MIGRATION")
    print("=" * 70)

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # 1. Create meters table
        print("\n1. Creating meters table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meters (
                meter_id integer PRIMARY KEY,
                device_id integer,
                meter_name text,
                data_type text,
                ct_ratio text,
                voltage_scale text,
                channel_count integer,
                interface_name text,
                interface_id integer,
                organization_id text,
                uuid text,
                parent_id integer,
                registered bigint,
                expires bigint,
                status text,
                created_at timestamptz DEFAULT NOW(),
                updated_at timestamptz DEFAULT NOW()
            );
            -- Note: No FK on device_id or meter_id since meters/channels
            -- may reference devices from sub-organizations not yet ingested.
        """)
        print("   ✅ meters table created")

        # 2. Add meter_id column to channels if not exists
        print("\n2. Adding meter_id to channels table...")
        cur.execute("""
            ALTER TABLE channels
            ADD COLUMN IF NOT EXISTS meter_id integer;
        """)
        print("   ✅ meter_id column added")

        # 3. Add foreign key constraint
        print("\n3. Adding foreign key constraint...")
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'fk_meter'
                ) THEN
                    ALTER TABLE channels
                    ADD CONSTRAINT fk_meter
                    FOREIGN KEY (meter_id) REFERENCES meters(meter_id);
                END IF;
            END $$;
        """)
        print("   ✅ Foreign key added")

        # 4. Create indexes
        print("\n4. Creating indexes...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_meters_device_id
                ON meters(device_id);
            CREATE INDEX IF NOT EXISTS idx_meters_org_id
                ON meters(organization_id);
            CREATE INDEX IF NOT EXISTS idx_channels_meter_id
                ON channels(meter_id);
        """)
        print("   ✅ Indexes created")

        # 5. Create view for meter-channel relationships
        print("\n5. Creating meter enrichment view...")
        cur.execute("""
            CREATE OR REPLACE VIEW v_meters_enriched AS
            SELECT
                m.meter_id,
                m.meter_name,
                m.data_type,
                m.ct_ratio,
                m.voltage_scale,
                m.channel_count,
                m.interface_name,
                m.organization_id,
                d.device_name,
                d.device_type,
                COUNT(c.channel_id) as linked_channels,
                STRING_AGG(c.channel_name, ', ') as channel_names
            FROM meters m
            LEFT JOIN devices d ON m.device_id = d.device_id
            LEFT JOIN channels c ON m.meter_id = c.meter_id
            GROUP BY
                m.meter_id, m.meter_name, m.data_type, m.ct_ratio,
                m.voltage_scale, m.channel_count, m.interface_name,
                m.organization_id, d.device_name, d.device_type;
        """)
        print("   ✅ View created: v_meters_enriched")

        # Commit all changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Show summary
        cur.execute("SELECT COUNT(*) FROM meters")
        meter_count = cur.fetchone()[0]
        print(f"\n📊 Current state:")
        print(f"   Meters in database: {meter_count}")

        if meter_count == 0:
            print("\n💡 Next step: Run ingestion to populate meters table")
            print("   npm run py:ingest -- --site 23271 --days 1")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
