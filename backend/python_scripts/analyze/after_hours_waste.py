"""
After-Hours Energy Waste Analytics

Identifies energy consumption during non-business hours that exceeds
the expected baseline, indicating potential waste or optimization opportunities.

Python conversion of backend/scripts/reports/analytics/after-hours-waste.js
"""

from typing import List, Dict, Any
from lib.stats_utils import non_zero_percentile, calculate_stats
from lib.date_utils import parse_timestamp, get_interval_hours
from config.report_config import is_business_hours


def calculate_after_hours_waste(
    channel_data: Dict[str, Any],
    baseline_data: List[Dict[str, Any]],
    config: Dict[str, Any],
    interval_seconds: int
) -> Dict[str, Any]:
    """
    Calculate after-hours waste for a channel
    
    Args:
        channel_data: Dictionary with channelId, channelName, and readings
        baseline_data: List of baseline readings
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        
    Returns:
        Dictionary with after-hours waste analysis
    """
    baseline_percentile = config['afterHours']['baselinePercentile']
    min_power_threshold = config['afterHours']['minPowerThreshold']
    min_excess_kwh = config['afterHours']['minExcessKwh']
    interval_hours = get_interval_hours(interval_seconds)
    
    # 1. Calculate baseline after-hours power (5th percentile of after-hours periods)
    baseline_after_hours_power = [
        reading.get('P') or reading.get('power_kw', 0)
        for reading in baseline_data
        if not is_business_hours(parse_timestamp(reading['ts']), config)
        and (reading.get('P') or reading.get('power_kw', 0)) > min_power_threshold
    ]
    
    baseline_kw = non_zero_percentile(baseline_after_hours_power, baseline_percentile)
    
    # 2. Calculate this week's after-hours consumption
    report_after_hours_readings = [
        {
            'ts': reading['ts'],
            'power': reading.get('P') or reading.get('power_kw', 0),
        }
        for reading in channel_data['readings']
        if not is_business_hours(parse_timestamp(reading['ts']), config)
    ]
    
    total_after_hours_kwh = 0.0
    excess_after_hours_kwh = 0.0
    excess_intervals = []
    
    for reading in report_after_hours_readings:
        kwh = reading['power'] * interval_hours
        total_after_hours_kwh += kwh
        
        excess = max(0, reading['power'] - baseline_kw)
        excess_kwh = excess * interval_hours
        excess_after_hours_kwh += excess_kwh
        
        if excess > min_power_threshold:
            excess_intervals.append({
                'ts': reading['ts'],
                'power': reading['power'],
                'baselinePower': baseline_kw,
                'excessKw': excess,
                'excessKwh': excess_kwh,
            })
    
    # 3. Calculate statistics
    after_hours_powers = [r['power'] for r in report_after_hours_readings]
    stats = calculate_stats(after_hours_powers)
    
    return {
        'channelId': channel_data['channelId'],
        'channelName': channel_data['channelName'],
        'baseline': {
            'kw': round(baseline_kw, 2),
            'source': f"{baseline_percentile}th percentile of after-hours baseline",
        },
        'thisWeek': {
            'totalAfterHoursKwh': round(total_after_hours_kwh, 2),
            'excessAfterHoursKwh': round(excess_after_hours_kwh, 2),
            'avgPowerKw': round(stats['mean'], 2),
            'maxPowerKw': round(stats['max'], 2),
            'minPowerKw': round(stats['min'], 2),
            'intervals': len(report_after_hours_readings),
        },
        'impact': {
            'excessKwh': round(excess_after_hours_kwh, 2),
            'excessCost': round(excess_after_hours_kwh * config['tariff']['defaultRate'], 2),
            'percentOfTotal': round(excess_after_hours_kwh / total_after_hours_kwh * 100, 1) if total_after_hours_kwh > 0 else 0,
        },
        'excessIntervals': excess_intervals[:10],  # Top 10 for details
        'isSignificant': excess_after_hours_kwh >= min_excess_kwh,
    }


def analyze_after_hours_waste(
    channels_data: List[Dict[str, Any]],
    baselines_data: List[Dict[str, Any]],
    config: Dict[str, Any],
    interval_seconds: int
) -> Dict[str, Any]:
    """
    Analyze after-hours waste for all channels
    
    Args:
        channels_data: List of channel data dictionaries
        baselines_data: List of baseline data dictionaries
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        
    Returns:
        Dictionary with complete after-hours waste analysis
    """
    results = []
    
    for channel_data in channels_data:
        baseline_data = next(
            (b for b in baselines_data if b['channelId'] == channel_data['channelId']),
            None
        )
        
        if not baseline_data or len(baseline_data.get('readings', [])) == 0:
            print(f"Warning: No baseline data for channel {channel_data['channelId']}, skipping after-hours analysis")
            continue
        
        result = calculate_after_hours_waste(channel_data, baseline_data['readings'], config, interval_seconds)
        
        if result['isSignificant']:
            results.append(result)
    
    # Sort by excess kWh (highest first)
    results.sort(key=lambda r: r['impact']['excessKwh'], reverse=True)
    
    # Calculate totals
    total_excess_kwh = sum(r['impact']['excessKwh'] for r in results)
    total_excess_cost = sum(r['impact']['excessCost'] for r in results)
    
    return {
        'topMeters': results[:10],  # Top 10 contributors
        'allMeters': results,
        'summary': {
            'totalMetersWithExcess': len(results),
            'totalExcessKwh': round(total_excess_kwh, 2),
            'totalExcessCost': round(total_excess_cost, 2),
            'estimatedAnnualCost': round(total_excess_cost * 52, 2),
        },
        'charts': {
            'topContributorsChart': [
                {
                    'name': r['channelName'],
                    'excessKwh': r['impact']['excessKwh'],
                    'cost': r['impact']['excessCost'],
                }
                for r in results[:10]
            ],
            'afterHoursProfile': generate_after_hours_profile(results),
        },
    }


def generate_after_hours_profile(results: List[Dict[str, Any]]) -> List[Dict[str, float]]:
    """
    Generate after-hours load profile by hour of day
    
    Args:
        results: List of after-hours analysis results
        
    Returns:
        List of hourly profile data
    """
    profile = []
    
    # Aggregate by hour (simplified - would need actual timestamp grouping for real implementation)
    for hour in range(24):
        total_kw = sum(r['thisWeek'].get('avgPowerKw', 0) for r in results)
        
        profile.append({
            'hour': hour,
            'avgPowerKw': round(total_kw / max(1, len(results)), 2),
        })
    
    return profile
