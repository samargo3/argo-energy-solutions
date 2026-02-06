"""
Spike Detection Analytics

Identifies unusual power spikes that exceed normal operating levels

Python conversion of backend/scripts/reports/analytics/spike-detection.js
"""

from typing import List, Dict, Any, Optional
from ..lib.stats_utils import percentile, group_by
from ..lib.date_utils import parse_timestamp, get_hour_of_week, get_interval_hours


def build_spike_baseline(baseline_readings: List[Dict[str, Any]]) -> Dict[int, Dict[str, float]]:
    """
    Build baseline for spike detection (95th percentile by hour of week)
    
    Args:
        baseline_readings: List of baseline readings
        
    Returns:
        Dictionary mapping hour-of-week to baseline statistics
    """
    def get_hour_key(reading: Dict[str, Any]) -> int:
        ts = parse_timestamp(reading['ts'])
        return get_hour_of_week(ts)
    
    grouped = group_by(baseline_readings, get_hour_key)
    
    baseline = {}
    
    for hour_of_week, readings in grouped.items():
        powers = [
            r.get('P') or r.get('power_kw', 0)
            for r in readings
        ]
        powers = [p for p in powers if p is not None and not (isinstance(p, float) and p != p)]  # Filter None and NaN
        
        if len(powers) > 0:
            baseline[hour_of_week] = {
                'p95': percentile(powers, 95),
                'p50': percentile(powers, 50),
                'count': len(powers),
            }
    
    return baseline


def group_consecutive_spikes(spikes: List[Dict[str, Any]], interval_seconds: int) -> List[Dict[str, Any]]:
    """
    Group consecutive spike readings into events
    
    Args:
        spikes: List of spike readings
        interval_seconds: Interval resolution in seconds
        
    Returns:
        List of spike events
    """
    if len(spikes) == 0:
        return []
    
    events = []
    current_event = None
    
    for spike in spikes:
        if current_event is None:
            current_event = {
                'start': spike['ts'],
                'end': spike['ts'],
                'peakPower': spike['power'],
                'totalExcessKwh': spike['excessKwh'],
                'intervals': 1,
            }
        else:
            prev_time = parse_timestamp(current_event['end'])
            curr_time = parse_timestamp(spike['ts'])
            gap = (curr_time - prev_time).total_seconds()
            
            # Check if consecutive (within 2 intervals)
            if gap <= interval_seconds * 2:
                current_event['end'] = spike['ts']
                current_event['peakPower'] = max(current_event['peakPower'], spike['power'])
                current_event['totalExcessKwh'] += spike['excessKwh']
                current_event['intervals'] += 1
            else:
                # Save current and start new
                events.append({
                    **current_event,
                    'duration': f"{current_event['intervals']} intervals",
                })
                
                current_event = {
                    'start': spike['ts'],
                    'end': spike['ts'],
                    'peakPower': spike['power'],
                    'totalExcessKwh': spike['excessKwh'],
                    'intervals': 1,
                }
    
    # Save last event
    if current_event:
        events.append({
            **current_event,
            'duration': f"{current_event['intervals']} intervals",
        })
    
    return events


def detect_spikes(
    channel_data: Dict[str, Any],
    baseline_data: Dict[str, Any],
    config: Dict[str, Any],
    interval_seconds: int,
    is_site_total: bool = False
) -> Dict[str, Any]:
    """
    Detect spikes in a channel's data
    
    Args:
        channel_data: Dictionary with channelId, channelName, and readings
        baseline_data: Dictionary with baseline readings
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        is_site_total: Whether this is the site total channel
        
    Returns:
        Dictionary with spike detection results
    """
    spike_config = config['spike']
    min_absolute_kw = spike_config['siteMinKw'] if is_site_total else spike_config['submeterMinKw']
    multiplier = spike_config['multiplier']
    min_duration = spike_config['minDuration']
    interval_hours = get_interval_hours(interval_seconds)
    
    # Build baseline
    baseline = build_spike_baseline(baseline_data['readings'])
    
    # Detect spikes
    spikes = []
    
    for reading in channel_data['readings']:
        ts = parse_timestamp(reading['ts'])
        hour_of_week = get_hour_of_week(ts)
        baseline_stats = baseline.get(hour_of_week)
        
        if not baseline_stats:
            continue
        
        power = reading.get('P') or reading.get('power_kw', 0)
        threshold = max(baseline_stats['p95'] * multiplier, min_absolute_kw)
        
        if power > threshold and power > min_absolute_kw:
            spikes.append({
                'ts': reading['ts'],
                'power': power,
                'baselineP95': baseline_stats['p95'],
                'threshold': threshold,
                'excessKw': power - baseline_stats['p95'],
                'excessKwh': (power - baseline_stats['p95']) * interval_hours,
            })
    
    # Group adjacent spikes into events
    events = group_consecutive_spikes(spikes, interval_seconds)
    
    # Filter by minimum duration
    significant_events = [e for e in events if e['intervals'] >= min_duration]
    
    return {
        'channelId': channel_data['channelId'],
        'channelName': channel_data['channelName'],
        'spikeCount': len(significant_events),
        'events': significant_events,
    }


def analyze_spikes(
    channels_data: List[Dict[str, Any]],
    baselines_data: List[Dict[str, Any]],
    config: Dict[str, Any],
    interval_seconds: int,
    site_channel_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Analyze spikes for all channels
    
    Args:
        channels_data: List of channel data dictionaries
        baselines_data: List of baseline data dictionaries
        config: Configuration dictionary
        interval_seconds: Interval resolution in seconds
        site_channel_id: Channel ID of the site total (optional)
        
    Returns:
        Dictionary with complete spike analysis
    """
    results = []
    
    for channel_data in channels_data:
        baseline_data = next(
            (b for b in baselines_data if b['channelId'] == channel_data['channelId']),
            None
        )
        
        if not baseline_data or len(baseline_data.get('readings', [])) == 0:
            print(f"Warning: No baseline data for channel {channel_data['channelId']}, skipping spike detection")
            continue
        
        is_site_total = channel_data['channelId'] == site_channel_id
        result = detect_spikes(channel_data, baseline_data, config, interval_seconds, is_site_total)
        
        if result['spikeCount'] > 0:
            results.append(result)
    
    # Sort by peak power
    results.sort(
        key=lambda r: max(e['peakPower'] for e in r['events']) if r['events'] else 0,
        reverse=True
    )
    
    total_events = sum(r['spikeCount'] for r in results)
    total_excess_kwh = sum(
        sum(e['totalExcessKwh'] for e in r['events'])
        for r in results
    )
    
    return {
        'channelsWithSpikes': len(results),
        'totalSpikeEvents': total_events,
        'totalExcessKwh': round(total_excess_kwh, 2),
        'results': results,
        'topSpikes': get_top_spikes(results, 10),
    }


def get_top_spikes(results: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    """
    Get top N spikes by peak power
    
    Args:
        results: List of spike analysis results
        count: Number of top spikes to return
        
    Returns:
        List of top spike events
    """
    all_spikes = []
    
    for channel_result in results:
        for event in channel_result['events']:
            all_spikes.append({
                'channelName': channel_result['channelName'],
                **event,
            })
    
    all_spikes.sort(key=lambda s: s['peakPower'], reverse=True)
    
    return all_spikes[:count]
