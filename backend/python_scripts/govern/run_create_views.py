#!/usr/bin/env python3
"""
Run the layered views SQL script against Neon.

Usage:
    python backend/python_scripts/run_create_views.py
    npm run db:views
"""

import os
import sys

# Project root (govern/ -> python_scripts/ -> backend/ -> project root)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
os.chdir(ROOT)

from pathlib import Path
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env')

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 required. Install with: pip install psycopg2-binary")
    sys.exit(1)

LAYERED_SQL_PATH = os.path.join(ROOT, 'backend', 'scripts', 'database', 'create-layered-views.sql')
DATA_CONTRACT_SQL_PATH = os.path.join(ROOT, 'backend', 'scripts', 'database', 'create-data-contract-views.sql')


def _load_sql_statements(path: str):
    if not os.path.isfile(path):
        print(f"❌ SQL file not found: {path}")
        sys.exit(1)

    with open(path, 'r') as f:
        sql = f.read()

    statements = []
    for raw in sql.replace('\r\n', '\n').split(';'):
        stmt = raw.strip()
        if not stmt or all(line.strip().startswith('--') or not line.strip() for line in stmt.split('\n')):
            continue
        statements.append(stmt)
    return statements


def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set in .env")
        sys.exit(1)

    layered_statements = _load_sql_statements(LAYERED_SQL_PATH)
    data_contract_statements = _load_sql_statements(DATA_CONTRACT_SQL_PATH)

    print("📐 Creating layered views and Option A analytics views...\n")

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # Create layered views (existing pipeline)
        for stmt in layered_statements:
            if not stmt.strip():
                continue
            cur.execute(stmt + ';')

        # Create data contract views (health + virtual metering)
        print("\n📐 Creating data contract views (health monitor + virtual metering)...\n")
        for stmt in data_contract_statements:
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
    print("   Data Contract: v_data_health_monitor, v_virtual_readings")
    print("\n💡 After each ingestion run, materialized views are refreshed automatically.")
    print("   Or run: npm run db:refresh-views")
    sys.exit(0)


if __name__ == '__main__':
    main()
