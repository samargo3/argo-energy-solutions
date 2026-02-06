"""
Date utility functions for weekly report generation

Python conversion of backend/scripts/reports/lib/date-utils.js
Uses pytz for timezone handling and datetime for date operations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union
import pytz


def get_last_complete_week(
    timezone: str = 'America/New_York',
    reference_date: datetime = None
) -> Dict[str, datetime]:
    """
    Get the last complete week (Monday 00:00 to Sunday 23:59) in a given timezone
    
    Args:
        timezone: IANA timezone (e.g., 'America/New_York')
        reference_date: Optional reference date (defaults to now)
        
    Returns:
        Dictionary with 'start' and 'end' datetime objects
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    # Convert to target timezone
    tz = pytz.timezone(timezone)
    now = reference_date.astimezone(tz) if reference_date.tzinfo else tz.localize(reference_date)
    
    # Find the most recent Monday 00:00
    day_of_week = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Go back to last Monday of the previous week
    days_to_last_monday = day_of_week + 7
    last_monday = now - timedelta(days=days_to_last_monday)
    last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Last Sunday 23:59:59
    last_sunday = last_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return {
        'start': last_monday,
        'end': last_sunday,
    }


def get_baseline_period(
    report_start: datetime,
    weeks_count: int = 4
) -> Dict[str, datetime]:
    """
    Get the baseline period (N weeks before the report week)
    
    Args:
        report_start: Start of report week
        weeks_count: Number of weeks for baseline
        
    Returns:
        Dictionary with 'start' and 'end' datetime objects
    """
    # Day before report week starts
    baseline_end = report_start - timedelta(days=1)
    baseline_end = baseline_end.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # N weeks before baseline end
    baseline_start = baseline_end - timedelta(days=weeks_count * 7 - 1)
    baseline_start = baseline_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return {
        'start': baseline_start,
        'end': baseline_end,
    }


def to_iso_string(date: datetime) -> str:
    """
    Format date as ISO string for API calls
    
    Args:
        date: Datetime object
        
    Returns:
        ISO formatted string
    """
    return date.isoformat()


def to_unix_timestamp(date: datetime) -> int:
    """
    Format date as Unix timestamp (seconds)
    
    Args:
        date: Datetime object
        
    Returns:
        Unix timestamp in seconds
    """
    return int(date.timestamp())


def parse_timestamp(ts: Union[int, float, str, datetime]) -> datetime:
    """
    Parse timestamp (handles both Unix seconds and ISO strings)
    
    Args:
        ts: Timestamp as Unix seconds, ISO string, or datetime
        
    Returns:
        Datetime object
    """
    if isinstance(ts, datetime):
        return ts
    elif isinstance(ts, (int, float)):
        # Assume Unix seconds
        return datetime.fromtimestamp(ts, tz=pytz.UTC)
    else:
        # Try parsing as ISO string
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00'))


def get_hour_of_week(date: datetime) -> int:
    """
    Get hour of week (0-167) from a date
    Monday 00:00 = 0, Sunday 23:00 = 167
    
    Args:
        date: Datetime object
        
    Returns:
        Hour of week (0-167)
    """
    day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
    hour = date.hour
    return day_of_week * 24 + hour


def get_day_and_hour(date: datetime) -> Dict[str, Union[str, int]]:
    """
    Get day of week and hour from a date
    
    Args:
        date: Datetime object
        
    Returns:
        Dictionary with 'dayOfWeek' (name) and 'hour'
    """
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return {
        'dayOfWeek': day_names[date.weekday()],
        'hour': date.hour,
    }


def get_interval_hours(resolution: int) -> float:
    """
    Calculate interval duration in hours
    
    Args:
        resolution: Resolution in seconds (900, 1800, 3600, etc.)
        
    Returns:
        Interval duration in hours
    """
    return resolution / 3600


def generate_expected_timestamps(
    start: datetime,
    end: datetime,
    interval_seconds: int
) -> List[datetime]:
    """
    Generate an array of expected timestamps for a period
    
    Args:
        start: Start datetime
        end: End datetime
        interval_seconds: Interval in seconds
        
    Returns:
        List of expected timestamps
    """
    timestamps = []
    current = start
    
    while current <= end:
        timestamps.append(current)
        current = current + timedelta(seconds=interval_seconds)
    
    return timestamps


def format_display_date(date: datetime) -> str:
    """
    Format date for display (e.g., "Mon Jan 15, 2026 07:00")
    
    Args:
        date: Datetime object
        
    Returns:
        Formatted date string
    """
    return date.strftime('%a %b %d, %Y %H:%M')


def format_date_range(start: datetime, end: datetime) -> str:
    """
    Format date range for display
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        Formatted date range string
    """
    start_str = start.strftime('%b %d, %Y')
    end_str = end.strftime('%b %d, %Y')
    return f"{start_str} - {end_str}"
