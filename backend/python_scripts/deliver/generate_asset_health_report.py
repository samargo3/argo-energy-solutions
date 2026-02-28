#!/usr/bin/env python3
"""
Asset Health & Use Assessment Report — CLI Wrapper

Generates a non-technical, impact-focused PDF for Westchester Country Day
School facilities and operations managers: which equipment consumes the most
energy, what it costs, and what to do about it.

Usage:
    python generate_asset_health_report.py --site 23271
    python generate_asset_health_report.py --site 23271 --start 2026-01-01 --end 2026-01-28
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

_PKG_ROOT     = Path(__file__).resolve().parent.parent        # python_scripts/
_PROJECT_ROOT = _PKG_ROOT.parent.parent                       # repo root
_REPORTS_PKG  = _PROJECT_ROOT / 'backend' / 'python_reports' / 'scripts'

if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
if str(_REPORTS_PKG) not in sys.path:
    sys.path.insert(0, str(_REPORTS_PKG))

load_dotenv(_PROJECT_ROOT / '.env')


def main():
    parser = argparse.ArgumentParser(
        description='Generate Asset Health & Use Assessment PDF')
    parser.add_argument(
        '--site', required=True,
        help='Site ID (e.g. 23271 for Westchester Country Day School)')
    parser.add_argument(
        '--start',
        help='Start date YYYY-MM-DD (default: 28 days ago)')
    parser.add_argument(
        '--end',
        help='End date YYYY-MM-DD (default: yesterday)')
    parser.add_argument(
        '--output',
        default=str(_PROJECT_ROOT / 'reports'),
        help='Output directory (default: <repo>/reports)')
    args = parser.parse_args()

    # Default: last 4 complete weeks (28 days ending yesterday)
    end_date   = args.end   or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = args.start or (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in environment")
        sys.exit(1)

    print("Generating Asset Health & Use Assessment")
    print(f"  Site:   {args.site}")
    print(f"  Period: {start_date} to {end_date}")
    print(f"  Output: {args.output}")
    print()

    try:
        conn = psycopg2.connect(db_url)

        from generate_asset_health_report import AssetHealthReportGenerator

        generator = AssetHealthReportGenerator(
            conn=conn,
            site_id=args.site,
            start_date=start_date,
            end_date=end_date,
            output_dir=args.output,
        )
        pdf_path = generator.generate()

        conn.close()
        print(f"\nPDF saved to: {pdf_path}")

    except Exception as e:
        print(f"\nReport generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
