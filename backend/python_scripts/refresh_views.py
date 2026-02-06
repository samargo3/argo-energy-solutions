#!/usr/bin/env python3
"""
Refresh materialized views after data ingestion.

Call this at the end of your ingestion script so analytics views stay current.
Uses REFRESH MATERIALIZED VIEW CONCURRENTLY so reads are not blocked.

Usage:
    from refresh_views import refresh_materialized_views
    refresh_materialized_views()
"""

import os
import sys
from typing import List, Optional

# Allow running from project root or backend/python_scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None

load_dotenv()


# Materialized views that support CONCURRENTLY (must have a UNIQUE index)
REFRESHABLE_VIEWS = [
    'mv_hourly_usage',
]


def refresh_materialized_views(
    db_url: Optional[str] = None,
    view_names: Optional[List[str]] = None,
    concurrent: bool = True,
    verbose: bool = True,
) -> bool:
    """
    Refresh materialized views after new data is loaded.

    Uses REFRESH MATERIALIZED VIEW CONCURRENTLY when possible so that
    queries can still read the old snapshot during refresh.

    Args:
        db_url: PostgreSQL connection string. Defaults to DATABASE_URL env.
        view_names: List of materialized view names. Defaults to REFRESHABLE_VIEWS.
        concurrent: If True, use CONCURRENTLY (requires unique index).
        verbose: If True, print progress.

    Returns:
        True if all refreshes succeeded, False otherwise.
    """
    if psycopg2 is None:
        if verbose:
            print("⚠️  psycopg2 not installed; skipping materialized view refresh")
        return False

    url = db_url or os.getenv('DATABASE_URL')
    if not url:
        if verbose:
            print("⚠️  DATABASE_URL not set; skipping materialized view refresh")
        return False

    names = view_names or REFRESHABLE_VIEWS
    if not names:
        return True

    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True  # REFRESH cannot run inside a transaction block
        cur = conn.cursor()
        all_ok = True

        for name in names:
            try:
                if concurrent:
                    cur.execute(f'REFRESH MATERIALIZED VIEW CONCURRENTLY {name}')
                else:
                    cur.execute(f'REFRESH MATERIALIZED VIEW {name}')
                if verbose:
                    print(f"   ✅ Refreshed {name}")
            except Exception as e:
                all_ok = False
                if verbose:
                    print(f"   ❌ {name}: {e}")

        cur.close()
        conn.close()
        return all_ok

    except Exception as e:
        if verbose:
            print(f"⚠️  Materialized view refresh failed: {e}")
        return False


def main():
    """CLI entrypoint for refreshing views."""
    import argparse
    p = argparse.ArgumentParser(description='Refresh materialized views after ingestion')
    p.add_argument('--no-concurrent', action='store_true', help='Use REFRESH without CONCURRENTLY')
    p.add_argument('-q', '--quiet', action='store_true', help='Suppress output')
    args = p.parse_args()

    ok = refresh_materialized_views(
        concurrent=not args.no_concurrent,
        verbose=not args.quiet,
    )
    if not args.quiet:
        print("\n✅ View refresh complete." if ok else "\n⚠️  Some refreshes failed.")
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
