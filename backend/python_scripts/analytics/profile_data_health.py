#!/usr/bin/env python3
"""
Data Health Profile for Energy Readings

Analyzes the quality and coverage of data in the Neon database (readings table).
Run from project root with: python -m backend.python_scripts.analytics.profile_data_health
Or: cd backend/python_scripts && python -m analytics.profile_data_health

Requirements: DATABASE_URL in .env
"""

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

# Table name: main energy readings table (channel_id, timestamp, energy_kwh, ...)
TABLE_NAME = "readings"
TIMESTAMP_COL = "timestamp"
ENERGY_COL = "energy_kwh"
GAP_THRESHOLD_HOURS = 1


def _fmt_interval(seconds: float) -> str:
    """Format seconds as human-readable interval (e.g. 900 -> '15 min')."""
    if seconds is None or seconds < 0:
        return "N/A"
    if seconds < 60:
        return f"{int(seconds)} sec"
    if seconds < 3600:
        return f"{int(seconds / 60)} min"
    if seconds < 86400:
        return f"{round(seconds / 3600, 1)} hour"
    return f"{round(seconds / 86400, 1)} day"


def run_profile(db_url: str) -> None:
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)

    try:
        with conn.cursor() as cur:
            # ----- Date range -----
            cur.execute(
                f"""
                SELECT MIN({TIMESTAMP_COL}) AS min_ts, MAX({TIMESTAMP_COL}) AS max_ts
                FROM {TABLE_NAME}
                """
            )
            row = cur.fetchone()
            min_ts = row["min_ts"]
            max_ts = row["max_ts"]

            # ----- Total rows -----
            cur.execute(f"SELECT COUNT(*) AS n FROM {TABLE_NAME}")
            total_rows = cur.fetchone()["n"]

            # ----- Resolution: most common time difference between consecutive rows -----
            # Compute deltas per channel, then aggregate
            cur.execute(
                f"""
                WITH deltas AS (
                    SELECT
                        EXTRACT(EPOCH FROM (
                            {TIMESTAMP_COL} - LAG({TIMESTAMP_COL}) OVER (
                                PARTITION BY channel_id ORDER BY {TIMESTAMP_COL}
                            )
                        )) AS delta_seconds
                    FROM {TABLE_NAME}
                )
                SELECT delta_seconds, COUNT(*) AS cnt
                FROM deltas
                WHERE delta_seconds IS NOT NULL AND delta_seconds > 0
                GROUP BY delta_seconds
                ORDER BY cnt DESC
                LIMIT 20
                """
            )
            resolution_rows = cur.fetchall()
            if resolution_rows:
                top_interval_seconds = float(resolution_rows[0]["delta_seconds"])
                top_count = resolution_rows[0]["cnt"]
                resolution_summary = (
                    f"{_fmt_interval(top_interval_seconds)} "
                    f"({top_count:,} occurrences)"
                )
                resolution_detail = [
                    (float(r["delta_seconds"]), r["cnt"]) for r in resolution_rows
                ]
            else:
                resolution_summary = "N/A (no consecutive rows or single row)"
                top_interval_seconds = None
                resolution_detail = []

            # ----- Gap detection: time jumps larger than threshold -----
            cur.execute(
                f"""
                WITH gaps AS (
                    SELECT
                        channel_id,
                        {TIMESTAMP_COL} AS gap_end,
                        LAG({TIMESTAMP_COL}) OVER (
                            PARTITION BY channel_id ORDER BY {TIMESTAMP_COL}
                        ) AS gap_start,
                        EXTRACT(EPOCH FROM (
                            {TIMESTAMP_COL} - LAG({TIMESTAMP_COL}) OVER (
                                PARTITION BY channel_id ORDER BY {TIMESTAMP_COL}
                            )
                        )) / 3600.0 AS gap_hours
                    FROM {TABLE_NAME}
                )
                SELECT channel_id, gap_start, gap_end, gap_hours
                FROM gaps
                WHERE gap_hours > %s
                ORDER BY gap_hours DESC
                LIMIT 50
                """,
                (GAP_THRESHOLD_HOURS,),
            )
            gap_rows = cur.fetchall()
            gap_count = len(gap_rows)

            # ----- Zero check: rows with energy_kwh = 0 -----
            cur.execute(
                f"SELECT COUNT(*) AS n FROM {TABLE_NAME} WHERE {ENERGY_COL} = 0"
            )
            zero_energy_count = cur.fetchone()["n"]

            # ----- Null energy check -----
            cur.execute(
                f"SELECT COUNT(*) AS n FROM {TABLE_NAME} WHERE {ENERGY_COL} IS NULL"
            )
            null_energy_count = cur.fetchone()["n"]

        # ----- Print summary -----
        sep = "=" * 60
        print()
        print(sep)
        print("  DATA HEALTH PROFILE — " + TABLE_NAME)
        print(sep)
        print()
        print("  Date range")
        print("  ---------")
        print(f"    Min timestamp:  {min_ts}")
        print(f"    Max timestamp:  {max_ts}")
        if min_ts and max_ts and total_rows:
            try:
                span_days = (max_ts - min_ts).total_seconds() / 86400
                print(f"    Span:           {span_days:.1f} days")
            except Exception:
                pass
        print()
        print("  Total rows")
        print("  ----------")
        print(f"    Count:         {total_rows:,}")
        print()
        print("  Resolution check (most common interval between consecutive rows)")
        print("  -----------------------------------------------------------------")
        print(f"    Primary:      {resolution_summary}")
        if resolution_detail and len(resolution_detail) > 1:
            print("    Top intervals:")
            for sec, cnt in resolution_detail[:5]:
                print(f"      {_fmt_interval(sec):>12}  {cnt:,} occurrences")
        print()
        print("  Gap detection (time jumps > " + str(GAP_THRESHOLD_HOURS) + " hour)")
        print("  ------------------------------------------------------------")
        print(f"    Gaps found:    {gap_count}")
        if gap_rows:
            print("    Sample (channel_id, gap_start, gap_end, gap_hours):")
            for r in gap_rows[:10]:
                print(
                    f"      {r['channel_id']}  {r['gap_start']}  {r['gap_end']}  {r['gap_hours']:.2f}h"
                )
        print()
        print("  Zero / null energy")
        print("  ------------------")
        print(f"    Rows with energy_kwh = 0:  {zero_energy_count:,}")
        print(f"    Rows with energy_kwh NULL: {null_energy_count:,}")
        if total_rows and total_rows > 0:
            pct_zero = 100.0 * zero_energy_count / total_rows
            pct_null = 100.0 * null_energy_count / total_rows
            print(f"    Percent zero:  {pct_zero:.2f}%")
            print(f"    Percent null:  {pct_null:.2f}%")
        print()
        print(sep)
        print()

    finally:
        conn.close()


def main() -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment. Set it in .env at project root.")
        sys.exit(1)
    run_profile(db_url)


if __name__ == "__main__":
    main()
