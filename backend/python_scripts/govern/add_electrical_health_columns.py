#!/usr/bin/env python3
"""
Database migration: Add electrical health and phase-level columns to readings table.

Adds 20 new columns for:
- Electrical health screening (frequency, neutral current, THD, apparent power, cost)
- Phase-level measurements (V1-V3, I1-I3, P1-P3, PF1-PF3, E1-E3)

All statements are idempotent (ADD COLUMN IF NOT EXISTS).
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env')

MIGRATION_SQL = """
-- Electrical health fields
ALTER TABLE readings ADD COLUMN IF NOT EXISTS frequency_hz REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS neutral_current_a REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS thd_current REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS apparent_power_va REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS cost REAL;

-- Phase-level voltage (Line-to-Neutral)
ALTER TABLE readings ADD COLUMN IF NOT EXISTS voltage_v1 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS voltage_v2 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS voltage_v3 REAL;

-- Phase-level current
ALTER TABLE readings ADD COLUMN IF NOT EXISTS current_a1 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS current_a2 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS current_a3 REAL;

-- Phase-level power (stored as kW after conversion)
ALTER TABLE readings ADD COLUMN IF NOT EXISTS power_w1 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS power_w2 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS power_w3 REAL;

-- Phase-level power factor
ALTER TABLE readings ADD COLUMN IF NOT EXISTS power_factor_1 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS power_factor_2 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS power_factor_3 REAL;

-- Phase-level energy (stored as kWh after conversion)
ALTER TABLE readings ADD COLUMN IF NOT EXISTS energy_wh1 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS energy_wh2 REAL;
ALTER TABLE readings ADD COLUMN IF NOT EXISTS energy_wh3 REAL;
"""


def run_migration():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in environment")
        return False

    print("Starting electrical health columns migration...\n")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        # Count existing columns before
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'readings'
        """)
        before_count = cur.fetchone()[0]
        print(f"Before: {before_count} columns in readings table")

        # Run migration
        statements = [s.strip() for s in MIGRATION_SQL.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            if 'ADD COLUMN' in statement:
                col_name = statement.split('IF NOT EXISTS')[-1].strip().split()[0]
                print(f"   [{i}/{len(statements)}] Adding {col_name}...", end=' ')
            cur.execute(statement)
            print("done")

        # Count after
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'readings'
        """)
        after_count = cur.fetchone()[0]

        conn.commit()

        added = after_count - before_count
        print(f"\nMigration complete!")
        print(f"   Columns before: {before_count}")
        print(f"   Columns after:  {after_count}")
        print(f"   Columns added:  {added}")

        if added == 0:
            print("   (All columns already existed - migration is idempotent)")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\nMigration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
