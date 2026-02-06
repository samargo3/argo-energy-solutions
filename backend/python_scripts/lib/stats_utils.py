"""
Statistical utility functions for analytics

Python conversion of backend/scripts/reports/lib/stats-utils.js
Uses numpy and scipy for efficient statistical calculations.
"""

import numpy as np
from scipy import stats as scipy_stats
from typing import List, Dict, Any, Callable, Optional


def calculate_stats(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for an array of numbers
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with count, sum, mean, min, max, median, std
    """
    if not values or len(values) == 0:
        return {
            'count': 0,
            'sum': 0.0,
            'mean': 0.0,
            'min': 0.0,
            'max': 0.0,
            'median': 0.0,
            'std': 0.0,
        }
    
    arr = np.array(values)
    
    return {
        'count': len(values),
        'sum': float(np.sum(arr)),
        'mean': float(np.mean(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr)),
        'median': float(np.median(arr)),
        'std': float(np.std(arr)),
    }


def percentile(values: List[float], p: float) -> float:
    """
    Calculate percentile of an array
    
    Args:
        values: List of numeric values
        p: Percentile (0-100)
        
    Returns:
        Percentile value
    """
    if not values or len(values) == 0:
        return 0.0
    
    return float(np.percentile(values, p))


def calculate_iqr(values: List[float]) -> Dict[str, float]:
    """
    Calculate interquartile range (IQR)
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with q1, q3, and iqr
    """
    if not values or len(values) == 0:
        return {'q1': 0.0, 'q3': 0.0, 'iqr': 0.0}
    
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    
    return {
        'q1': q1,
        'q3': q3,
        'iqr': q3 - q1,
    }


def z_score(value: float, mean: float, std: float) -> float:
    """
    Calculate z-score for a value
    
    Args:
        value: The value to calculate z-score for
        mean: Mean of the distribution
        std: Standard deviation of the distribution
        
    Returns:
        Z-score
    """
    if std == 0:
        return 0.0
    return (value - mean) / std


def non_zero_percentile(values: List[float], p: float) -> float:
    """
    Filter out zeros and calculate percentile of non-zero values
    
    Args:
        values: List of numeric values
        p: Percentile (0-100)
        
    Returns:
        Percentile value of non-zero values
    """
    non_zero = [v for v in values if v > 0]
    return percentile(non_zero, p)


def group_by(array: List[Any], key_fn: Callable) -> Dict[Any, List[Any]]:
    """
    Group values by a key function
    
    Args:
        array: List of items to group
        key_fn: Function that returns the grouping key for each item
        
    Returns:
        Dictionary mapping keys to lists of items
    """
    result = {}
    for item in array:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def rolling_stats(values: List[float], window_size: int) -> List[Dict[str, Any]]:
    """
    Calculate rolling statistics over a window
    
    Args:
        values: List of numeric values
        window_size: Size of the rolling window
        
    Returns:
        List of dictionaries with rolling statistics
    """
    results = []
    
    for i in range(window_size - 1, len(values)):
        window = values[i - window_size + 1:i + 1]
        stats = calculate_stats(window)
        stats['index'] = i
        results.append(stats)
    
    return results


def rolling_variance(values: List[float], window_size: int) -> List[Dict[str, float]]:
    """
    Calculate rolling variance over a window
    
    Args:
        values: List of numeric values
        window_size: Size of the rolling window
        
    Returns:
        List of dictionaries with rolling variance, std, and mean
    """
    results = []
    
    for i in range(window_size - 1, len(values)):
        window = values[i - window_size + 1:i + 1]
        stats = calculate_stats(window)
        results.append({
            'index': i,
            'variance': stats['std'] ** 2,
            'std': stats['std'],
            'mean': stats['mean'],
        })
    
    return results


def detect_outliers(values: List[float], multiplier: float = 1.5) -> List[Dict[str, Any]]:
    """
    Detect outliers using IQR method
    
    Args:
        values: List of numeric values
        multiplier: IQR multiplier for outlier bounds (default 1.5)
        
    Returns:
        List of dictionaries with value, index, isOutlier, and bounds
    """
    iqr_stats = calculate_iqr(values)
    q1, q3, iqr = iqr_stats['q1'], iqr_stats['q3'], iqr_stats['iqr']
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    return [
        {
            'value': value,
            'index': index,
            'isOutlier': value < lower_bound or value > upper_bound,
            'lowerBound': lower_bound,
            'upperBound': upper_bound,
        }
        for index, value in enumerate(values)
    ]


def calculate_completeness(actual_count: int, expected_count: int) -> float:
    """
    Calculate completeness percentage
    
    Args:
        actual_count: Actual number of data points
        expected_count: Expected number of data points
        
    Returns:
        Completeness percentage (0-100)
    """
    if expected_count == 0:
        return 0.0
    return (actual_count / expected_count) * 100


def find_gaps(timestamps: List[Any], expected_interval_seconds: int) -> List[Dict[str, Any]]:
    """
    Find gaps in a time series
    
    Args:
        timestamps: List of timestamps (datetime objects or parseable strings)
        expected_interval_seconds: Expected interval between readings in seconds
        
    Returns:
        List of gap dictionaries with start, end, and missing intervals
    """
    from datetime import datetime
    gaps = []
    
    for i in range(1, len(timestamps)):
        prev_time = timestamps[i - 1]
        curr_time = timestamps[i]
        
        # Convert to datetime if needed
        if isinstance(prev_time, str):
            prev_time = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
        if isinstance(curr_time, str):
            curr_time = datetime.fromisoformat(curr_time.replace('Z', '+00:00'))
        
        actual_interval = (curr_time - prev_time).total_seconds()
        
        # Allow 10% tolerance
        if actual_interval > expected_interval_seconds * 1.1:
            gaps.append({
                'start': timestamps[i - 1],
                'end': timestamps[i],
                'expectedIntervals': round(actual_interval / expected_interval_seconds),
                'actualInterval': actual_interval,
                'missingIntervals': round(actual_interval / expected_interval_seconds) - 1,
            })
    
    return gaps


def aggregate_by_period(
    data_points: List[Any],
    period_fn: Callable,
    value_fn: Callable
) -> Dict[Any, Dict[str, float]]:
    """
    Aggregate values by time period (hour of day, day of week, etc.)
    
    Args:
        data_points: List of data points
        period_fn: Function that returns the period key for each data point
        value_fn: Function that extracts the value from each data point
        
    Returns:
        Dictionary mapping periods to statistics
    """
    grouped = group_by(data_points, period_fn)
    
    result = {}
    for period, points in grouped.items():
        values = [value_fn(p) for p in points if value_fn(p) is not None]
        result[period] = calculate_stats(values)
    
    return result
