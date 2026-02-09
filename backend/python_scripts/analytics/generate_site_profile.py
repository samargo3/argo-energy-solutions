#!/usr/bin/env python3
"""
Site Energy Profile — Key Performance Indicators (KPIs)

Derives energy insights from Nov–Feb (or custom range) using Layer 3 business data
(v_readings_enriched). Read-only analytics: average daily consumption, day vs. night
power, weekday vs. weekend, and baseload.

Analysis:
  - Average Daily Consumption: Total kWh / Number of Days
  - Day vs. Night: Avg Power (kW) — Day 9 AM–5 PM, Night 8 PM–6 AM
  - Weekday vs. Weekend: Avg Daily kWh
  - Baseload: Minimum consistent power draw (10th percentile of readings)

Usage:
  python backend/python_scripts/analytics/generate_site_profile.py
  python backend/python_scripts/analytics/generate_site_profile.py --site 23271
  python backend/python_scripts/analytics/generate_site_profile.py --start 2024-11-01 --end 2025-02-28
  npm run py:site-profile

Requirements: DATABASE_URL in .env
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / ".env")


def run_site_profile(
    db_url: str,
    site_id: str,
    start_date: str,
    end_date: str,
) -> None:
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)

    try:
        with conn.cursor() as cur:
            # Resolve site name for display
            cur.execute(
                """
                SELECT organization_id, organization_name
                FROM organizations
                WHERE organization_id = %s
                """,
                (site_id,),
            )
            org = cur.fetchone()
            site_name = org["organization_name"] if org else site_id

            # ----- 1. Average Daily Consumption (Total kWh / Number of Days) -----
            cur.execute(
                """
                WITH site_readings AS (
                    SELECT timestamp, energy_kwh, power_kw
                    FROM v_readings_enriched
                    WHERE site_id = %s
                      AND timestamp >= %s::date
                      AND timestamp < (%s::date + INTERVAL '1 day')
                ),
                totals AS (
                    SELECT
                        COUNT(DISTINCT DATE(timestamp)) AS days_with_data,
                        MIN(timestamp)::date AS first_date,
                        MAX(timestamp)::date AS last_date,
                        SUM(energy_kwh) AS total_kwh
                    FROM site_readings
                )
                SELECT
                    total_kwh,
                    days_with_data,
                    first_date,
                    last_date,
                    (last_date - first_date + 1) AS span_days
                FROM totals
                """,
                (site_id, start_date, end_date),
            )
            row = cur.fetchone()
            total_kwh = float(row["total_kwh"] or 0)
            days_with_data = row["days_with_data"] or 0
            first_date = row["first_date"]
            last_date = row["last_date"]
            span_days = max(1, (row["span_days"] or 1))
            avg_daily_kwh = total_kwh / span_days if total_kwh else 0

            # ----- 2. Day vs. Night: Avg Power (kW) — Day 9 AM–5 PM, Night 8 PM–6 AM -----
            cur.execute(
                """
                WITH site_readings AS (
                    SELECT timestamp, power_kw, EXTRACT(HOUR FROM timestamp) AS hour
                    FROM v_readings_enriched
                    WHERE site_id = %s
                      AND timestamp >= %s::date
                      AND timestamp < (%s::date + INTERVAL '1 day')
                      AND power_kw IS NOT NULL
                )
                SELECT
                    AVG(CASE WHEN hour >= 9 AND hour < 17 THEN power_kw END) AS avg_power_day,
                    AVG(CASE WHEN hour >= 20 OR hour < 6 THEN power_kw END) AS avg_power_night
                FROM site_readings
                """,
                (site_id, start_date, end_date),
            )
            day_night = cur.fetchone()
            avg_power_day = float(day_night["avg_power_day"] or 0)
            avg_power_night = float(day_night["avg_power_night"] or 0)

            # ----- 3. Weekday vs. Weekend: Avg Daily kWh -----
            cur.execute(
                """
                WITH site_readings AS (
                    SELECT timestamp, energy_kwh,
                           DATE(timestamp) AS d,
                           EXTRACT(DOW FROM timestamp) AS dow
                    FROM v_readings_enriched
                    WHERE site_id = %s
                      AND timestamp >= %s::date
                      AND timestamp < (%s::date + INTERVAL '1 day')
                ),
                daily_kwh AS (
                    SELECT d, dow, SUM(energy_kwh) AS day_kwh
                    FROM site_readings
                    GROUP BY d, dow
                )
                SELECT
                    AVG(CASE WHEN dow IN (0, 6) THEN day_kwh END) AS avg_kwh_weekend,
                    AVG(CASE WHEN dow NOT IN (0, 6) THEN day_kwh END) AS avg_kwh_weekday
                FROM daily_kwh
                """,
                (site_id, start_date, end_date),
            )
            wd_we = cur.fetchone()
            avg_kwh_weekend = float(wd_we["avg_kwh_weekend"] or 0)
            avg_kwh_weekday = float(wd_we["avg_kwh_weekday"] or 0)

            # ----- 4. Baseload: 10th percentile of power (minimum consistent draw) -----
            cur.execute(
                """
                SELECT PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY power_kw) AS p10_power_kw
                FROM v_readings_enriched
                WHERE site_id = %s
                  AND timestamp >= %s::date
                  AND timestamp < (%s::date + INTERVAL '1 day')
                  AND power_kw IS NOT NULL
                  AND power_kw >= 0
                """,
                (site_id, start_date, end_date),
            )
            baseload_row = cur.fetchone()
            baseload_kw = float(baseload_row["p10_power_kw"] or 0)

        # ----- Print KPIs -----
        sep = "=" * 58
        print()
        print(sep)
        print("  SITE PROFILE — Key Performance Indicators (KPIs)")
        print(sep)
        print()
        print(f"  Site: {site_name} (id: {site_id})")
        print(f"  Period: {start_date} → {end_date}")
        span_str = f"{first_date} to {last_date}" if (first_date and last_date) else "no data"
        print(f"  Days with data: {days_with_data}  (span: {span_str})")
        print()
        print("  ── Average Daily Consumption ──")
        print(f"    Total kWh (period):  {total_kwh:,.1f} kWh")
        print(f"    Avg daily consumption: {avg_daily_kwh:,.1f} kWh/day")
        print()
        print("  ── Day vs. Night (Avg Power) ──")
        print(f"    Day (9 AM–5 PM):   {avg_power_day:,.2f} kW")
        print(f"    Night (8 PM–6 AM): {avg_power_night:,.2f} kW")
        day_night_ratio = (avg_power_day / avg_power_night) if avg_power_night else 0
        print(f"    Day/Night ratio:   {day_night_ratio:.2f}")
        print()
        print("  ── Weekday vs. Weekend (Avg Daily kWh) ──")
        print(f"    Weekday: {avg_kwh_weekday:,.1f} kWh/day")
        print(f"    Weekend: {avg_kwh_weekend:,.1f} kWh/day")
        wd_we_ratio = (avg_kwh_weekday / avg_kwh_weekend) if avg_kwh_weekend else 0
        print(f"    Weekday/Weekend:   {wd_we_ratio:.2f}")
        print()
        print("  ── Baseload (10th percentile power) ──")
        print(f"    Baseload: {baseload_kw:,.2f} kW")
        print()
        print(sep)
        print()

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate site energy profile KPIs from Nov–Feb (or custom) data."
    )
    parser.add_argument(
        "--site",
        default="23271",
        help="Organization/site ID (default: 23271)",
    )
    parser.add_argument(
        "--start",
        default="2024-11-01",
        help="Start date YYYY-MM-DD (default: 2024-11-01)",
    )
    parser.add_argument(
        "--end",
        default="2025-02-28",
        help="End date YYYY-MM-DD (default: 2025-02-28)",
    )
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment. Set it in .env at project root.")
        sys.exit(1)

    run_site_profile(
        db_url=db_url,
        site_id=args.site,
        start_date=args.start,
        end_date=args.end,
    )


if __name__ == "__main__":
    main()
