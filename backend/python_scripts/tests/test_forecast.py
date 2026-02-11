"""Tests for analyze/forecast.py — Prophet-based energy forecasting"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure package root is importable
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from analyze.forecast import generate_forecast, _fetch_hourly_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hourly_df(days: int = 14) -> pd.DataFrame:
    """Create a synthetic hourly energy DataFrame for testing."""
    hours = days * 24
    base = datetime(2026, 1, 1)
    timestamps = [base + timedelta(hours=h) for h in range(hours)]
    # Simple sinusoidal pattern (mimics daily usage cycle)
    import math
    values = [10 + 5 * math.sin(2 * math.pi * h / 24) + (h % 7) * 0.1 for h in range(hours)]
    return pd.DataFrame({"ds": timestamps, "y": values})


def _mock_cursor_with_data(df: pd.DataFrame):
    """Create a mock connection whose cursor returns the given DataFrame rows."""
    rows = [(row["ds"], row["y"]) for _, row in df.iterrows()]
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = rows
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


# ---------------------------------------------------------------------------
# Tests: _fetch_hourly_data
# ---------------------------------------------------------------------------

class TestFetchHourlyData:
    def test_returns_empty_df_when_no_rows(self):
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        result = _fetch_hourly_data(mock_conn, site_id=1, lookback_days=30)
        assert result.empty
        assert list(result.columns) == ["ds", "y"]

    def test_returns_dataframe_with_data(self):
        df = _make_hourly_df(days=3)
        mock_conn = _mock_cursor_with_data(df)
        result = _fetch_hourly_data(mock_conn, site_id=1, lookback_days=30)
        assert len(result) == 72  # 3 days * 24 hours
        assert "ds" in result.columns
        assert "y" in result.columns


# ---------------------------------------------------------------------------
# Tests: generate_forecast
# ---------------------------------------------------------------------------

class TestGenerateForecast:
    def test_insufficient_data_returns_error(self):
        """With <48 rows, should return an error summary."""
        # Only 1 day = 24 rows
        df = _make_hourly_df(days=1)
        mock_conn = _mock_cursor_with_data(df)

        result = generate_forecast(mock_conn, site_id=1, horizon_days=7, lookback_days=30)

        assert result["forecast"] == []
        assert "error" in result["summary"]
        assert result["summary"]["rows_available"] == 24
        assert result["model_info"] is None

    def test_forecast_produces_results(self):
        """With enough data, should produce a valid forecast."""
        df = _make_hourly_df(days=30)
        mock_conn = _mock_cursor_with_data(df)

        result = generate_forecast(
            mock_conn, site_id=1, horizon_days=7, lookback_days=90
        )

        # Should have forecast data
        assert len(result["forecast"]) == 7 * 24  # 7 days * 24 hours
        assert result["summary"]["horizon_days"] == 7
        assert result["summary"]["total_predicted_kwh"] > 0
        assert result["model_info"] is not None
        assert "daily" in result["model_info"]["seasonalities"]

    def test_forecast_values_are_non_negative(self):
        """Predicted values should be clamped to >= 0."""
        df = _make_hourly_df(days=14)
        mock_conn = _mock_cursor_with_data(df)

        result = generate_forecast(
            mock_conn, site_id=1, horizon_days=7, lookback_days=90
        )

        for row in result["forecast"]:
            assert row["predicted_kwh"] >= 0
            assert row["lower_bound"] >= 0

    def test_daily_forecast_aggregation(self):
        """Summary should contain daily forecast breakdown."""
        df = _make_hourly_df(days=14)
        mock_conn = _mock_cursor_with_data(df)

        result = generate_forecast(
            mock_conn, site_id=1, horizon_days=7, lookback_days=90
        )

        daily = result["summary"]["daily_forecast"]
        assert len(daily) == 7
        for day in daily:
            assert "date" in day
            assert "predicted_kwh" in day
            assert day["predicted_kwh"] > 0

    def test_trend_direction_computed(self):
        """Summary should include trend_direction when >= 2 forecast days."""
        df = _make_hourly_df(days=14)
        mock_conn = _mock_cursor_with_data(df)

        result = generate_forecast(
            mock_conn, site_id=1, horizon_days=7, lookback_days=90
        )

        summary = result["summary"]
        assert "trend_direction" in summary
        assert summary["trend_direction"] in ("increasing", "decreasing", "stable")
