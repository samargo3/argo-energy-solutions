"""
Unit tests for lib/site_registry.py

Tests the fallback / default behavior without a live database.
The site_registry module gracefully falls back to a hardcoded default
when the `sites` table is missing — we verify that contract here.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Allow imports from the package root
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

import psycopg2.errors
from lib.site_registry import (
    get_active_sites,
    get_site,
    get_active_site_ids,
    _default_sites,
)


# ── _default_sites ──────────────────────────────────────────────

class TestDefaultSites:
    def test_returns_list(self):
        result = _default_sites()
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_wilson_center_present(self):
        result = _default_sites()
        ids = [s["site_id"] for s in result]
        assert 23271 in ids

    def test_required_keys(self):
        site = _default_sites()[0]
        for key in ("site_id", "site_name", "wcds_only", "resolution", "timezone"):
            assert key in site, f"Missing key: {key}"


# ── get_active_sites (fallback path) ────────────────────────────

class TestGetActiveSitesFallback:
    def _make_conn_that_raises(self, error):
        """Create a mock connection whose cursor raises the given error."""
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = error
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    def test_fallback_on_undefined_table(self):
        conn = self._make_conn_that_raises(
            psycopg2.errors.UndefinedTable("relation \"sites\" does not exist")
        )
        result = get_active_sites(conn)
        assert len(result) >= 1
        assert result[0]["site_id"] == 23271
        conn.rollback.assert_called_once()


# ── get_site (fallback path) ────────────────────────────────────

class TestGetSiteFallback:
    def _make_conn_that_raises(self, error):
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = error
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        return mock_conn

    def test_fallback_returns_wilson(self):
        conn = self._make_conn_that_raises(
            psycopg2.errors.UndefinedTable("relation \"sites\" does not exist")
        )
        result = get_site(conn, 23271)
        assert result is not None
        assert result["site_id"] == 23271

    def test_fallback_returns_none_for_unknown(self):
        conn = self._make_conn_that_raises(
            psycopg2.errors.UndefinedTable("relation \"sites\" does not exist")
        )
        result = get_site(conn, 99999)
        assert result is None


# ── get_active_site_ids ─────────────────────────────────────────

class TestGetActiveSiteIds:
    def test_returns_list_of_ints(self):
        mock_cur = MagicMock()
        mock_cur.execute.side_effect = psycopg2.errors.UndefinedTable("")
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        ids = get_active_site_ids(mock_conn)
        assert isinstance(ids, list)
        assert all(isinstance(i, int) for i in ids)
