#!/usr/bin/env python3
"""
Run the layered views SQL script against Neon.

Usage:
    python backend/python_scripts/run_create_views.py
    npm run db:views
"""

import os
import sys

# Project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv()

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 required. Install with: pip install psycopg2-binary")
    sys.exit(1)

SQL_PATH = os.path.join(ROOT, 'backend', 'scripts', 'database', 'create-layered-views.sql')


def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set in .env")
        sys.exit(1)

    if not os.path.isfile(SQL_PATH):
        print(f"❌ SQL file not found: {SQL_PATH}")
        sys.exit(1)

    with open(SQL_PATH, 'r') as f:
        sql = f.read()

    # Split into statements (semicolon at end of line or end of string)
    statements = []
    for raw in sql.replace('\r\n', '\n').split(';'):
        stmt = raw.strip()
        if not stmt or all(line.strip().startswith('--') or not line.strip() for line in stmt.split('\n')):
            continue
        statements.append(stmt)

    print("📐 Creating layered views and Option A analytics views...\n")

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        for i, stmt in enumerate(statements):
            if not stmt.strip():
                continue
            cur.execute(stmt + ';')
    except Exception as e:
        print(f"❌ Error: {e}")
        cur.close()
        conn.close()
        sys.exit(1)

    cur.close()
    conn.close()

    print("✅ All views created successfully.")
    print("\n📋 Created:")
    print("   Layer 1: v_clean_readings")
    print("   Layer 2: mv_hourly_usage (materialized) + unique index")
    print("   Option A: v_sites, v_meters, v_readings_enriched, v_latest_readings,")
    print("             v_readings_hourly, v_readings_daily, v_readings_monthly")
    print("\n💡 After each ingestion run, materialized views are refreshed automatically.")
    print("   Or run: npm run db:refresh-views")
    sys.exit(0)


if __name__ == '__main__':
    main()
