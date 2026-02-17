"""
Configuration for Python analytics
"""

from .report_config import (
    DEFAULT_CONFIG,
    merge_config,
    is_business_hours,
    get_day_of_week,
    # Data collection constants
    READINGS_PER_DAY_15MIN,
    READINGS_PER_DAY_HOURLY,
    READINGS_PER_WEEK_15MIN,
    # Validation limits
    MAX_POWER_KW,
    VOLTAGE_MIN,
    VOLTAGE_MAX,
    FREQUENCY_MIN_HZ,
    FREQUENCY_MAX_HZ,
    MAX_THD_CURRENT,
    # HTTP & retry defaults
    DEFAULT_API_TIMEOUT,
    LONG_API_TIMEOUT,
    DEFAULT_RETRY_ATTEMPTS,
    # Ingestion health thresholds
    STALE_CRITICAL_HOURS,
    STALE_WARNING_HOURS,
)

__all__ = [
    'DEFAULT_CONFIG',
    'merge_config',
    'is_business_hours',
    'get_day_of_week',
    'READINGS_PER_DAY_15MIN',
    'READINGS_PER_DAY_HOURLY',
    'READINGS_PER_WEEK_15MIN',
    'MAX_POWER_KW',
    'VOLTAGE_MIN',
    'VOLTAGE_MAX',
    'FREQUENCY_MIN_HZ',
    'FREQUENCY_MAX_HZ',
    'MAX_THD_CURRENT',
    'DEFAULT_API_TIMEOUT',
    'LONG_API_TIMEOUT',
    'DEFAULT_RETRY_ATTEMPTS',
    'STALE_CRITICAL_HOURS',
    'STALE_WARNING_HOURS',
]
