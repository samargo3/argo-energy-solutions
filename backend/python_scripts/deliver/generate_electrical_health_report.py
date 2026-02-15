#!/usr/bin/env python3
"""
Electrical Health Screening Report — CLI Wrapper

Generates a professional PDF report for Facilities/Electrical stakeholders.
Covers: voltage stability, max current events, frequency excursions,
neutral current indicators, and current THD analysis.

Usage:
    python generate_electrical_health_report.py --site 23271
    python generate_electrical_health_report.py --site 23271 --start-date 2026-01-01 --end-date 2026-01-31
    python generate_electrical_health_report.py --site 23271 --nominal-voltage 208
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env')

# Also add the python_reports package to path
_REPORTS_PKG = _PROJECT_ROOT / 'backend' / 'python_reports' / 'scripts'
if str(_REPORTS_PKG) not in sys.path:
    sys.path.insert(0, str(_REPORTS_PKG))


def main():
    parser = argparse.ArgumentParser(
        description='Generate Electrical Health Screening PDF Report')
    parser.add_argument('--site', required=True, help='Site/organization ID')
    parser.add_argument('--start-date',
                        help='Start date YYYY-MM-DD (default: 30 days ago)')
    parser.add_argument('--end-date',
                        help='End date YYYY-MM-DD (default: today)')
    parser.add_argument('--nominal-voltage', type=int,
                        choices=[120, 208, 277, 480],
                        help='Nominal voltage (auto-detected if omitted)')
    parser.add_argument('--output', default=str(_PROJECT_ROOT / 'reports'),
                        help='Output directory')
    args = parser.parse_args()

    # Resolve dates
    end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')
    start_date = args.start_date or (
        datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # Connect to database
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in environment")
        sys.exit(1)

    print(f"Generating Electrical Health Screening Report")
    print(f"  Site: {args.site}")
    print(f"  Period: {start_date} to {end_date}")
    if args.nominal_voltage:
        print(f"  Nominal Voltage: {args.nominal_voltage}V")
    else:
        print(f"  Nominal Voltage: auto-detect")
    print()

    try:
        conn = psycopg2.connect(db_url)

        from generate_electrical_health_report import ElectricalHealthReportGenerator

        generator = ElectricalHealthReportGenerator(
            conn=conn,
            site_id=args.site,
            start_date=start_date,
            end_date=end_date,
            nominal_voltage=args.nominal_voltage,
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
