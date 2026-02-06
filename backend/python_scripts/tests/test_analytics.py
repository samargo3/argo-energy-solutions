#!/usr/bin/env python3
"""
Analytics Testing Suite

Comprehensive testing of all analytics modules with real Wilson Center data.
Validates calculations, data quality, and report generation.

Usage:
    python test_analytics.py [--verbose]
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env')

from lib import (
    calculate_stats,
    percentile,
    calculate_iqr,
    get_last_complete_week,
    get_baseline_period,
    parse_timestamp,
)
from config import DEFAULT_CONFIG
from analyze import (
    analyze_sensor_health_for_site,
    analyze_after_hours_waste,
    analyze_anomalies,
    analyze_spikes,
    generate_quick_wins,
)


class AnalyticsTestSuite:
    """Test suite for analytics modules"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found")
        
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def _get_connection(self):
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def log(self, message, level="INFO"):
        """Log a message"""
        colors = {
            "INFO": "\033[94m",     # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",    # Red
            "RESET": "\033[0m"
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        
        if self.verbose or level in ["SUCCESS", "ERROR"]:
            print(f"{color}{message}{reset}")
    
    def assert_test(self, condition, test_name, details=""):
        """Assert a test condition"""
        if condition:
            self.tests_passed += 1
            self.test_results.append({"test": test_name, "status": "PASS", "details": details})
            self.log(f"✅ PASS: {test_name}", "SUCCESS")
            if details and self.verbose:
                self.log(f"   {details}", "INFO")
        else:
            self.tests_failed += 1
            self.test_results.append({"test": test_name, "status": "FAIL", "details": details})
            self.log(f"❌ FAIL: {test_name}", "ERROR")
            if details:
                self.log(f"   {details}", "WARNING")
    
    def fetch_test_data(self, site_id=23271):
        """Fetch real data for testing"""
        self.log("\n📊 Fetching test data from database...", "INFO")
        
        # Get last complete week
        period = get_last_complete_week('America/New_York')
        baseline = get_baseline_period(period['start'], 4)
        
        self.log(f"   Report period: {period['start'].date()} to {period['end'].date()}", "INFO")
        self.log(f"   Baseline: {baseline['start'].date()} to {baseline['end'].date()}", "INFO")
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Get channels
                cur.execute("""
                    SELECT channel_id, channel_name, channel_type
                    FROM channels
                    WHERE organization_id = %s
                    ORDER BY channel_name
                """, (str(site_id),))
                channels = cur.fetchall()
                
                self.log(f"   Found {len(channels)} channels", "INFO")
                
                # Get report period data
                report_data = []
                for channel in channels[:5]:  # Test with first 5 channels for speed
                    cur.execute("""
                        SELECT 
                            timestamp as ts,
                            energy_kwh as E,
                            power_kw as P
                        FROM readings
                        WHERE channel_id = %s
                            AND timestamp >= %s
                            AND timestamp <= %s
                        ORDER BY timestamp
                    """, (channel['channel_id'], period['start'], period['end']))
                    
                    readings = [dict(r) for r in cur.fetchall()]
                    if len(readings) > 0:
                        report_data.append({
                            'channelId': channel['channel_id'],
                            'channelName': channel['channel_name'],
                            'readings': readings,
                        })
                
                # Get baseline data
                baseline_data = []
                for channel in channels[:5]:
                    cur.execute("""
                        SELECT 
                            timestamp as ts,
                            energy_kwh as E,
                            power_kw as P
                        FROM readings
                        WHERE channel_id = %s
                            AND timestamp >= %s
                            AND timestamp <= %s
                        ORDER BY timestamp
                    """, (channel['channel_id'], baseline['start'], baseline['end']))
                    
                    readings = [dict(r) for r in cur.fetchall()]
                    if len(readings) > 0:
                        baseline_data.append({
                            'channelId': channel['channel_id'],
                            'channelName': channel['channel_name'],
                            'readings': readings,
                        })
        
        self.log(f"   Report data: {len(report_data)} channels", "SUCCESS")
        self.log(f"   Baseline data: {len(baseline_data)} channels", "SUCCESS")
        
        return report_data, baseline_data, period, baseline
    
    def test_statistics_functions(self):
        """Test statistical utility functions"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 1: Statistical Functions", "INFO")
        self.log("="*70, "INFO")
        
        # Test data
        test_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Test calculate_stats
        stats = calculate_stats(test_values)
        self.assert_test(
            stats['mean'] == 5.5,
            "calculate_stats: mean calculation",
            f"Expected 5.5, got {stats['mean']}"
        )
        self.assert_test(
            stats['median'] == 5.5,
            "calculate_stats: median calculation",
            f"Expected 5.5, got {stats['median']}"
        )
        self.assert_test(
            stats['min'] == 1 and stats['max'] == 10,
            "calculate_stats: min/max calculation",
            f"Expected min=1 max=10, got min={stats['min']} max={stats['max']}"
        )
        
        # Test percentile
        p25 = percentile(test_values, 25)
        p75 = percentile(test_values, 75)
        self.assert_test(
            p25 == 3.25,
            "percentile: 25th percentile",
            f"Expected 3.25, got {p25}"
        )
        self.assert_test(
            p75 == 7.75,
            "percentile: 75th percentile",
            f"Expected 7.75, got {p75}"
        )
        
        # Test IQR
        iqr = calculate_iqr(test_values)
        self.assert_test(
            iqr['iqr'] == 4.5,
            "calculate_iqr: IQR calculation",
            f"Expected 4.5, got {iqr['iqr']}"
        )
        
        # Test with empty array
        empty_stats = calculate_stats([])
        self.assert_test(
            empty_stats['count'] == 0,
            "calculate_stats: empty array handling",
            "Empty array should return count=0"
        )
    
    def test_sensor_health(self, report_data):
        """Test sensor health analytics"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 2: Sensor Health Analytics", "INFO")
        self.log("="*70, "INFO")
        
        config = DEFAULT_CONFIG
        
        # Run sensor health analysis
        result = analyze_sensor_health_for_site(report_data, config, 900)
        
        # Validate structure
        self.assert_test(
            'totalIssues' in result,
            "sensor_health: result structure",
            f"Result has totalIssues: {result.get('totalIssues')}"
        )
        
        self.assert_test(
            'issues' in result and isinstance(result['issues'], list),
            "sensor_health: issues list",
            f"Found {len(result.get('issues', []))} issues"
        )
        
        # Check severity counts
        total_severity = result['highSeverity'] + result['mediumSeverity'] + result['lowSeverity']
        self.assert_test(
            total_severity == result['totalIssues'],
            "sensor_health: severity count consistency",
            f"Total severity ({total_severity}) matches totalIssues ({result['totalIssues']})"
        )
        
        # Validate issue structure
        if len(result['issues']) > 0:
            issue = result['issues'][0]
            self.assert_test(
                all(key in issue for key in ['type', 'severity', 'channelId', 'channelName']),
                "sensor_health: issue structure",
                "Issue has all required fields"
            )
        
        self.log(f"\n   Summary:", "INFO")
        self.log(f"   Total issues: {result['totalIssues']}", "INFO")
        self.log(f"   High severity: {result['highSeverity']}", "INFO")
        self.log(f"   Medium severity: {result['mediumSeverity']}", "INFO")
        self.log(f"   Low severity: {result['lowSeverity']}", "INFO")
        
        return result
    
    def test_after_hours_waste(self, report_data, baseline_data):
        """Test after-hours waste analytics"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 3: After-Hours Waste Analytics", "INFO")
        self.log("="*70, "INFO")
        
        config = DEFAULT_CONFIG
        
        # Run after-hours waste analysis
        result = analyze_after_hours_waste(report_data, baseline_data, config, 900)
        
        # Validate structure
        self.assert_test(
            'summary' in result,
            "after_hours_waste: result structure",
            "Result has summary"
        )
        
        self.assert_test(
            'topMeters' in result and isinstance(result['topMeters'], list),
            "after_hours_waste: topMeters list",
            f"Found {len(result.get('topMeters', []))} meters with excess"
        )
        
        # Validate summary
        summary = result['summary']
        self.assert_test(
            all(key in summary for key in ['totalExcessKwh', 'totalExcessCost', 'estimatedAnnualCost']),
            "after_hours_waste: summary structure",
            "Summary has all required fields"
        )
        
        # Check calculations
        self.assert_test(
            summary['totalExcessKwh'] >= 0,
            "after_hours_waste: positive excess kWh",
            f"Excess kWh: {summary['totalExcessKwh']:.2f}"
        )
        
        self.assert_test(
            summary['estimatedAnnualCost'] == summary['totalExcessCost'] * 52,
            "after_hours_waste: annual cost calculation",
            f"Annual cost correctly calculated: ${summary['estimatedAnnualCost']:.2f}"
        )
        
        self.log(f"\n   Summary:", "INFO")
        self.log(f"   Total excess: {summary['totalExcessKwh']:.2f} kWh/week", "INFO")
        self.log(f"   Weekly cost: ${summary['totalExcessCost']:.2f}", "INFO")
        self.log(f"   Annual cost: ${summary['estimatedAnnualCost']:.2f}", "INFO")
        
        return result
    
    def test_anomaly_detection(self, report_data, baseline_data):
        """Test anomaly detection"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 4: Anomaly Detection", "INFO")
        self.log("="*70, "INFO")
        
        config = DEFAULT_CONFIG
        
        # Run anomaly detection
        result = analyze_anomalies(report_data, baseline_data, config, 900)
        
        # Validate structure
        self.assert_test(
            'totalAnomalyEvents' in result,
            "anomaly_detection: result structure",
            f"Found {result.get('totalAnomalyEvents', 0)} anomaly events"
        )
        
        self.assert_test(
            'results' in result and isinstance(result['results'], list),
            "anomaly_detection: results list",
            f"Analyzed {len(result.get('results', []))} channels"
        )
        
        # Check calculations
        self.assert_test(
            result['totalExcessKwh'] >= 0,
            "anomaly_detection: positive excess kWh",
            f"Total excess: {result['totalExcessKwh']:.2f} kWh"
        )
        
        # Validate timeline
        self.assert_test(
            'timeline' in result and isinstance(result['timeline'], list),
            "anomaly_detection: timeline structure",
            f"Timeline has {len(result.get('timeline', []))} events"
        )
        
        self.log(f"\n   Summary:", "INFO")
        self.log(f"   Channels with anomalies: {result['channelsWithAnomalies']}", "INFO")
        self.log(f"   Total events: {result['totalAnomalyEvents']}", "INFO")
        self.log(f"   Total excess: {result['totalExcessKwh']:.2f} kWh", "INFO")
        
        return result
    
    def test_spike_detection(self, report_data, baseline_data):
        """Test spike detection"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 5: Spike Detection", "INFO")
        self.log("="*70, "INFO")
        
        config = DEFAULT_CONFIG
        
        # Run spike detection
        result = analyze_spikes(report_data, baseline_data, config, 900)
        
        # Validate structure
        self.assert_test(
            'totalSpikeEvents' in result,
            "spike_detection: result structure",
            f"Found {result.get('totalSpikeEvents', 0)} spike events"
        )
        
        self.assert_test(
            'results' in result and isinstance(result['results'], list),
            "spike_detection: results list",
            f"Analyzed {len(result.get('results', []))} channels"
        )
        
        # Check calculations
        self.assert_test(
            result['totalExcessKwh'] >= 0,
            "spike_detection: positive excess kWh",
            f"Total excess: {result['totalExcessKwh']:.2f} kWh"
        )
        
        # Validate top spikes
        self.assert_test(
            'topSpikes' in result and isinstance(result['topSpikes'], list),
            "spike_detection: topSpikes structure",
            f"Top spikes list has {len(result.get('topSpikes', []))} entries"
        )
        
        self.log(f"\n   Summary:", "INFO")
        self.log(f"   Channels with spikes: {result['channelsWithSpikes']}", "INFO")
        self.log(f"   Total events: {result['totalSpikeEvents']}", "INFO")
        self.log(f"   Total excess: {result['totalExcessKwh']:.2f} kWh", "INFO")
        
        return result
    
    def test_quick_wins(self, analytics_results):
        """Test quick wins generation"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 6: Quick Wins Generation", "INFO")
        self.log("="*70, "INFO")
        
        config = DEFAULT_CONFIG
        
        # Generate quick wins
        quick_wins = generate_quick_wins(analytics_results, config)
        
        # Validate structure
        self.assert_test(
            isinstance(quick_wins, list),
            "quick_wins: result is list",
            f"Generated {len(quick_wins)} recommendations"
        )
        
        # Validate each quick win
        if len(quick_wins) > 0:
            win = quick_wins[0]
            required_fields = ['title', 'type', 'priority', 'impact', 'recommendations', 'confidence', 'owner', 'effort']
            self.assert_test(
                all(field in win for field in required_fields),
                "quick_wins: recommendation structure",
                "All required fields present"
            )
            
            # Check priority values
            valid_priorities = ['high', 'medium', 'low']
            self.assert_test(
                win['priority'] in valid_priorities,
                "quick_wins: valid priority",
                f"Priority is '{win['priority']}'"
            )
            
            # Check impact structure
            self.assert_test(
                'weeklyKwh' in win['impact'] or win['impact']['weeklyKwh'] == 'N/A',
                "quick_wins: impact structure",
                "Impact has weeklyKwh field"
            )
        
        # Check sorting (high priority first)
        if len(quick_wins) > 1:
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            is_sorted = all(
                priority_order[quick_wins[i]['priority']] <= priority_order[quick_wins[i+1]['priority']]
                for i in range(len(quick_wins)-1)
            )
            self.assert_test(
                is_sorted,
                "quick_wins: priority sorting",
                "Recommendations sorted by priority"
            )
        
        self.log(f"\n   Summary:", "INFO")
        for i, win in enumerate(quick_wins[:3], 1):
            self.log(f"   {i}. [{win['priority'].upper()}] {win['title']}", "INFO")
        
        return quick_wins
    
    def test_end_to_end(self):
        """Run complete end-to-end test"""
        self.log("\n" + "="*70, "INFO")
        self.log("TEST 7: End-to-End Integration", "INFO")
        self.log("="*70, "INFO")
        
        # Fetch data
        report_data, baseline_data, period, baseline = self.fetch_test_data()
        
        # Run all analytics
        sensor_health = analyze_sensor_health_for_site(report_data, DEFAULT_CONFIG, 900)
        after_hours = analyze_after_hours_waste(report_data, baseline_data, DEFAULT_CONFIG, 900)
        anomalies = analyze_anomalies(report_data, baseline_data, DEFAULT_CONFIG, 900)
        spikes = analyze_spikes(report_data, baseline_data, DEFAULT_CONFIG, 900)
        
        analytics_dict = {
            'sensorHealth': sensor_health,
            'afterHoursWaste': after_hours,
            'anomalies': anomalies,
            'spikes': spikes,
        }
        
        quick_wins = generate_quick_wins(analytics_dict, DEFAULT_CONFIG)
        
        # Build complete report structure
        report = {
            'metadata': {
                'generatedAt': datetime.now().isoformat(),
                'testRun': True,
                'period': {
                    'start': period['start'].isoformat(),
                    'end': period['end'].isoformat(),
                },
            },
            'summary': {
                'channelsTested': len(report_data),
                'reportReadings': sum(len(c['readings']) for c in report_data),
                'baselineReadings': sum(len(c['readings']) for c in baseline_data),
            },
            'results': {
                'sensorHealth': {
                    'totalIssues': sensor_health['totalIssues'],
                    'highSeverity': sensor_health['highSeverity'],
                },
                'afterHoursWaste': {
                    'totalExcess': after_hours['summary']['totalExcessKwh'],
                },
                'anomalies': {
                    'totalEvents': anomalies['totalAnomalyEvents'],
                },
                'spikes': {
                    'totalEvents': spikes['totalSpikeEvents'],
                },
                'quickWins': len(quick_wins),
            }
        }
        
        # Save test report
        output_path = 'reports/test-analytics-report.json'
        os.makedirs('reports', exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.assert_test(
            os.path.exists(output_path),
            "end_to_end: report generation",
            f"Report saved to {output_path}"
        )
        
        self.log(f"\n   Test Report Summary:", "INFO")
        self.log(f"   Channels tested: {report['summary']['channelsTested']}", "INFO")
        self.log(f"   Report readings: {report['summary']['reportReadings']:,}", "INFO")
        self.log(f"   Baseline readings: {report['summary']['baselineReadings']:,}", "INFO")
        self.log(f"   Sensor issues: {report['results']['sensorHealth']['totalIssues']}", "INFO")
        self.log(f"   After-hours waste: {report['results']['afterHoursWaste']['totalExcess']:.2f} kWh", "INFO")
        self.log(f"   Anomalies: {report['results']['anomalies']['totalEvents']}", "INFO")
        self.log(f"   Spikes: {report['results']['spikes']['totalEvents']}", "INFO")
        self.log(f"   Quick wins: {report['results']['quickWins']}", "INFO")
        
        return report
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("\n" + "="*70, "SUCCESS")
        self.log("🧪 ANALYTICS TESTING SUITE", "SUCCESS")
        self.log("="*70 + "\n", "SUCCESS")
        
        try:
            # Fetch test data once
            report_data, baseline_data, period, baseline = self.fetch_test_data()
            
            # Run tests
            self.test_statistics_functions()
            sensor_health = self.test_sensor_health(report_data)
            after_hours = self.test_after_hours_waste(report_data, baseline_data)
            anomalies = self.test_anomaly_detection(report_data, baseline_data)
            spikes = self.test_spike_detection(report_data, baseline_data)
            
            analytics_results = {
                'sensorHealth': sensor_health,
                'afterHoursWaste': after_hours,
                'anomalies': anomalies,
                'spikes': spikes,
            }
            
            quick_wins = self.test_quick_wins(analytics_results)
            self.test_end_to_end()
            
            # Print summary
            self.print_summary()
            
            return self.tests_failed == 0
            
        except Exception as e:
            self.log(f"\n❌ CRITICAL ERROR: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def print_summary(self):
        """Print test summary"""
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.log("\n" + "="*70, "INFO")
        self.log("📊 TEST SUMMARY", "INFO")
        self.log("="*70, "INFO")
        self.log(f"\nTotal Tests: {total_tests}", "INFO")
        self.log(f"Passed: {self.tests_passed}", "SUCCESS")
        if self.tests_failed > 0:
            self.log(f"Failed: {self.tests_failed}", "ERROR")
        self.log(f"Pass Rate: {pass_rate:.1f}%", "SUCCESS" if pass_rate == 100 else "WARNING")
        
        if self.tests_failed == 0:
            self.log("\n✅ ALL TESTS PASSED! Analytics are working correctly.", "SUCCESS")
        else:
            self.log("\n⚠️  SOME TESTS FAILED. Review the output above.", "WARNING")
        
        self.log("\n" + "="*70 + "\n", "INFO")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test analytics modules with real data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    suite = AnalyticsTestSuite(verbose=args.verbose)
    success = suite.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
