"""
Configuration for Python analytics
"""

from .report_config import (
    DEFAULT_CONFIG,
    merge_config,
    is_business_hours,
    get_day_of_week,
)

__all__ = [
    'DEFAULT_CONFIG',
    'merge_config',
    'is_business_hours',
    'get_day_of_week',
]
