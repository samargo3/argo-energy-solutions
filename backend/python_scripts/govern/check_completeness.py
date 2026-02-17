#!/usr/bin/env python3
"""
WCDS Data Completeness Audit — Govern Layer

Checks the Neon PostgreSQL database for gaps in WCDS Wilson Center data.
Hardware was installed 2025-04-29, so we expect 24 hourly readings per channel
per day from that date onward.

Reports:
  - Per-channel coverage (first/last reading, total records, % complete)
  - Missing days per channel
  - Gap summary for targeted re-ingestion

Usage:
  python backend/python_scripts/govern/check_completeness.py
  python backend/python_scripts/govern/check_completeness.py --since 2025-04-29
  python backend/python_scripts/govern/check_completeness.py --channel 162285
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import psycopg2
from dotenv import load_dotenv
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

sys.path.insert(0, str(_PKG_ROOT))
from config.report_config import READINGS_PER_DAY_HOURLY

# Wilson Center WCDS channels (hardware installed 2025-04-29)
WCDS_CHANNELS = {
    162119: 'RTU-2_WCDS_Wilson Ctr',
    162120: 'RTU-3_WCDS_Wilson Ctr',
    162121: 'AHU-2_WCDS_Wilson Ctr',
    162122: 'AHU-1A_WCDS_Wilson Ctr',
    162123: 'AHU-1B_WCDS_Wilson Ctr',
    162285: 'CDPK_Kitchen Main Panel(s)',
    162319: 'CDKH_Kitchen Panel(small)',
    162320: 'RTU-1_WCDS_Wilson Ctr',
}

INSTALL_DATE = date(2025, 4, 29)
EXPECTED_READINGS_PER_DAY = READINGS_PER_DAY_HOURLY


def connect() -> psycopg2.extensions.connection:
    url = os.getenv('DATABASE_URL')
    if not url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(url)


def get_channel_summary(conn, channel_id: int, since: date) -> Dict:
    """Get coverage stats for a single channel."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                MIN(timestamp) AS first_reading,
                MAX(timestamp) AS last_reading,
                COUNT(*) AS total_records,
                COUNT(DISTINCT DATE(timestamp)) AS days_with_data
            FROM readings
            WHERE channel_id = %s
              AND timestamp >= %s
        """, (channel_id, since))
        row = cur.fetchone()
        return {
            'first': row[0],
            'last': row[1],
            'total': row[2],
            'days_with_data': row[3],
        }


def get_missing_days(conn, channel_id: int, since: date, until: date) -> List[date]:
    """Find days with 0 readings for a channel in the given range."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DATE(timestamp) AS reading_date, COUNT(*) AS cnt
            FROM readings
            WHERE channel_id = %s
              AND timestamp >= %s
              AND timestamp < %s + INTERVAL '1 day'
            GROUP BY DATE(timestamp)
        """, (channel_id, since, until))
        present_days = {row[0] for row in cur.fetchall()}

    all_days = []
    current = since
    while current <= until:
        all_days.append(current)
        current += timedelta(days=1)

    return [d for d in all_days if d not in present_days]


def get_partial_days(conn, channel_id: int, since: date, until: date) -> List[Tuple[date, int]]:
    """Find days with < 24 readings (partial data)."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DATE(timestamp) AS reading_date, COUNT(*) AS cnt
            FROM readings
            WHERE channel_id = %s
              AND timestamp >= %s
              AND timestamp < %s + INTERVAL '1 day'
            GROUP BY DATE(timestamp)
            HAVING COUNT(*) < %s
            ORDER BY reading_date
        """, (channel_id, since, until, EXPECTED_READINGS_PER_DAY))
        return [(row[0], row[1]) for row in cur.fetchall()]


def collapse_date_ranges(dates: List[date]) -> List[Tuple[date, date]]:
    """Collapse a sorted list of dates into contiguous ranges for backfill commands."""
    if not dates:
        return []
    dates = sorted(dates)
    ranges = []
    start = dates[0]
    prev = dates[0]
    for d in dates[1:]:
        if (d - prev).days == 1:
            prev = d
        else:
            ranges.append((start, prev))
            start = d
            prev = d
    ranges.append((start, prev))
    return ranges


def main():
    parser = argparse.ArgumentParser(description='WCDS Data Completeness Audit')
    parser.add_argument('--since', type=str, default=INSTALL_DATE.isoformat(),
                        help=f'Check from this date (default: {INSTALL_DATE})')
    parser.add_argument('--until', type=str, default=None,
                        help='Check until this date (default: yesterday)')
    parser.add_argument('--channel', type=int, default=None,
                        help='Check a single channel ID')
    args = parser.parse_args()

    since = datetime.strptime(args.since, '%Y-%m-%d').date()
    until = datetime.strptime(args.until, '%Y-%m-%d').date() if args.until else (date.today() - timedelta(days=1))
    total_expected_days = (until - since).days + 1

    channels = {args.channel: WCDS_CHANNELS.get(args.channel, f'Channel {args.channel}')} if args.channel else WCDS_CHANNELS

    print("═" * 70)
    print("  WCDS Data Completeness Audit")
    print(f"  Range: {since} → {until} ({total_expected_days} days)")
    print(f"  Expected: {EXPECTED_READINGS_PER_DAY} readings/channel/day")
    print(f"  Channels: {len(channels)}")
    print("═" * 70)

    conn = connect()
    all_missing_ranges = []

    for ch_id, ch_name in channels.items():
        summary = get_channel_summary(conn, ch_id, since)
        missing = get_missing_days(conn, ch_id, since, until)
        partial = get_partial_days(conn, ch_id, since, until)

        pct = (summary['days_with_data'] / total_expected_days * 100) if total_expected_days > 0 else 0
        expected_total = total_expected_days * EXPECTED_READINGS_PER_DAY

        print(f"\n📊 {ch_id}: {ch_name}")
        print(f"   First reading:  {summary['first'] or 'NONE'}")
        print(f"   Last reading:   {summary['last'] or 'NONE'}")
        print(f"   Total records:  {summary['total']:,} / {expected_total:,} expected")
        print(f"   Days with data: {summary['days_with_data']} / {total_expected_days} ({pct:.1f}%)")

        if missing:
            ranges = collapse_date_ranges(missing)
            print(f"   ❌ Missing days: {len(missing)}")
            for r_start, r_end in ranges[:10]:
                if r_start == r_end:
                    print(f"      • {r_start}")
                else:
                    print(f"      • {r_start} → {r_end} ({(r_end - r_start).days + 1} days)")
                all_missing_ranges.append((r_start, r_end))
            if len(ranges) > 10:
                print(f"      ... and {len(ranges) - 10} more ranges")
        else:
            print(f"   ✅ No missing days")

        if partial:
            print(f"   ⚠️  Partial days: {len(partial)}")
            for d, cnt in partial[:5]:
                print(f"      • {d}: {cnt}/{EXPECTED_READINGS_PER_DAY} readings")
            if len(partial) > 5:
                print(f"      ... and {len(partial) - 5} more")

    # ── Backfill recommendations ──────────────────────────────────────
    if all_missing_ranges:
        # Merge overlapping ranges across all channels
        merged = collapse_date_ranges(
            sorted(set(d for r_start, r_end in all_missing_ranges
                       for d in [r_start + timedelta(days=i)
                                 for i in range((r_end - r_start).days + 1)]))
        )

        print("\n" + "═" * 70)
        print("  🔧 BACKFILL COMMANDS")
        print("═" * 70)
        for r_start, r_end in merged:
            print(f"\n  python backend/python_scripts/ingest/ingest_to_postgres.py \\")
            print(f"    --start-date {r_start} --end-date {r_end} --wcds-only")
        print()
    else:
        print("\n" + "═" * 70)
        print("  ✅ ALL DATA COMPLETE — no gaps found!")
        print("═" * 70)

    conn.close()


if __name__ == '__main__':
    main()
