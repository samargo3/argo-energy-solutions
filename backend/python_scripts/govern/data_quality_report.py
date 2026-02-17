#!/usr/bin/env python3
"""
Data Quality Report
Identifies missing data, gaps, anomalies, and quality issues.
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
from config.report_config import READINGS_PER_DAY_15MIN

def generate_quality_report(days=7):
    """Generate data quality report for last N days."""
    db_url = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    print("📊 DATA QUALITY REPORT")
    print("=" * 80)
    print(f"Analysis Period: Last {days} days\n")

    # 1. Expected vs Actual readings per channel
    cur.execute("""
        WITH channel_stats AS (
            SELECT
                c.channel_id,
                c.channel_name,
                COUNT(r.timestamp) as actual_readings,
                %s * %s as expected_readings,
                ROUND(COUNT(r.timestamp)::numeric / (%s * %s) * 100, 1) as completeness_pct
            FROM channels c
            LEFT JOIN readings r ON c.channel_id = r.channel_id
                AND r.timestamp >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY c.channel_id, c.channel_name
        )
        SELECT * FROM channel_stats
        ORDER BY completeness_pct ASC
    """, (days, READINGS_PER_DAY_15MIN, days, READINGS_PER_DAY_15MIN, days))

    print("1. CHANNEL COMPLETENESS")
    print("-" * 80)
    print(f"{'Channel':<30} {'Actual':>10} {'Expected':>10} {'Complete':>10}")
    print("-" * 80)

    issues = []
    for row in cur.fetchall():
        channel_name = row[1][:28]
        actual = row[2]
        expected = row[3]
        pct = row[4]

        status = "✅" if pct >= 95 else "⚠️" if pct >= 80 else "❌"
        print(f"{status} {channel_name:<28} {actual:>10,} {expected:>10,} {pct:>9}%")

        if pct < 95:
            issues.append(f"{channel_name}: {pct}% complete")

    # 2. Check for gaps (missing time periods)
    cur.execute("""
        WITH time_series AS (
            SELECT generate_series(
                DATE_TRUNC('hour', CURRENT_TIMESTAMP - INTERVAL '%s days'),
                DATE_TRUNC('hour', CURRENT_TIMESTAMP),
                INTERVAL '1 hour'
            ) as hour
        ),
        readings_per_hour AS (
            SELECT
                DATE_TRUNC('hour', timestamp) as hour,
                COUNT(*) as reading_count
            FROM readings
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            GROUP BY DATE_TRUNC('hour', timestamp)
        )
        SELECT
            ts.hour,
            COALESCE(rph.reading_count, 0) as readings
        FROM time_series ts
        LEFT JOIN readings_per_hour rph ON ts.hour = rph.hour
        WHERE COALESCE(rph.reading_count, 0) = 0
        ORDER BY ts.hour DESC
        LIMIT 10
    """, (days, days))

    gaps = cur.fetchall()
    print(f"\n2. DATA GAPS (Hours with 0 readings)")
    print("-" * 80)
    if gaps:
        for gap in gaps:
            print(f"⚠️  {gap[0]}: No readings")
            issues.append(f"Gap at {gap[0]}")
    else:
        print("✅ No gaps detected")

    # 3. Null value analysis
    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE energy_kwh IS NULL) as null_energy,
            COUNT(*) FILTER (WHERE power_kw IS NULL) as null_power,
            COUNT(*) FILTER (WHERE voltage_v IS NULL) as null_voltage,
            COUNT(*) FILTER (WHERE current_a IS NULL) as null_current
        FROM readings
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
    """ % days)

    null_stats = cur.fetchone()
    print(f"\n3. NULL VALUE ANALYSIS")
    print("-" * 80)
    print(f"Total Readings:   {null_stats[0]:>10,}")
    print(f"Null Energy:      {null_stats[1]:>10,} ({null_stats[1]/null_stats[0]*100:.1f}%)")
    print(f"Null Power:       {null_stats[2]:>10,} ({null_stats[2]/null_stats[0]*100:.1f}%)")
    print(f"Null Voltage:     {null_stats[3]:>10,} ({null_stats[3]/null_stats[0]*100:.1f}%)")
    print(f"Null Current:     {null_stats[4]:>10,} ({null_stats[4]/null_stats[0]*100:.1f}%)")

    # 4. Anomaly detection (outliers)
    cur.execute("""
        WITH stats AS (
            SELECT
                AVG(power_kw) as avg_power,
                STDDEV(power_kw) as stddev_power
            FROM readings
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND power_kw IS NOT NULL
        )
        SELECT COUNT(*) as outlier_count
        FROM readings, stats
        WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            AND power_kw IS NOT NULL
            AND ABS(power_kw - stats.avg_power) > 3 * stats.stddev_power
    """ % (days, days))

    outliers = cur.fetchone()[0]
    print(f"\n4. ANOMALY DETECTION")
    print("-" * 80)
    print(f"Outliers (>3σ):   {outliers:>10,}")
    if outliers > 0:
        issues.append(f"{outliers} statistical outliers detected")

    # Summary
    print(f"\n{'=' * 80}")
    print(f"📋 SUMMARY")
    print(f"{'=' * 80}")
    if issues:
        print(f"⚠️  {len(issues)} issues detected:\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No significant data quality issues detected")

    cur.close()
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate data quality report')
    parser.add_argument('--days', type=int, default=7, help='Days to analyze (default: 7)')
    args = parser.parse_args()

    generate_quality_report(args.days)
