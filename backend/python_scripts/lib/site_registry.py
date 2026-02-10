"""
Site Registry — query the `sites` table for active customer locations.

Used by pipeline scripts (daily sync, reports) to discover which sites
to process without hardcoding site IDs.

Usage:
    from lib.site_registry import get_active_sites, get_site

    sites = get_active_sites(conn)
    # [{'site_id': 23271, 'site_name': 'Wilson Center', ...}, ...]

    site = get_site(conn, 23271)
    # {'site_id': 23271, 'site_name': 'Wilson Center', ...}
"""

from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


def get_active_sites(conn) -> List[Dict]:
    """Return all active sites from the sites table.

    Each dict contains: site_id, site_name, wcds_only, resolution,
    timezone, notes.

    Falls back gracefully if the sites table doesn't exist yet
    (returns Wilson Center default so pipelines don't break before
    the migration runs).
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT site_id, site_name, wcds_only, resolution, timezone, notes
                FROM   sites
                WHERE  is_active = true
                ORDER  BY site_name
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows] if rows else _default_sites()
    except psycopg2.errors.UndefinedTable:
        conn.rollback()  # clear the error state
        return _default_sites()


def get_site(conn, site_id: int) -> Optional[Dict]:
    """Return a single site by ID, or None if not found.

    Falls back to a default if the sites table doesn't exist yet.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT site_id, site_name, wcds_only, resolution, timezone, notes
                FROM   sites
                WHERE  site_id = %s
            """, (site_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        defaults = {s['site_id']: s for s in _default_sites()}
        return defaults.get(site_id)


def get_active_site_ids(conn) -> List[int]:
    """Convenience — return just the list of active site IDs."""
    return [s['site_id'] for s in get_active_sites(conn)]


def _default_sites() -> List[Dict]:
    """Hardcoded fallback so pipelines work before the migration runs."""
    return [{
        'site_id': 23271,
        'site_name': 'Wilson Center',
        'wcds_only': True,
        'resolution': 3600,
        'timezone': 'America/New_York',
        'notes': 'Fallback default — run db:migrate:sites to populate the sites table.',
    }]
