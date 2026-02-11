"""Tests for analyze/cost_model.py — TOU rate modeling & demand charge analysis"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from analyze.cost_model import (
    analyze_tou_costs,
    analyze_demand_charges,
    generate_cost_optimization_report,
    _classify_tou_period,
    DEFAULT_TOU_SCHEDULE,
    DEFAULT_FLAT_RATE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hourly_usage(days: int = 30):
    """Create synthetic hourly usage tuples (hour, total_kwh, peak_kw)."""
    import math
    base = datetime(2026, 1, 5, 0, 0)  # a Monday
    rows = []
    for h in range(days * 24):
        ts = base + timedelta(hours=h)
        # Business hours pattern: higher during 9-17
        hour_of_day = ts.hour
        if 9 <= hour_of_day <= 17:
            kwh = 50 + 20 * math.sin(math.pi * (hour_of_day - 9) / 8)
            kw = kwh * 1.1
        else:
            kwh = 10 + 5 * math.sin(math.pi * hour_of_day / 24)
            kw = kwh * 0.9
        rows.append((ts, kwh, kw))
    return rows


def _mock_conn_with_usage(days: int = 30):
    """Create a mock connection that returns synthetic hourly usage."""
    rows = _make_hourly_usage(days)
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = rows
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


def _mock_conn_empty():
    """Create a mock connection that returns no data."""
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    return mock_conn


# ---------------------------------------------------------------------------
# Tests: _classify_tou_period
# ---------------------------------------------------------------------------

class TestClassifyTouPeriod:
    def test_weekday_on_peak(self):
        """Weekday 2pm should be on-peak."""
        ts = pd.Timestamp("2026-01-05 14:00")  # Monday
        period, rate = _classify_tou_period(ts, DEFAULT_TOU_SCHEDULE)
        assert period == "on_peak"
        assert rate == 0.20

    def test_weekday_off_peak(self):
        """Weekday 3am should be off-peak."""
        ts = pd.Timestamp("2026-01-05 03:00")  # Monday
        period, rate = _classify_tou_period(ts, DEFAULT_TOU_SCHEDULE)
        assert period == "off_peak"
        assert rate == 0.06

    def test_weekday_mid_peak(self):
        """Weekday 9am should be mid-peak."""
        ts = pd.Timestamp("2026-01-05 09:00")  # Monday
        period, rate = _classify_tou_period(ts, DEFAULT_TOU_SCHEDULE)
        assert period == "mid_peak"
        assert rate == 0.10

    def test_weekend_always_off_peak(self):
        """Saturday 2pm should be off-peak."""
        ts = pd.Timestamp("2026-01-10 14:00")  # Saturday
        period, rate = _classify_tou_period(ts, DEFAULT_TOU_SCHEDULE)
        assert period == "off_peak"
        assert rate == 0.06

    def test_sunday_off_peak(self):
        """Sunday 10am should be off-peak."""
        ts = pd.Timestamp("2026-01-11 10:00")  # Sunday
        period, rate = _classify_tou_period(ts, DEFAULT_TOU_SCHEDULE)
        assert period == "off_peak"
        assert rate == 0.06


# ---------------------------------------------------------------------------
# Tests: analyze_tou_costs
# ---------------------------------------------------------------------------

class TestAnalyzeTouCosts:
    def test_empty_data(self):
        conn = _mock_conn_empty()
        result = analyze_tou_costs(conn, site_id=1, days=30)
        assert "error" in result

    def test_returns_cost_breakdown(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_tou_costs(conn, site_id=1, days=7)

        assert result["total_kwh"] > 0
        assert result["flat_total_cost"] > 0
        assert result["tou_total_cost"] > 0
        assert "period_breakdown" in result
        assert "on_peak" in result["period_breakdown"]
        assert "off_peak" in result["period_breakdown"]

    def test_flat_vs_tou_comparison(self):
        """TOU cost should differ from flat cost for varied usage."""
        conn = _mock_conn_with_usage(days=7)
        result = analyze_tou_costs(conn, site_id=1, days=7, flat_rate=0.12)

        # With variable pricing, flat and TOU should not be identical
        assert result["flat_total_cost"] != result["tou_total_cost"]
        assert "tou_vs_flat_savings" in result
        assert "tou_vs_flat_pct" in result

    def test_load_shift_opportunity(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_tou_costs(conn, site_id=1, days=7)

        opp = result["load_shift_opportunity"]
        assert "on_peak_kwh" in opp
        assert opp["potential_savings_per_kwh"] > 0  # on_peak - off_peak > 0

    def test_daily_detail(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_tou_costs(conn, site_id=1, days=7)
        assert len(result["daily_detail"]) == 7
        for day in result["daily_detail"]:
            assert "date" in day
            assert "kwh" in day
            assert day["kwh"] > 0


# ---------------------------------------------------------------------------
# Tests: analyze_demand_charges
# ---------------------------------------------------------------------------

class TestAnalyzeDemandCharges:
    def test_empty_data(self):
        conn = _mock_conn_empty()
        result = analyze_demand_charges(conn, site_id=1, days=30)
        assert "error" in result

    def test_returns_peak_analysis(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_demand_charges(conn, site_id=1, days=7)

        assert result["billing_peak_kw"] > 0
        assert result["monthly_demand_charge"] > 0
        assert result["annual_demand_charge"] == result["monthly_demand_charge"] * 12

    def test_shaving_scenarios(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_demand_charges(conn, site_id=1, days=7)

        scenarios = result["shaving_scenarios"]
        assert len(scenarios) == 4  # 5%, 10%, 15%, 20%

        for s in scenarios:
            assert s["reduced_peak_kw"] < result["billing_peak_kw"]
            assert s["monthly_savings"] > 0
            assert s["annual_savings"] == round(s["monthly_savings"] * 12, 2)

    def test_load_profile(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_demand_charges(conn, site_id=1, days=7)

        profile = result["load_profile"]
        assert len(profile) == 24  # one entry per hour
        for entry in profile:
            assert 0 <= entry["hour"] <= 23
            assert entry["avg_kw"] >= 0

    def test_recommendations_generated(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_demand_charges(conn, site_id=1, days=7)

        recs = result["recommendations"]
        assert len(recs) > 0
        for rec in recs:
            assert "priority" in rec
            assert "title" in rec
            assert "detail" in rec

    def test_peak_events_top_10(self):
        conn = _mock_conn_with_usage(days=7)
        result = analyze_demand_charges(conn, site_id=1, days=7)

        events = result["top_peak_events"]
        assert len(events) <= 10
        # Should be sorted descending
        demands = [e["demand_kw"] for e in events]
        assert demands == sorted(demands, reverse=True)


# ---------------------------------------------------------------------------
# Tests: generate_cost_optimization_report
# ---------------------------------------------------------------------------

class TestGenerateCostOptimizationReport:
    def test_combined_report(self):
        conn = _mock_conn_with_usage(days=7)
        result = generate_cost_optimization_report(conn, site_id=1, days=7)

        assert "tou_analysis" in result
        assert "demand_analysis" in result
        assert "combined_summary" in result

        summary = result["combined_summary"]
        assert summary["total_energy_kwh"] > 0
        assert summary["estimated_monthly_savings_potential"] >= 0
        assert summary["estimated_annual_savings_potential"] == round(
            summary["estimated_monthly_savings_potential"] * 12, 2
        )
