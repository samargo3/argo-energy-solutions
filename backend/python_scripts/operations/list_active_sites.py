#!/usr/bin/env python3
"""
List Active Sites — CLI helper for pipeline orchestration.

Outputs active site IDs (one per line) so shell scripts and GitHub
Actions workflows can iterate over them without hardcoding.

Usage:
    python operations/list_active_sites.py
    # Output:
    # 23271

    # In a shell loop:
    for SITE in $(python operations/list_active_sites.py); do
        python ingest/ingest_to_postgres.py --site "$SITE" --days 3
    done

    # JSON output (for GitHub Actions matrix):
    python operations/list_active_sites.py --json
    # Output: [{"site_id":23271,"site_name":"Wilson Center","wcds_only":true,"resolution":3600}]
"""

import os
import sys
import json
import argparse
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env', override=False)

from lib.site_registry import get_active_sites


def main():
    parser = argparse.ArgumentParser(description='List active sites from the sites table')
    parser.add_argument('--json', action='store_true', help='Output as JSON array')
    args = parser.parse_args()

    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not configured", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    try:
        sites = get_active_sites(conn)
    finally:
        conn.close()

    if args.json:
        print(json.dumps(sites, default=str))
    else:
        for site in sites:
            print(site['site_id'])


if __name__ == '__main__':
    main()
