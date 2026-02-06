"""
Anomaly Detection Analytics

Detects anomalous energy consumption patterns by comparing
current week's data against historical baseline.

Python conversion of backend/scripts/reports/analytics/anomaly-detection.js
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from lib.stats_utils import calculate_stats, calculate_iqr, z_score, group_by
from lib.date_utils import parse_timestamp, get_hour_of_week, get_interval_hours
from config.report_config import is_business_hours


def build_baseline_profile(baseline_readings: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[int, Dict[str, float]]:
    """
    Build baseline profile by hour-of-week
    
    Args:
        baseline_readings: List of readings for baseline period
        config: Configuration dictionary
        
    Returns:
        Dictionary mapping hour-of-week to statistical profile
    """
    # Group by hour of week (0-167)
    def get_hour_key(reading: Dict[str, Any]) -> int:
        ts = parse_timestamp(reading['ts'])
        return get_hour_of_week(ts)
    
    grouped = group_by(baseline_readings, get_hour_key)
    
    profile = {}
    
    for hour_of_week, readings in grouped.items():
        powers = [
            r.get('P') or r.get('power_kw', 0)
            for r in readings
        ]
        powers = [p for p in powers if p is not None and not (isinstance(p, float) and p != p)]  # Filter None and NaN
        
        if len(powers) > 0:
            stats = calculate_stats(powers)
            iqr = calculate_iqr(powers)
            
            profile[hour_of_week] = {
                **stats,
                **iqr,
                'upperThreshold': iqr['q3'] + (config['anomaly']['iqrMultiplier'] * iqr['iqr']),
            }
    
    return profile


def group_consecutive_anomalies(readings: List[Dict[str, Any]], min_consecutive: int) -> List[Dict[str, Any]]:
    """
    Group consecutive anomalous readings into events
    
    Args:
        readings: List of anomalous readings
        min_consecutive: Minimum consecutive intervals to flag as event
        
    Returns:
        List of anomaly events
    """
    if len(readings) == 0:
        return []
    
    events = []
    current_event = None
    
    for reading in readings:
        if current_event is None:
            # Start new event
            current_event = {
                'start': reading['ts'],
                'end': reading['ts'],
                'readings': [reading],
                'peakPower': reading['power'],
                'totalExcessKwh': reading['excessKwh'],
                'avgExcessKw': reading['excessKw'],
            }
        else:
            # Check if consecutive (within 2 intervals)
            prev_time = parse_timestamp(current_event['end'])
            curr_time = parse_timestamp(reading['ts'])
            gap = (curr_time - prev_time).total_seconds()
            
            if gap < 7200:  # Within 2 hours (allowing for missed intervals)
                # Add to current event
                current_event['end'] = reading['ts']
                current_event['readings'].append(reading)
                current_event['peakPower'] = max(current_event['peakPower'], reading['power'])
                current_event['totalExcessKwh'] += reading['excessKwh']
            else:
                # Save current event and start new one
                if len(current_event['readings']) >= min_consecutive:
                    current_event['avgExcessKw'] = current_event['totalExcessKwh'] / (len(current_event['readings']) * 0.25)
                    current_event['duration'] = f"{len(current_event['readings'])} intervals"
                    current_event['context'] = 'business_hours' if current_event['readings'][0]['isBusinessHours'] else 'after_hours'
                    # Remove 'readings' to reduce output size
                    del current_event['readings']
                    events.append(current_event)
                
                current_event = {
                    'start': reading['ts'],
                    'end': reading['ts'],
                    'readings': [reading],
                    'peakPower': reading['power'],
                    'totalExcessKwh': reading['excessKwh'],
                }
    
    # Save last event
    if current_event and len(current_event['readings']) >= min_consecutive:
        current_event['avgExcessKw'] = current_event['totalExcessKwh'] / (len(current_event['readings']) * 0.25)
        current_event['duration'] = f"{len(current_event['readings'])} intervals"
        current_event['context'] = 'business_hours' if current_event['readings'][0]['isBusinessHours'] else 'after_hours'
        del current_event['readings']
        events.append(current_event)
    
    return events


def detect_anomalies(
    channel_data: Dict[str, Any],
    baseline_data: Dict[str, Any],
    config: Dict[str, Any],
    interval_seconds: int
) -> Dict[str, Any]:
    """
    Detect anomalies in a channel's data
    
    Args:
        channel_data: Dictionary with channelId, channelName, and readings
        baseline_data: Dictionary with baseline readings
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        
    Returns:
        Dictionary with anomaly detection results
    """
    iqr_multiplier = config['anomaly']['iqrMultiplier']
    min_consecutive_intervals = config['anomaly']['minConsecutiveIntervals']
    min_excess_kwh = config['anomaly']['minExcessKwh']
    interval_hours = get_interval_hours(interval_seconds)
    
    # Build baseline profile
    baseline_profile = build_baseline_profile(baseline_data['readings'], config)
    
    # Check each reading against baseline
    anomalous_readings = []
    
    for reading in channel_data['readings']:
        ts = parse_timestamp(reading['ts'])
        hour_of_week = get_hour_of_week(ts)
        baseline = baseline_profile.get(hour_of_week)
        
        if not baseline:
            continue  # No baseline for this hour
        
        power = reading.get('P') or reading.get('power_kw', 0)
        
        # Check if this reading exceeds the threshold
        if power > baseline['upperThreshold']:
            excess_kw = power - baseline['median']
            excess_kwh = excess_kw * interval_hours
            
            anomalous_readings.append({
                'ts': reading['ts'],
                'power': power,
                'baselineMedian': baseline['median'],
                'threshold': baseline['upperThreshold'],
                'excessKw': excess_kw,
                'excessKwh': excess_kwh,
                'zScore': z_score(power, baseline['mean'], baseline['std']),
                'isBusinessHours': is_business_hours(ts, config),
            })
    
    # Group consecutive anomalies into events
    events = group_consecutive_anomalies(anomalous_readings, min_consecutive_intervals)
    
    # Filter by minimum excess kWh
    significant_events = [e for e in events if e['totalExcessKwh'] >= min_excess_kwh]
    
    return {
        'channelId': channel_data['channelId'],
        'channelName': channel_data['channelName'],
        'anomalyCount': len(significant_events),
        'events': significant_events,
    }


def analyze_anomalies(
    channels_data: List[Dict[str, Any]],
    baselines_data: List[Dict[str, Any]],
    config: Dict[str, Any],
    interval_seconds: int
) -> Dict[str, Any]:
    """
    Analyze anomalies for all channels
    
    Args:
        channels_data: List of channel data dictionaries
        baselines_data: List of baseline data dictionaries
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        
    Returns:
        Dictionary with complete anomaly analysis results
    """
    results = []
    
    for channel_data in channels_data:
        # Find matching baseline
        baseline_data = next(
            (b for b in baselines_data if b['channelId'] == channel_data['channelId']),
            None
        )
        
        if not baseline_data or len(baseline_data.get('readings', [])) == 0:
            print(f"Warning: No baseline data for channel {channel_data['channelId']}, skipping anomaly detection")
            continue
        
        result = detect_anomalies(channel_data, baseline_data, config, interval_seconds)
        
        if result['anomalyCount'] > 0:
            results.append(result)
    
    # Sort by total excess kWh across all events
    results.sort(
        key=lambda r: sum(e['totalExcessKwh'] for e in r['events']),
        reverse=True
    )
    
    # Calculate summary statistics
    total_events = sum(r['anomalyCount'] for r in results)
    total_excess_kwh = sum(
        sum(e['totalExcessKwh'] for e in r['events'])
        for r in results
    )
    
    return {
        'channelsWithAnomalies': len(results),
        'totalAnomalyEvents': total_events,
        'totalExcessKwh': round(total_excess_kwh, 2),
        'results': results,
        'timeline': generate_anomaly_timeline(results),
    }


def generate_anomaly_timeline(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate anomaly timeline for visualization
    
    Args:
        results: List of anomaly analysis results
        
    Returns:
        Timeline of anomaly events sorted by time
    """
    timeline = []
    
    for channel_result in results:
        for event in channel_result['events']:
            timeline.append({
                'channelName': channel_result['channelName'],
                'start': event['start'],
                'end': event['end'],
                'peakPower': event['peakPower'],
                'excessKwh': event['totalExcessKwh'],
                'context': event['context'],
            })
    
    # Sort by start time
    timeline.sort(key=lambda e: parse_timestamp(e['start']))
    
    return timeline
