#!/usr/bin/env python3
"""
Weekly Exceptions & Opportunities Brief Generator

Generates a comprehensive weekly energy analytics report from PostgreSQL data

Usage:
    python generate_weekly_report.py --site <org_id> [options]

Options:
    --site <id>        Site organization ID (required)
    --start <iso>      Report start date (ISO format, optional)
    --end <iso>        Report end date (ISO format, optional)
    --out <file>       Output file path (default: report-{timestamp}.json)
    --timezone <tz>    Timezone override (default: America/New_York)
    --html             Also generate HTML report

If --start and --end are not provided, uses last complete week (Mon-Sun)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env')

from lib import (
    get_last_complete_week,
    get_baseline_period,
    format_date_range,
    to_unix_timestamp,
)
from config import DEFAULT_CONFIG, merge_config
from analyze import (
    analyze_sensor_health_for_site,
    analyze_after_hours_waste,
    analyze_anomalies,
    analyze_spikes,
    generate_quick_wins,
)


class DatabaseDataFetcher:
    """Fetches energy data from PostgreSQL database"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def fetch_site_metadata(self, site_id: int) -> Dict[str, Any]:
        """Fetch site metadata"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT organization_id, organization_name
                    FROM organizations
                    WHERE organization_id = %s
                """, (str(site_id),))
                
                result = cur.fetchone()
                if not result:
                    return {
                        'siteId': site_id,
                        'siteName': f'Site {site_id}',
                        'address': 'N/A',
                    }
                
                return {
                    'siteId': site_id,
                    'siteName': result['organization_name'],
                    'address': 'N/A',  # Could be added to organizations table
                }
    
    def fetch_channels(self, site_id: int) -> List[Dict[str, Any]]:
        """Fetch all channels for a site"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT channel_id, channel_name, channel_type, unit
                    FROM channels
                    WHERE organization_id = %s
                    ORDER BY channel_name
                """, (str(site_id),))
                
                return [dict(row) for row in cur.fetchall()]
    
    def fetch_readings(
        self,
        channel_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch readings for a channel in a date range"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        timestamp as ts,
                        energy_kwh as E,
                        power_kw as P,
                        voltage_v,
                        current_a,
                        power_factor
                    FROM readings
                    WHERE channel_id = %s
                        AND timestamp >= %s
                        AND timestamp <= %s
                    ORDER BY timestamp
                """, (channel_id, start_date, end_date))
                
                return [dict(row) for row in cur.fetchall()]
    
    def fetch_all_data(
        self,
        site_id: int,
        report_period: Dict[str, datetime],
        baseline_period: Dict[str, datetime]
    ) -> Dict[str, Any]:
        """Fetch all required data for report generation"""
        
        print(f"\n📊 Fetching data from PostgreSQL...")
        
        # Fetch site metadata
        print(f"   Fetching site metadata...")
        site_metadata = self.fetch_site_metadata(site_id)
        
        # Fetch channels
        print(f"   Fetching channels...")
        channels = self.fetch_channels(site_id)
        print(f"   Found {len(channels)} channels")
        
        # Fetch report period data
        print(f"\n📅 Fetching report period data...")
        report_data = []
        for i, channel in enumerate(channels, 1):
            print(f"   [{i}/{len(channels)}] {channel['channel_name']}...", end=' ')
            readings = self.fetch_readings(
                channel['channel_id'],
                report_period['start'],
                report_period['end']
            )
            print(f"{len(readings)} readings")
            
            if len(readings) > 0:
                report_data.append({
                    'channelId': channel['channel_id'],
                    'channelName': channel['channel_name'],
                    'readings': readings,
                })
        
        # Fetch baseline data
        print(f"\n📊 Fetching baseline period data...")
        baseline_data = []
        for i, channel in enumerate(channels, 1):
            print(f"   [{i}/{len(channels)}] {channel['channel_name']}...", end=' ')
            readings = self.fetch_readings(
                channel['channel_id'],
                baseline_period['start'],
                baseline_period['end']
            )
            print(f"{len(readings)} readings")
            
            if len(readings) > 0:
                baseline_data.append({
                    'channelId': channel['channel_id'],
                    'channelName': channel['channel_name'],
                    'readings': readings,
                })
        
        # Calculate resolution (assume 15-minute = 900s)
        resolution = 900
        
        return {
            'siteMetadata': site_metadata,
            'reportData': report_data,
            'baselineData': baseline_data,
            'resolution': resolution,
        }


def generate_headline(analytics: Dict[str, Any]) -> List[str]:
    """Generate headline summary of key findings"""
    headlines = []
    
    if analytics['sensorHealth']['highSeverity'] > 0:
        headlines.append(
            f"{analytics['sensorHealth']['highSeverity']} critical data quality issue(s) detected"
        )
    
    if analytics['afterHoursWaste']['summary']['totalExcessKwh'] > 0:
        headlines.append(
            f"${analytics['afterHoursWaste']['summary']['totalExcessCost']:.0f}/week "
            f"in after-hours waste identified"
        )
    
    if analytics['anomalies']['totalAnomalyEvents'] > 5:
        headlines.append(
            f"{analytics['anomalies']['totalAnomalyEvents']} unusual consumption events detected"
        )
    
    return headlines if headlines else ["No significant issues detected this week"]


def identify_top_risks(analytics: Dict[str, Any]) -> List[str]:
    """Identify top risks from analytics"""
    risks = []
    
    # High severity sensor issues
    if analytics['sensorHealth']['highSeverity'] > 0:
        risks.append(f"Missing data on {analytics['sensorHealth']['highSeverity']} channel(s)")
    
    # Large anomalies
    if analytics['anomalies']['totalExcessKwh'] > 100:
        risks.append(f"Significant unexpected consumption: {analytics['anomalies']['totalExcessKwh']:.0f} kWh")
    
    # After-hours waste
    if analytics['afterHoursWaste']['summary']['totalExcessKwh'] > 100:
        risks.append(f"High after-hours waste: {analytics['afterHoursWaste']['summary']['totalExcessKwh']:.0f} kWh/week")
    
    return risks if risks else ["No significant risks identified"]


def identify_top_opportunities(analytics: Dict[str, Any]) -> List[str]:
    """Identify top opportunities from analytics"""
    opportunities = []
    
    # After-hours waste
    if analytics['afterHoursWaste']['summary']['totalExcessKwh'] > 50:
        opportunities.append(
            f"After-hours optimization: ${analytics['afterHoursWaste']['summary']['estimatedAnnualCost']:.0f}/year potential"
        )
    
    # Spikes
    if analytics['spikes']['totalSpikeEvents'] > 0:
        opportunities.append(f"Demand spike reduction: {analytics['spikes']['totalSpikeEvents']} events to investigate")
    
    return opportunities if opportunities else ["Continue monitoring for optimization opportunities"]


def calculate_avg_completeness(channels_data: List[Dict[str, Any]]) -> float:
    """Calculate average data completeness"""
    if not channels_data:
        return 0.0
    
    # Simplified: assume 672 readings per week (7 days * 96 intervals/day)
    expected = 672
    total_completeness = 0.0
    
    for channel in channels_data:
        actual = len(channel.get('readings', []))
        completeness = (actual / expected) * 100
        total_completeness += completeness
    
    return total_completeness / len(channels_data)


def generate_weekly_brief(options: Dict[str, Any]) -> Dict[str, Any]:
    """Main report generation function"""
    
    site_id = options['site_id']
    start_date = options['start_date']
    end_date = options['end_date']
    config = options['config']
    output_path = options['output_path']
    
    print('\n' + '=' * 70)
    print('WEEKLY EXCEPTIONS & OPPORTUNITIES BRIEF')
    print('=' * 70)
    print(f"Site ID: {site_id}")
    print(f"Period: {format_date_range(start_date, end_date)}")
    print(f"Timezone: {config['timezone']}")
    print('=' * 70 + '\n')
    
    # Initialize data fetcher
    data_fetcher = DatabaseDataFetcher(config)
    
    # Calculate baseline period
    baseline_period = get_baseline_period(start_date, config['baseline']['weeksCount'])
    
    print(f"Baseline period: {format_date_range(baseline_period['start'], baseline_period['end'])}")
    print(f"({config['baseline']['weeksCount']} weeks prior to report week)\n")
    
    # Fetch all data
    data = data_fetcher.fetch_all_data(
        site_id,
        {'start': start_date, 'end': end_date},
        baseline_period
    )
    
    print('\n' + '=' * 70)
    print('RUNNING ANALYTICS')
    print('=' * 70 + '\n')
    
    # Run analytics
    print('1. Analyzing sensor health...')
    sensor_health = analyze_sensor_health_for_site(
        data['reportData'],
        config,
        data['resolution']
    )
    print(f"   Found {sensor_health['totalIssues']} issue(s)\n")
    
    print('2. Analyzing after-hours waste...')
    after_hours_waste = analyze_after_hours_waste(
        data['reportData'],
        data['baselineData'],
        config,
        data['resolution']
    )
    print(f"   Found {len(after_hours_waste['topMeters'])} meter(s) with significant excess\n")
    
    print('3. Detecting anomalies...')
    anomalies = analyze_anomalies(
        data['reportData'],
        data['baselineData'],
        config,
        data['resolution']
    )
    print(f"   Found {anomalies['totalAnomalyEvents']} anomaly event(s)\n")
    
    print('4. Detecting spikes...')
    spikes = analyze_spikes(
        data['reportData'],
        data['baselineData'],
        config,
        data['resolution']
    )
    print(f"   Found {spikes['totalSpikeEvents']} spike event(s)\n")
    
    print('5. Generating quick wins...')
    analytics_dict = {
        'sensorHealth': sensor_health,
        'afterHoursWaste': after_hours_waste,
        'anomalies': anomalies,
        'spikes': spikes,
    }
    quick_wins = generate_quick_wins(analytics_dict, config)
    print(f"   Generated {len(quick_wins)} recommendation(s)\n")
    
    # Build report structure
    report = {
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'reportVersion': '1.0.0-python',
            'site': data['siteMetadata'],
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'timezone': config['timezone'],
            },
            'baseline': {
                'start': baseline_period['start'].isoformat(),
                'end': baseline_period['end'].isoformat(),
                'weeksCount': config['baseline']['weeksCount'],
            },
            'dataResolution': f"{data['resolution']}s ({data['resolution'] // 60}min)",
        },
        
        'summary': {
            'headline': generate_headline(analytics_dict),
            'topRisks': identify_top_risks(analytics_dict),
            'topOpportunities': identify_top_opportunities(analytics_dict),
            'totalPotentialSavings': {
                'weeklyKwh': after_hours_waste['summary']['totalExcessKwh'] + anomalies['totalExcessKwh'],
                'weeklyCost': after_hours_waste['summary']['totalExcessCost'] + (anomalies['totalExcessKwh'] * config['tariff']['defaultRate']),
                'estimatedAnnual': (after_hours_waste['summary']['totalExcessCost'] + (anomalies['totalExcessKwh'] * config['tariff']['defaultRate'])) * 52,
            },
        },
        
        'sections': {
            'sensorHealth': {
                'summary': sensor_health['summary'],
                'totalIssues': sensor_health['totalIssues'],
                'bySeverity': {
                    'high': sensor_health['highSeverity'],
                    'medium': sensor_health['mediumSeverity'],
                    'low': sensor_health['lowSeverity'],
                },
                'issues': sensor_health['issues'],
            },
            
            'afterHoursWaste': {
                'summary': after_hours_waste['summary'],
                'topMeters': after_hours_waste['topMeters'],
            },
            
            'anomalies': {
                'summary': {
                    'totalEvents': anomalies['totalAnomalyEvents'],
                    'affectedChannels': anomalies['channelsWithAnomalies'],
                    'totalExcessKwh': anomalies['totalExcessKwh'],
                },
                'timeline': anomalies['timeline'],
                'byChannel': anomalies['results'],
            },
            
            'spikes': {
                'summary': {
                    'totalEvents': spikes['totalSpikeEvents'],
                    'affectedChannels': spikes['channelsWithSpikes'],
                    'totalExcessKwh': spikes['totalExcessKwh'],
                },
                'topSpikes': spikes['topSpikes'],
                'byChannel': spikes['results'],
            },
            
            'quickWins': quick_wins,
        },
        
        'charts': {
            'afterHoursRanking': after_hours_waste.get('charts', {}).get('topContributorsChart', []),
            'anomalyTimeline': anomalies.get('timeline', []),
            'spikeEvents': spikes.get('topSpikes', []),
        },
        
        'dataQuality': {
            'channelsAnalyzed': len(data['reportData']),
            'avgCompleteness': calculate_avg_completeness(data['reportData']),
        },
    }
    
    # Save JSON report
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    file_size_kb = os.path.getsize(output_path) / 1024
    
    print('\n' + '=' * 70)
    print('REPORT GENERATION COMPLETE')
    print('=' * 70)
    print(f"JSON Report: {output_path}")
    print(f"  File size: {file_size_kb:.1f} KB")
    
    # Print summary
    print_summary(report)
    
    return report


def print_summary(report: Dict[str, Any]):
    """Print report summary to console"""
    print('\n' + '=' * 70)
    print('REPORT SUMMARY')
    print('=' * 70)
    
    print('\nHEADLINE:')
    for headline in report['summary']['headline']:
        print(f"  • {headline}")
    
    print('\nTOP QUICK WINS:')
    for i, win in enumerate(report['sections']['quickWins'][:5], 1):
        impact = win['impact']
        if isinstance(impact['weeklyKwh'], (int, float)):
            print(f"  {i}. {win['title']}")
            print(f"     Impact: {impact['weeklyKwh']:.0f} kWh/week (${impact['weeklyCost']:.0f}/week)")
        else:
            print(f"  {i}. {win['title']}")
    
    print('\nPOTENTIAL SAVINGS:')
    savings = report['summary']['totalPotentialSavings']
    print(f"  Weekly: {savings['weeklyKwh']:.0f} kWh (${savings['weeklyCost']:.0f})")
    print(f"  Annual: ${savings['estimatedAnnual']:.0f}")
    
    print('\n' + '=' * 70 + '\n')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate Weekly Exceptions & Opportunities Brief'
    )
    parser.add_argument('--site', type=int, required=True, help='Site organization ID')
    parser.add_argument('--start', type=str, help='Report start date (ISO format)')
    parser.add_argument('--end', type=str, help='Report end date (ISO format)')
    parser.add_argument('--out', type=str, help='Output file path')
    parser.add_argument('--timezone', type=str, default='America/New_York', help='Timezone')
    parser.add_argument('--html', action='store_true', help='Also generate HTML report')
    
    args = parser.parse_args()
    
    # Determine report period
    if args.start and args.end:
        start_date = datetime.fromisoformat(args.start)
        end_date = datetime.fromisoformat(args.end)
    else:
        period = get_last_complete_week(args.timezone)
        start_date = period['start']
        end_date = period['end']
    
    # Determine output path
    if args.out:
        output_path = args.out
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"reports/weekly-brief-{args.site}-{timestamp}.json"
    
    # Merge config
    config = merge_config({'timezone': args.timezone})
    
    # Generate report
    try:
        report = generate_weekly_brief({
            'site_id': args.site,
            'start_date': start_date,
            'end_date': end_date,
            'config': config,
            'output_path': output_path,
        })
        
        print(f"✅ Report generated successfully!")
        print(f"\n💡 Review the JSON file for detailed analytics:\n   {output_path}\n")
        
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
