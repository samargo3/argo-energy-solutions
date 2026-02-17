#!/usr/bin/env python3
"""
Ingestion Health Monitor
Checks if data is being ingested regularly and alerts if stale.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

sys.path.insert(0, str(_PKG_ROOT))
from config.report_config import STALE_CRITICAL_HOURS, STALE_WARNING_HOURS

def check_ingestion_health():
    """Check if data ingestion is healthy."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not configured")
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Check last reading timestamp
    cur.execute("SELECT MAX(timestamp) FROM readings")
    last_reading = cur.fetchone()[0]

    if not last_reading:
        print("❌ No readings found in database")
        sys.exit(1)

    # Check how stale the data is
    now = datetime.now(last_reading.tzinfo)
    hours_stale = (now - last_reading).total_seconds() / 3600

    print("🔍 INGESTION HEALTH CHECK")
    print("=" * 60)
    print(f"Last Reading:  {last_reading}")
    print(f"Current Time:  {now}")
    print(f"Hours Stale:   {hours_stale:.1f} hours")
    print()

    # Alert thresholds
    if hours_stale > STALE_CRITICAL_HOURS:
        print(f"🚨 CRITICAL: Data is >{STALE_CRITICAL_HOURS} hours stale!")
        print("   Action: Check API credentials and run ingestion")
        sys.exit(2)
    elif hours_stale > STALE_WARNING_HOURS:
        print(f"⚠️  WARNING: Data is >{STALE_WARNING_HOURS} hours stale")
        print("   Action: Investigate ingestion process")
        sys.exit(1)
    else:
        print("✅ HEALTHY: Data is current")
        sys.exit(0)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_ingestion_health()
