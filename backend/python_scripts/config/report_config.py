"""
Weekly Report Configuration

Central configuration for the Weekly Exceptions & Opportunities Brief
Python conversion of backend/scripts/reports/config/report-config.js
"""

from datetime import datetime
from typing import Dict, Any, Optional


# Default configuration
DEFAULT_CONFIG = {
    # Timezone for report calculations
    'timezone': 'America/New_York',
    
    # Business hours schedule (24-hour format)
    'businessHours': {
        'monday': {'start': 7, 'end': 18},
        'tuesday': {'start': 7, 'end': 18},
        'wednesday': {'start': 7, 'end': 18},
        'thursday': {'start': 7, 'end': 18},
        'friday': {'start': 7, 'end': 18},
        'saturday': None,  # None means all day after-hours
        'sunday': None,
    },
    
    # Data resolution preferences (in seconds)
    'intervalPreferences': [900, 1800, 3600],  # 15min, 30min, 60min
    
    # Baseline calculation parameters
    'baseline': {
        'weeksCount': 4,  # Number of weeks to use for baseline
        'minCompleteness': 70,  # Minimum data completeness required (%)
    },
    
    # Sensor/communications issue detection thresholds
    'sensorHealth': {
        'gapMultiplier': 2,  # Gap detection: missing data threshold
        'staleHours': 2,  # Stale meter: hours since last data
        'missingThresholdPct': 10,  # Missing data threshold (%)
        'flatlineHours': 6,  # Flatline detection: hours with near-zero variance
        'flatlineVarianceThreshold': 0.01,  # Variance threshold for flatline (kW)
    },
    
    # After-hours waste detection
    'afterHours': {
        'baselinePercentile': 5,  # Percentile for baseline after-hours load
        'minPowerThreshold': 0.1,  # Minimum kW to exclude from analysis
        'minExcessKwh': 10,  # Minimum excess kWh to flag as significant
    },
    
    # Anomaly detection parameters
    'anomaly': {
        'iqrMultiplier': 3,  # Statistical threshold: median + (IQR * multiplier)
        'zScoreThreshold': 3,  # Z-score threshold (alternative method)
        'minConsecutiveIntervals': 3,  # Minimum consecutive intervals to flag
        'minExcessKwh': 5,  # Minimum excess kWh to report
    },
    
    # Spike detection parameters
    'spike': {
        'baselinePercentile': 95,  # Percentile for "normal" baseline
        'multiplier': 1.5,  # Multiplier above baseline to flag spike
        'submeterMinKw': 5,  # Absolute minimum threshold for submeters (kW)
        'siteMinKw': 20,  # Absolute minimum threshold for site total (kW)
        'minDuration': 1,  # Minimum duration (intervals) to report
    },
    
    # Quick wins generation
    'quickWins': {
        'maxCount': 10,  # Maximum number of recommendations
        'minWeeklyImpact': 10,  # Minimum weekly kWh impact to suggest
    },
    
    # Energy cost ($/kWh) - optional, for $ calculations
    'tariff': {
        'defaultRate': 0.12,  # $0.12/kWh default
        'demandCharge': None,  # $/kW if applicable
    },
    
    # Report output options
    'output': {
        'includeCharts': True,
        'includeRawData': False,
        'precision': 2,  # decimal places for numbers
    },
}


def merge_config(user_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge user config with defaults
    
    Args:
        user_config: User-provided configuration overrides
        
    Returns:
        Merged configuration dictionary
    """
    if user_config is None:
        user_config = {}
    
    config = DEFAULT_CONFIG.copy()
    
    # Merge top-level keys
    for key, value in user_config.items():
        if key in config and isinstance(config[key], dict) and isinstance(value, dict):
            # Deep merge for nested dictionaries
            config[key] = {**config[key], **value}
        else:
            config[key] = value
    
    return config


def is_business_hours(date: datetime, config: Dict[str, Any] = None) -> bool:
    """
    Check if a timestamp is during business hours
    
    Args:
        date: Datetime object to check
        config: Configuration dictionary (uses DEFAULT_CONFIG if None)
        
    Returns:
        True if during business hours, False otherwise
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_name = day_names[date.weekday()]
    hours = config['businessHours'][day_name]
    
    if hours is None:
        return False  # None means all day after-hours
    
    hour = date.hour
    return hours['start'] <= hour < hours['end']


def get_day_of_week(date: datetime) -> str:
    """
    Get the day of week name from a date
    
    Args:
        date: Datetime object
        
    Returns:
        Day of week name (lowercase)
    """
    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return day_names[date.weekday()]
