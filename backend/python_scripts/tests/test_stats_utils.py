"""
Unit tests for lib/stats_utils.py

Runs offline — no database or network required.
"""

import sys
from pathlib import Path

# Allow imports from the package root
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from lib.stats_utils import (
    calculate_stats,
    percentile,
    calculate_iqr,
    z_score,
    non_zero_percentile,
    group_by,
    rolling_stats,
    rolling_variance,
    detect_outliers,
    calculate_completeness,
    find_gaps,
)


# ── calculate_stats ──────────────────────────────────────────────

class TestCalculateStats:
    def test_basic_values(self):
        result = calculate_stats([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        assert result["count"] == 10
        assert result["sum"] == 55.0
        assert result["mean"] == 5.5
        assert result["min"] == 1.0
        assert result["max"] == 10.0
        assert result["median"] == 5.5

    def test_empty_list(self):
        result = calculate_stats([])
        assert result["count"] == 0
        assert result["mean"] == 0.0

    def test_none_input(self):
        result = calculate_stats(None)
        assert result["count"] == 0

    def test_single_value(self):
        result = calculate_stats([42.0])
        assert result["count"] == 1
        assert result["mean"] == 42.0
        assert result["std"] == 0.0


# ── percentile ───────────────────────────────────────────────────

class TestPercentile:
    def test_median_is_50th(self):
        assert percentile([1, 2, 3, 4, 5], 50) == 3.0

    def test_empty_returns_zero(self):
        assert percentile([], 50) == 0.0

    def test_25th_and_75th(self):
        vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert percentile(vals, 25) == 3.25
        assert percentile(vals, 75) == 7.75


# ── calculate_iqr ────────────────────────────────────────────────

class TestCalculateIQR:
    def test_basic(self):
        result = calculate_iqr([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        assert result["q1"] == 3.25
        assert result["q3"] == 7.75
        assert result["iqr"] == 4.5

    def test_empty(self):
        result = calculate_iqr([])
        assert result["iqr"] == 0.0


# ── z_score ──────────────────────────────────────────────────────

class TestZScore:
    def test_standard(self):
        assert z_score(10, 5, 2.5) == 2.0

    def test_zero_std(self):
        assert z_score(10, 5, 0) == 0.0

    def test_negative(self):
        assert z_score(0, 5, 2.5) == -2.0


# ── non_zero_percentile ─────────────────────────────────────────

class TestNonZeroPercentile:
    def test_filters_zeros(self):
        vals = [0, 0, 0, 5, 10, 15]
        result = non_zero_percentile(vals, 50)
        assert result == 10.0  # median of [5, 10, 15]

    def test_all_zeros(self):
        assert non_zero_percentile([0, 0, 0], 50) == 0.0


# ── group_by ─────────────────────────────────────────────────────

class TestGroupBy:
    def test_group_by_key(self):
        items = [{"type": "a", "v": 1}, {"type": "b", "v": 2}, {"type": "a", "v": 3}]
        grouped = group_by(items, lambda x: x["type"])
        assert len(grouped["a"]) == 2
        assert len(grouped["b"]) == 1

    def test_empty_list(self):
        assert group_by([], lambda x: x) == {}


# ── rolling_stats ────────────────────────────────────────────────

class TestRollingStats:
    def test_window_size(self):
        vals = [1, 2, 3, 4, 5]
        results = rolling_stats(vals, 3)
        assert len(results) == 3  # 5 - 3 + 1
        assert results[0]["mean"] == 2.0  # avg(1,2,3)
        assert results[0]["index"] == 2


# ── rolling_variance ────────────────────────────────────────────

class TestRollingVariance:
    def test_basic(self):
        vals = [1, 2, 3, 4, 5]
        results = rolling_variance(vals, 3)
        assert len(results) == 3
        assert "variance" in results[0]
        assert "std" in results[0]
        assert results[0]["variance"] >= 0.0


# ── detect_outliers ──────────────────────────────────────────────

class TestDetectOutliers:
    def test_detects_outlier(self):
        vals = [1, 2, 3, 4, 5, 100]
        results = detect_outliers(vals)
        outliers = [r for r in results if r["isOutlier"]]
        assert len(outliers) >= 1
        assert any(r["value"] == 100 for r in outliers)

    def test_no_outliers(self):
        # Values spread enough that IQR gives a meaningful range
        vals = [3, 4, 5, 6, 7, 8, 9]
        results = detect_outliers(vals)
        outliers = [r for r in results if r["isOutlier"]]
        assert len(outliers) == 0


# ── calculate_completeness ──────────────────────────────────────

class TestCalculateCompleteness:
    def test_full(self):
        assert calculate_completeness(100, 100) == 100.0

    def test_half(self):
        assert calculate_completeness(50, 100) == 50.0

    def test_zero_expected(self):
        assert calculate_completeness(10, 0) == 0.0


# ── find_gaps ────────────────────────────────────────────────────

class TestFindGaps:
    def test_gap_detected(self):
        from datetime import datetime, timedelta, timezone

        t1 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        t2 = t1 + timedelta(hours=1)
        t3 = t2 + timedelta(hours=3)  # 2-hour gap (expected 1h)

        gaps = find_gaps([t1, t2, t3], 3600)
        assert len(gaps) == 1
        assert gaps[0]["missingIntervals"] == 2

    def test_no_gap(self):
        from datetime import datetime, timedelta, timezone

        t1 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        t2 = t1 + timedelta(hours=1)
        t3 = t2 + timedelta(hours=1)

        gaps = find_gaps([t1, t2, t3], 3600)
        assert len(gaps) == 0

    def test_iso_string_timestamps(self):
        gaps = find_gaps(
            ["2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z", "2026-01-01T04:00:00Z"],
            3600,
        )
        assert len(gaps) == 1
