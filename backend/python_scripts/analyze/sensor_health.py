"""
Sensor & Communications Health Analytics

Detects data quality issues:
- Missing data gaps
- Stale meters (no recent data)
- Flatlined sensors
- Low data completeness

Python conversion of backend/scripts/reports/analytics/sensor-health.js
"""

from typing import List, Dict, Any
from datetime import datetime
from lib.stats_utils import find_gaps, calculate_completeness, rolling_variance
from lib.date_utils import parse_timestamp


def analyze_sensor_health(
    channel_data: Dict[str, Any],
    config: Dict[str, Any],
    interval_seconds: int
) -> List[Dict[str, Any]]:
    """
    Analyze sensor health for a channel's data
    
    Args:
        channel_data: Dictionary with channelId, channelName, and readings
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        
    Returns:
        List of health issues found
    """
    sensor_config = config['sensorHealth']
    gap_multiplier = sensor_config['gapMultiplier']
    missing_threshold_pct = sensor_config['missingThresholdPct']
    flatline_hours = sensor_config['flatlineHours']
    flatline_variance_threshold = sensor_config['flatlineVarianceThreshold']
    
    issues = []
    channel_id = channel_data['channelId']
    channel_name = channel_data['channelName']
    
    # 1. Detect missing data gaps
    gaps = find_gaps(
        [r['ts'] for r in channel_data['readings']],
        interval_seconds
    )
    
    for gap in gaps:
        if gap['missingIntervals'] >= gap_multiplier:
            issues.append({
                'type': 'missing_data',
                'severity': 'high' if gap['missingIntervals'] > 10 else 'medium',
                'channelId': channel_id,
                'channelName': channel_name,
                'start': gap['start'],
                'end': gap['end'],
                'missingIntervals': gap['missingIntervals'],
                'duration': f"{gap['actualInterval'] / 3600:.1f} hours",
                'description': f"Missing {gap['missingIntervals']} intervals ({gap['actualInterval'] / 3600:.1f}h gap)",
            })
    
    # 2. Check overall data completeness
    expected_intervals = channel_data.get('expectedIntervals', len(channel_data['readings']))
    actual_intervals = len(channel_data['readings'])
    completeness = calculate_completeness(actual_intervals, expected_intervals)
    
    if completeness < (100 - missing_threshold_pct):
        issues.append({
            'type': 'low_completeness',
            'severity': 'high' if completeness < 50 else 'medium',
            'channelId': channel_id,
            'channelName': channel_name,
            'completeness': f"{completeness:.1f}%",
            'missingCount': expected_intervals - actual_intervals,
            'description': f"Only {completeness:.1f}% data completeness (missing {expected_intervals - actual_intervals} intervals)",
        })
    
    # 3. Detect flatlined sensors
    power_readings = [
        r.get('P') or r.get('power_kw', 0)
        for r in channel_data['readings']
    ]
    power_readings = [p for p in power_readings if p is not None and not (isinstance(p, float) and p != p)]  # Filter None and NaN
    
    if len(power_readings) > 0:
        flatline_window = int((flatline_hours * 3600) / interval_seconds)
        
        if len(power_readings) >= flatline_window:
            rolling = rolling_variance(power_readings, flatline_window)
            
            for stat in rolling:
                if stat['variance'] < flatline_variance_threshold and stat['mean'] > 0.1:
                    # Flatline detected (low variance but non-zero mean)
                    start_idx = stat['index'] - flatline_window + 1
                    end_idx = stat['index']
                    
                    issues.append({
                        'type': 'flatline',
                        'severity': 'medium',
                        'channelId': channel_id,
                        'channelName': channel_name,
                        'start': channel_data['readings'][start_idx]['ts'] if start_idx < len(channel_data['readings']) else None,
                        'end': channel_data['readings'][end_idx]['ts'] if end_idx < len(channel_data['readings']) else None,
                        'meanPower': f"{stat['mean']:.2f} kW",
                        'variance': f"{stat['variance']:.4f}",
                        'description': f"Flatlined at {stat['mean']:.2f} kW for {flatline_hours}+ hours (possible stuck sensor)",
                    })
                    
                    # Only report first flatline to avoid spam
                    break
    
    # 4. Check for stale data (last reading is old)
    if len(channel_data['readings']) > 0:
        last_reading = channel_data['readings'][-1]
        last_time = parse_timestamp(last_reading['ts'])
        now = datetime.now(tz=last_time.tzinfo)
        hours_since_last_reading = (now - last_time).total_seconds() / 3600
        
        if hours_since_last_reading > sensor_config['staleHours']:
            issues.append({
                'type': 'stale_data',
                'severity': 'high' if hours_since_last_reading > 24 else 'low',
                'channelId': channel_id,
                'channelName': channel_name,
                'lastReading': last_reading['ts'],
                'hoursSince': f"{hours_since_last_reading:.1f}",
                'description': f"No data for {hours_since_last_reading:.1f} hours (last: {last_time.strftime('%Y-%m-%d %H:%M:%S')})",
                'source': 'inferred_from_timestamps',
            })
    
    return issues


def analyze_sensor_health_for_site(
    channels_data: List[Dict[str, Any]],
    config: Dict[str, Any],
    interval_seconds: int
) -> Dict[str, Any]:
    """
    Analyze sensor health for all channels
    
    Args:
        channels_data: List of channel data dictionaries
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        
    Returns:
        Dictionary with complete sensor health analysis
    """
    all_issues = []
    
    for channel_data in channels_data:
        issues = analyze_sensor_health(channel_data, config, interval_seconds)
        all_issues.extend(issues)
    
    # Sort by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    all_issues.sort(key=lambda i: severity_order[i['severity']])
    
    return {
        'totalIssues': len(all_issues),
        'highSeverity': len([i for i in all_issues if i['severity'] == 'high']),
        'mediumSeverity': len([i for i in all_issues if i['severity'] == 'medium']),
        'lowSeverity': len([i for i in all_issues if i['severity'] == 'low']),
        'issues': all_issues,
        'summary': generate_health_summary(all_issues),
    }


def generate_health_summary(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate a summary of health issues
    
    Args:
        issues: List of health issues
        
    Returns:
        List of summary items by issue type
    """
    by_type = {}
    
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in by_type:
            by_type[issue_type] = {
                'count': 0,
                'channels': set(),
            }
        by_type[issue_type]['count'] += 1
        by_type[issue_type]['channels'].add(issue['channelName'])
    
    summary = []
    
    for issue_type, data in by_type.items():
        channel_list = ', '.join(list(data['channels'])[:3])
        more_text = f" and {len(data['channels']) - 3} more" if len(data['channels']) > 3 else ''
        
        summary.append({
            'type': issue_type,
            'count': data['count'],
            'affectedChannels': len(data['channels']),
            'description': f"{data['count']} {issue_type} issue(s) affecting {len(data['channels'])} channel(s): {channel_list}{more_text}",
        })
    
    return summary
