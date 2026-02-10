#!/usr/bin/env python3
"""
Sites Table Migration

Creates the `sites` table — the central registry for all monitored
customer locations.  Automated pipelines (daily sync, weekly reports)
query this table to discover which sites to process.

Following Argo Energy governance: Stage 2 (Govern — Schema Management)

Usage:
    python govern/create_sites_table.py
    npm run db:migrate:sites
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)


def run_migration():
    """Create sites table and seed with Wilson Center."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not configured")
        sys.exit(1)

    print("SITES TABLE MIGRATION")
    print("=" * 70)

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # ── 1. Create sites table ────────────────────────────────────
        print("\n1. Creating sites table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                site_id       integer     PRIMARY KEY,
                site_name     text        NOT NULL,
                is_active     boolean     NOT NULL DEFAULT true,
                wcds_only     boolean     NOT NULL DEFAULT true,
                resolution    integer     NOT NULL DEFAULT 3600,
                timezone      text        NOT NULL DEFAULT 'America/New_York',
                notes         text,
                created_at    timestamptz NOT NULL DEFAULT NOW(),
                updated_at    timestamptz NOT NULL DEFAULT NOW()
            );

            COMMENT ON TABLE  sites IS 'Central registry of monitored customer locations';
            COMMENT ON COLUMN sites.site_id    IS 'Eniscope organization_id';
            COMMENT ON COLUMN sites.is_active  IS 'Include in automated pipelines (daily sync, reports)';
            COMMENT ON COLUMN sites.wcds_only  IS 'Only fetch WCDS channels during ingestion';
            COMMENT ON COLUMN sites.resolution IS 'Default ingestion resolution in seconds (900=15min, 3600=1hr)';
        """)
        print("   sites table created")

        # ── 2. Seed Wilson Center ────────────────────────────────────
        print("\n2. Seeding Wilson Center (site 23271)...")
        cur.execute("""
            INSERT INTO sites (site_id, site_name, is_active, wcds_only, resolution, timezone, notes)
            VALUES (
                23271,
                'Wilson Center',
                true,
                true,
                3600,
                'America/New_York',
                'Eniscope 8 Hybrid — 8 WCDS channels. Hardware installed 2025-04-29.'
            )
            ON CONFLICT (site_id) DO UPDATE SET
                site_name  = EXCLUDED.site_name,
                updated_at = NOW();
        """)
        print("   Wilson Center seeded")

        # ── 3. Create index on is_active ─────────────────────────────
        print("\n3. Creating index for active-site lookups...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sites_active
                ON sites (is_active)
                WHERE is_active = true;
        """)
        print("   Index created")

        # ── 4. Create convenience view ───────────────────────────────
        print("\n4. Creating v_active_sites view...")
        cur.execute("""
            CREATE OR REPLACE VIEW v_active_sites AS
            SELECT site_id, site_name, wcds_only, resolution, timezone, notes
            FROM   sites
            WHERE  is_active = true
            ORDER  BY site_name;
        """)
        print("   View created: v_active_sites")

        # ── Commit ───────────────────────────────────────────────────
        conn.commit()
        print("\nMigration completed successfully!")

        # Show summary
        cur.execute("SELECT site_id, site_name, is_active FROM sites ORDER BY site_id")
        rows = cur.fetchall()
        print(f"\nRegistered sites ({len(rows)}):")
        for site_id, name, active in rows:
            status = "ACTIVE" if active else "INACTIVE"
            print(f"   {site_id}  {name:30s}  [{status}]")

    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    run_migration()
