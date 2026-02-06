"""
Quick Wins Generator

Generates actionable recommendations based on analytics findings

Python conversion of backend/scripts/reports/analytics/quick-wins.js
"""

from typing import List, Dict, Any, Optional


def generate_quick_wins(analytics: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate quick wins from all analytics results
    
    Args:
        analytics: Dictionary with all analytics results (anomalies, waste, spikes, health)
        config: Configuration dictionary
        
    Returns:
        List of quick win recommendations, sorted by priority and impact
    """
    wins = []
    
    # 1. After-hours waste opportunities
    if analytics.get('afterHoursWaste') and analytics['afterHoursWaste'].get('topMeters'):
        for meter in analytics['afterHoursWaste']['topMeters'][:3]:
            if meter['impact']['excessKwh'] >= config['quickWins']['minWeeklyImpact']:
                excess_pct = (meter['impact']['excessKwh'] / meter['thisWeek']['totalAfterHoursKwh'] * 100) if meter['thisWeek']['totalAfterHoursKwh'] > 0 else 0
                
                wins.append({
                    'title': f"Reduce overnight base load on {meter['channelName']}",
                    'type': 'after_hours_waste',
                    'priority': 'high' if meter['impact']['excessKwh'] > 100 else 'medium',
                    'impact': {
                        'weeklyKwh': meter['impact']['excessKwh'],
                        'weeklyCost': meter['impact']['excessCost'],
                        'annualCost': meter['impact']['excessCost'] * 52,
                    },
                    'description': (
                        f"{meter['channelName']} is consuming {meter['thisWeek']['avgPowerKw']:.1f} kW on average during after-hours, "
                        f"{excess_pct:.0f}% above baseline. "
                        f"This suggests equipment running unnecessarily or at higher than needed levels."
                    ),
                    'recommendations': [
                        'Verify equipment schedules match actual occupancy',
                        'Check for HVAC systems running outside business hours',
                        'Look for computers/servers left on unnecessarily',
                        'Consider adding occupancy sensors or time-based controls',
                    ],
                    'confidence': 'high' if meter['thisWeek']['intervals'] > 100 else 'medium',
                    'owner': 'Facilities Manager',
                    'effort': 'Low to Medium',
                })
    
    # 2. Sensor/communications issues
    if analytics.get('sensorHealth') and analytics['sensorHealth'].get('highSeverity', 0) > 0:
        high_issues = [i for i in analytics['sensorHealth']['issues'] if i['severity'] == 'high']
        affected_channels = list(set(i['channelName'] for i in high_issues))
        
        if len(affected_channels) > 0:
            wins.append({
                'title': f"Fix data communication issues on {len(affected_channels)} meter(s)",
                'type': 'sensor_health',
                'priority': 'high',
                'impact': {
                    'weeklyKwh': 'N/A',
                    'weeklyCost': 0,
                    'annualCost': 0,
                    'description': 'Missing data prevents accurate monitoring and may hide energy waste',
                },
                'description': (
                    f"{len(affected_channels)} meter(s) have high-severity data issues: {', '.join(affected_channels[:3])}. "
                    f"This prevents accurate energy monitoring and may be hiding consumption anomalies."
                ),
                'recommendations': [
                    'Check network connectivity and power to affected meters',
                    'Verify meter configuration and data logging settings',
                    'Contact meter vendor if issues persist',
                    'Consider replacing meters with repeated failures',
                ],
                'confidence': 'high',
                'owner': 'Energy Manager / Facilities',
                'effort': 'Medium',
            })
    
    # 3. Anomaly patterns
    if analytics.get('anomalies') and analytics['anomalies'].get('totalAnomalyEvents', 0) > 0:
        results = analytics['anomalies'].get('results', [])
        if len(results) > 0:
            top_anomaly = results[0]
            
            if top_anomaly and len(top_anomaly.get('events', [])) > 0:
                top_event = top_anomaly['events'][0]
                
                wins.append({
                    'title': f"Investigate recurring spikes on {top_anomaly['channelName']}",
                    'type': 'anomaly',
                    'priority': 'high' if top_event['totalExcessKwh'] > 50 else 'medium',
                    'impact': {
                        'weeklyKwh': top_event['totalExcessKwh'],
                        'weeklyCost': top_event['totalExcessKwh'] * config['tariff']['defaultRate'],
                        'annualCost': top_event['totalExcessKwh'] * config['tariff']['defaultRate'] * 52,
                    },
                    'description': (
                        f"{top_anomaly['channelName']} showed {top_anomaly['anomalyCount']} anomalous event(s) this week, "
                        f"consuming {top_event['totalExcessKwh']:.1f} kWh above normal patterns. "
                        f"Peak was {top_event['peakPower']:.1f} kW during {top_event['context']}."
                    ),
                    'recommendations': [
                        'Review equipment operation logs for this time period',
                        'Check if new equipment was added or settings changed',
                        'Verify load is appropriate for operational needs',
                        'Consider load shifting if during peak demand periods',
                    ],
                    'confidence': 'medium',
                    'owner': 'Operations / Energy Manager',
                    'effort': 'Medium',
                })
    
    # 4. Demand spike reduction
    if analytics.get('spikes') and analytics['spikes'].get('topSpikes') and len(analytics['spikes']['topSpikes']) > 0:
        top_spike = analytics['spikes']['topSpikes'][0]
        
        demand_charge = config['tariff'].get('demandCharge')
        additional_note = (
            f"Plus potential demand charges: ${top_spike['peakPower'] * demand_charge:.2f}/month"
            if demand_charge
            else 'May also impact demand charges if applicable'
        )
        
        wins.append({
            'title': f"Reduce demand spikes on {top_spike['channelName']}",
            'type': 'spike',
            'priority': 'medium',
            'impact': {
                'weeklyKwh': top_spike['totalExcessKwh'],
                'weeklyCost': top_spike['totalExcessKwh'] * config['tariff']['defaultRate'],
                'annualCost': top_spike['totalExcessKwh'] * config['tariff']['defaultRate'] * 52,
                'additionalNote': additional_note,
            },
            'description': (
                f"{top_spike['channelName']} experienced spikes up to {top_spike['peakPower']:.1f} kW. "
                f"This may indicate short-cycling, simultaneous equipment starts, or undersized equipment."
            ),
            'recommendations': [
                'Stagger start times for large equipment',
                'Check for short-cycling HVAC or refrigeration',
                'Consider soft-start controllers for motors',
                'Verify equipment is properly sized',
            ],
            'confidence': 'medium',
            'owner': 'Facilities Manager',
            'effort': 'Medium to High',
        })
    
    # 5. Low-hanging fruit: flatlined sensors
    flatline_issues = [i for i in analytics.get('sensorHealth', {}).get('issues', []) if i['type'] == 'flatline']
    if len(flatline_issues) > 0:
        wins.append({
            'title': f"Check stuck sensors ({len(flatline_issues)} detected)",
            'type': 'sensor_health',
            'priority': 'low',
            'impact': {
                'weeklyKwh': 'N/A',
                'weeklyCost': 0,
                'annualCost': 0,
                'description': 'Stuck sensors provide inaccurate data for decision-making',
            },
            'description': (
                f"{len(flatline_issues)} sensor(s) appear flatlined (stuck at constant value). "
                f"This typically indicates sensor failure or configuration issues."
            ),
            'recommendations': [
                'Inspect physical sensors for damage or disconnection',
                'Reset or recalibrate affected meters',
                'Replace sensors if recalibration fails',
            ],
            'confidence': 'high',
            'owner': 'Facilities / Maintenance',
            'effort': 'Low',
        })
    
    # 6. Aggregate opportunity summary
    if analytics.get('afterHoursWaste') and analytics['afterHoursWaste'].get('summary', {}).get('totalExcessKwh', 0) > 0:
        summary = analytics['afterHoursWaste']['summary']
        
        wins.append({
            'title': 'Overall after-hours optimization opportunity',
            'type': 'summary',
            'priority': 'high',
            'impact': {
                'weeklyKwh': summary['totalExcessKwh'],
                'weeklyCost': summary['totalExcessCost'],
                'annualCost': summary['estimatedAnnualCost'],
            },
            'description': (
                f"Site-wide after-hours consumption is {summary['totalExcessKwh']:.0f} kWh/week "
                f"above baseline. This represents a significant optimization opportunity."
            ),
            'recommendations': [
                'Conduct comprehensive after-hours walk-through',
                'Review and update all equipment schedules',
                'Implement building automation or occupancy-based controls',
                'Set up weekly monitoring to track progress',
            ],
            'confidence': 'high',
            'owner': 'Energy Manager / Facilities Director',
            'effort': 'Medium',
        })
    
    # Sort by priority and impact
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    
    def sort_key(win):
        priority_rank = priority_order.get(win['priority'], 3)
        impact_kwh = win['impact']['weeklyKwh'] if isinstance(win['impact']['weeklyKwh'], (int, float)) else 0
        return (priority_rank, -impact_kwh)  # negative for descending impact
    
    wins.sort(key=sort_key)
    
    # Limit to max count
    return wins[:config['quickWins']['maxCount']]
