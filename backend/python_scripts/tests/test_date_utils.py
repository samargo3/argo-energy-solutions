"""
Unit tests for lib/date_utils.py

Runs offline — no database or network required.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytz

# Allow imports from the package root
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from lib.date_utils import (
    get_last_complete_week,
    get_baseline_period,
    to_iso_string,
    to_unix_timestamp,
    parse_timestamp,
    get_hour_of_week,
    get_day_and_hour,
    get_interval_hours,
    generate_expected_timestamps,
    format_display_date,
    format_date_range,
)


# ── get_last_complete_week ──────────────────────────────────────

class TestGetLastCompleteWeek:
    def test_returns_monday_to_sunday(self):
        # Wednesday 2026-02-04 → last complete week is Mon 2026-01-26 – Sun 2026-02-01
        ref = datetime(2026, 2, 4, 12, 0, 0)
        result = get_last_complete_week("America/New_York", ref)
        assert result["start"].weekday() == 0   # Monday
        assert result["end"].weekday() == 6      # Sunday

    def test_start_at_midnight(self):
        ref = datetime(2026, 2, 4, 12, 0, 0)
        result = get_last_complete_week("America/New_York", ref)
        assert result["start"].hour == 0
        assert result["start"].minute == 0

    def test_end_at_2359(self):
        ref = datetime(2026, 2, 4, 12, 0, 0)
        result = get_last_complete_week("America/New_York", ref)
        assert result["end"].hour == 23
        assert result["end"].minute == 59


# ── get_baseline_period ─────────────────────────────────────────

class TestGetBaselinePeriod:
    def test_four_weeks_default(self):
        start = datetime(2026, 2, 2, 0, 0, 0)
        result = get_baseline_period(start, 4)
        delta = (result["end"] - result["start"]).days + 1
        assert delta == 28  # 4 weeks

    def test_end_is_day_before_start(self):
        start = datetime(2026, 2, 2, 0, 0, 0)
        result = get_baseline_period(start)
        assert result["end"].date() == (start - timedelta(days=1)).date()


# ── to_iso_string ───────────────────────────────────────────────

class TestToIsoString:
    def test_basic(self):
        dt = datetime(2026, 1, 15, 8, 30, 0)
        iso = to_iso_string(dt)
        assert "2026-01-15" in iso
        assert "08:30" in iso


# ── to_unix_timestamp ───────────────────────────────────────────

class TestToUnixTimestamp:
    def test_epoch(self):
        dt = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert to_unix_timestamp(dt) == 0


# ── parse_timestamp ─────────────────────────────────────────────

class TestParseTimestamp:
    def test_unix_seconds(self):
        result = parse_timestamp(0)
        assert result.year == 1970

    def test_iso_string(self):
        result = parse_timestamp("2026-06-15T12:00:00Z")
        assert result.year == 2026
        assert result.month == 6

    def test_passthrough_datetime(self):
        dt = datetime(2026, 1, 1)
        assert parse_timestamp(dt) is dt


# ── get_hour_of_week ────────────────────────────────────────────

class TestGetHourOfWeek:
    def test_monday_midnight(self):
        dt = datetime(2026, 2, 2, 0, 0, 0)  # Monday
        assert get_hour_of_week(dt) == 0

    def test_sunday_11pm(self):
        dt = datetime(2026, 2, 8, 23, 0, 0)  # Sunday
        assert get_hour_of_week(dt) == 167


# ── get_day_and_hour ────────────────────────────────────────────

class TestGetDayAndHour:
    def test_wednesday_3pm(self):
        dt = datetime(2026, 2, 4, 15, 0, 0)  # Wednesday
        result = get_day_and_hour(dt)
        assert result["dayOfWeek"] == "wednesday"
        assert result["hour"] == 15


# ── get_interval_hours ──────────────────────────────────────────

class TestGetIntervalHours:
    def test_one_hour(self):
        assert get_interval_hours(3600) == 1.0

    def test_fifteen_minutes(self):
        assert get_interval_hours(900) == 0.25


# ── generate_expected_timestamps ─────────────────────────────────

class TestGenerateExpectedTimestamps:
    def test_count(self):
        start = datetime(2026, 1, 1, 0, 0, 0)
        end = datetime(2026, 1, 1, 3, 0, 0)
        result = generate_expected_timestamps(start, end, 3600)
        assert len(result) == 4  # 0:00, 1:00, 2:00, 3:00

    def test_first_and_last(self):
        start = datetime(2026, 1, 1, 0, 0, 0)
        end = datetime(2026, 1, 1, 2, 0, 0)
        result = generate_expected_timestamps(start, end, 3600)
        assert result[0] == start
        assert result[-1] == end


# ── format_display_date ──────────────────────────────────────────

class TestFormatDisplayDate:
    def test_format(self):
        dt = datetime(2026, 1, 15, 7, 0, 0)
        result = format_display_date(dt)
        assert "Jan" in result
        assert "2026" in result
        assert "07:00" in result


# ── format_date_range ────────────────────────────────────────────

class TestFormatDateRange:
    def test_range_string(self):
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 7)
        result = format_date_range(start, end)
        assert "Jan 01, 2026" in result
        assert "Jan 07, 2026" in result
        assert " - " in result
