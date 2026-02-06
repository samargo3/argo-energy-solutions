"""
Utility libraries for Python analytics
"""

from .stats_utils import (
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
    aggregate_by_period,
)

from .date_utils import (
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

__all__ = [
    # stats_utils
    'calculate_stats',
    'percentile',
    'calculate_iqr',
    'z_score',
    'non_zero_percentile',
    'group_by',
    'rolling_stats',
    'rolling_variance',
    'detect_outliers',
    'calculate_completeness',
    'find_gaps',
    'aggregate_by_period',
    # date_utils
    'get_last_complete_week',
    'get_baseline_period',
    'to_iso_string',
    'to_unix_timestamp',
    'parse_timestamp',
    'get_hour_of_week',
    'get_day_and_hour',
    'get_interval_hours',
    'generate_expected_timestamps',
    'format_display_date',
    'format_date_range',
]
