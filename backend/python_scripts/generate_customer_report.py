#!/usr/bin/env python3
"""
Customer-Ready Weekly Exceptions & Opportunities Brief

Generates a professional HTML report for Facilities/Operations and Energy Managers.
Answers: "What changed this week that needs attention?"

Sections:
- Executive Summary
- Sensor & Communications Issues
- After-Hours Energy Waste
- Unusual Spikes & Anomalies
- Quick Wins & Recommendations

Usage:
    python generate_customer_report.py --site 23271
    python generate_customer_report.py --site 23271 --output custom-report.html
"""

import os
import sys
import json
import argparse
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.python_scripts.lib import (
    get_last_complete_week,
    get_baseline_period,
    format_date_range,
)
from backend.python_scripts.config import DEFAULT_CONFIG
from backend.python_scripts.analytics import (
    analyze_sensor_health_for_site,
    analyze_after_hours_waste,
    analyze_anomalies,
    analyze_spikes,
    generate_quick_wins,
)

load_dotenv()


def fetch_report_data(conn, site_id, start_date, end_date):
    """Fetch report period data from database"""
    with conn.cursor() as cur:
        # Get organization name
        cur.execute("""
            SELECT organization_name 
            FROM organizations 
            WHERE organization_id = %s
        """, (str(site_id),))
        result = cur.fetchone()
        org_name = result['organization_name'] if result else f"Site {site_id}"
        
        # Get channels
        cur.execute("""
            SELECT channel_id, channel_name, channel_type
            FROM channels
            WHERE organization_id = %s
            ORDER BY channel_name
        """, (str(site_id),))
        channels = cur.fetchall()
        
        # Fetch readings for each channel
        report_data = []
        for channel in channels:
            cur.execute("""
                SELECT 
                    timestamp as ts,
                    energy_kwh as E,
                    power_kw as P,
                    voltage_v,
                    current_a,
                    power_factor,
                    temperature_c,
                    relative_humidity
                FROM readings
                WHERE channel_id = %s
                    AND timestamp >= %s
                    AND timestamp <= %s
                ORDER BY timestamp
            """, (channel['channel_id'], start_date, end_date))
            
            readings = [dict(r) for r in cur.fetchall()]
            if len(readings) > 0:
                report_data.append({
                    'channelId': channel['channel_id'],
                    'channelName': channel['channel_name'],
                    'channelType': channel['channel_type'],
                    'readings': readings,
                })
        
        return org_name, report_data


def generate_html_report(data, org_name, period, output_path):
    """Generate professional HTML report"""
    
    # Extract data
    sensor_health = data['sensorHealth']
    after_hours = data['afterHoursWaste']
    anomalies = data['anomalies']
    spikes = data['spikes']
    quick_wins = data['quickWins']
    
    # Format dates
    start_date = datetime.fromisoformat(period['start'].replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    
    # Calculate executive summary stats
    total_issues = sensor_health['totalIssues']
    high_priority_issues = sensor_health['highSeverity']
    weekly_waste_kwh = after_hours['summary']['totalExcessKwh']
    weekly_waste_cost = after_hours['summary']['totalExcessCost']
    annual_savings_potential = after_hours['summary']['estimatedAnnualCost']
    total_anomalies = anomalies['totalAnomalyEvents']
    total_spikes = spikes['totalSpikeEvents']
    total_recommendations = len(quick_wins)
    
    # Determine status color
    if high_priority_issues > 0 or weekly_waste_cost > 100:
        status_color = '#dc3545'  # Red
        status_text = 'Action Required'
    elif total_issues > 0 or weekly_waste_cost > 50:
        status_color = '#ffc107'  # Yellow
        status_text = 'Attention Needed'
    else:
        status_color = '#28a745'  # Green
        status_text = 'Operating Normally'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Energy Report - {org_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }}
        
        .header h1 {{
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .header .subtitle {{
            font-size: 18px;
            opacity: 0.9;
        }}
        
        .header .date-range {{
            margin-top: 16px;
            font-size: 16px;
            opacity: 0.8;
        }}
        
        .status-banner {{
            background: {status_color};
            color: white;
            padding: 20px 40px;
            font-size: 18px;
            font-weight: 600;
            text-align: center;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 48px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 3px solid #667eea;
        }}
        
        .section-icon {{
            font-size: 32px;
            margin-right: 16px;
        }}
        
        .section-title {{
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .summary-card .label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        
        .summary-card .value {{
            font-size: 32px;
            font-weight: 700;
        }}
        
        .summary-card .unit {{
            font-size: 16px;
            opacity: 0.8;
        }}
        
        .alert-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 4px;
        }}
        
        .alert-box.danger {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        
        .alert-box.success {{
            background: #d4edda;
            border-left-color: #28a745;
        }}
        
        .alert-box .title {{
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 16px;
        }}
        
        .alert-box .details {{
            font-size: 14px;
            color: #666;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin-bottom: 24px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        thead {{
            background: #f8f9fa;
        }}
        
        th {{
            text-align: left;
            padding: 12px;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .priority-high {{
            color: #dc3545;
            font-weight: 600;
        }}
        
        .priority-medium {{
            color: #ffc107;
            font-weight: 600;
        }}
        
        .priority-low {{
            color: #6c757d;
        }}
        
        .recommendation-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .recommendation-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .recommendation-card.high {{
            border-left: 4px solid #dc3545;
        }}
        
        .recommendation-card.medium {{
            border-left: 4px solid #ffc107;
        }}
        
        .recommendation-card.low {{
            border-left: 4px solid #28a745;
        }}
        
        .recommendation-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }}
        
        .recommendation-title {{
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .recommendation-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .recommendation-badge.high {{
            background: #dc3545;
            color: white;
        }}
        
        .recommendation-badge.medium {{
            background: #ffc107;
            color: #333;
        }}
        
        .recommendation-badge.low {{
            background: #28a745;
            color: white;
        }}
        
        .recommendation-impact {{
            display: flex;
            gap: 24px;
            margin: 12px 0;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        
        .impact-item {{
            display: flex;
            flex-direction: column;
        }}
        
        .impact-label {{
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 4px;
        }}
        
        .impact-value {{
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .recommendation-actions {{
            margin-top: 12px;
        }}
        
        .recommendation-actions ul {{
            margin-left: 20px;
        }}
        
        .recommendation-actions li {{
            margin-bottom: 8px;
            color: #555;
        }}
        
        .no-issues {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }}
        
        .no-issues .icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 32px 40px;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
        
        .footer .logo {{
            font-size: 20px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
            }}
            
            .recommendation-card:hover {{
                transform: none;
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Weekly Exceptions & Opportunities Brief</h1>
            <div class="subtitle">{org_name}</div>
            <div class="date-range">📅 {date_range}</div>
        </div>
        
        <div class="status-banner">
            Status: {status_text}
        </div>
        
        <div class="content">
            <!-- EXECUTIVE SUMMARY -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon">📊</div>
                    <div class="section-title">Executive Summary</div>
                </div>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="label">Sensor Issues</div>
                        <div class="value">{total_issues}</div>
                        <div class="unit">{high_priority_issues} high priority</div>
                    </div>
                    
                    <div class="summary-card">
                        <div class="label">Weekly Waste</div>
                        <div class="value">{weekly_waste_kwh:.0f}</div>
                        <div class="unit">kWh (${weekly_waste_cost:.0f})</div>
                    </div>
                    
                    <div class="summary-card">
                        <div class="label">Annual Potential</div>
                        <div class="value">${annual_savings_potential:,.0f}</div>
                        <div class="unit">in savings</div>
                    </div>
                    
                    <div class="summary-card">
                        <div class="label">Recommendations</div>
                        <div class="value">{total_recommendations}</div>
                        <div class="unit">quick wins</div>
                    </div>
                </div>
            </div>
"""
    
    # SENSOR & COMMUNICATIONS ISSUES
    html += """
            <!-- SENSOR & COMMUNICATIONS ISSUES -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon">⚠️</div>
                    <div class="section-title">Sensor & Communications Issues</div>
                </div>
"""
    
    if sensor_health['totalIssues'] > 0:
        html += f"""
                <p style="margin-bottom: 16px;">Found <strong>{sensor_health['totalIssues']} issues</strong> affecting data quality and system visibility.</p>
                
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Severity</th>
                                <th>Meter</th>
                                <th>Issue Type</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
"""
        
        for issue in sensor_health['issues'][:20]:  # Limit to top 20
            severity_class = f"priority-{issue['severity']}"
            severity_icon = "🔴" if issue['severity'] == 'high' else "🟡" if issue['severity'] == 'medium' else "🟢"
            issue_type = issue['type'].replace('_', ' ').title()
            
            html += f"""
                            <tr>
                                <td class="{severity_class}">{severity_icon} {issue['severity'].upper()}</td>
                                <td>{issue['channelName']}</td>
                                <td>{issue_type}</td>
                                <td>{issue.get('details', 'See details in analytics')}</td>
                            </tr>
"""
        
        html += """
                        </tbody>
                    </table>
                </div>
"""
    else:
        html += """
                <div class="no-issues">
                    <div class="icon">✅</div>
                    <div>All sensors operating normally. No communication issues detected.</div>
                </div>
"""
    
    html += """
            </div>
"""
    
    # AFTER-HOURS ENERGY WASTE
    html += """
            <!-- AFTER-HOURS ENERGY WASTE -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon">🌙</div>
                    <div class="section-title">After-Hours Energy Waste</div>
                </div>
"""
    
    if after_hours['summary']['totalExcessKwh'] > 0:
        html += f"""
                <div class="alert-box danger">
                    <div class="title">⚠️ Excess after-hours energy consumption detected</div>
                    <div class="details">
                        <strong>{after_hours['summary']['totalExcessKwh']:.1f} kWh</strong> consumed during off-hours this week, 
                        costing <strong>${after_hours['summary']['totalExcessCost']:.2f}</strong>. 
                        If not addressed, this could cost <strong>${after_hours['summary']['estimatedAnnualCost']:,.2f}/year</strong>.
                    </div>
                </div>
"""
        
        if len(after_hours['topMeters']) > 0:
            html += """
                <h3 style="margin-bottom: 16px; color: #2c3e50;">Top Contributors</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Meter</th>
                                <th>Excess Energy</th>
                                <th>Weekly Cost</th>
                                <th>Annual Projection</th>
                                <th>% Above Baseline</th>
                            </tr>
                        </thead>
                        <tbody>
"""
            
            for meter in after_hours['topMeters'][:10]:  # Top 10
                html += f"""
                            <tr>
                                <td>{meter['channelName']}</td>
                                <td>{meter['excessKwh']:.1f} kWh</td>
                                <td>${meter['estimatedCost']:.2f}</td>
                                <td>${meter['estimatedCost'] * 52:.2f}</td>
                                <td>{meter['percentAboveBaseline']:.0f}%</td>
                            </tr>
"""
            
            html += """
                        </tbody>
                    </table>
                </div>
"""
    else:
        html += """
                <div class="no-issues">
                    <div class="icon">✅</div>
                    <div>After-hours energy consumption is within normal baseline parameters.</div>
                </div>
"""
    
    html += """
            </div>
"""
    
    # UNUSUAL SPIKES & ANOMALIES
    html += """
            <!-- UNUSUAL SPIKES & ANOMALIES -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon">📈</div>
                    <div class="section-title">Unusual Spikes & Anomalies</div>
                </div>
"""
    
    total_unusual = total_anomalies + total_spikes
    
    if total_unusual > 0:
        html += f"""
                <p style="margin-bottom: 16px;">Detected <strong>{total_unusual} unusual events</strong> this week ({total_anomalies} anomalies, {total_spikes} spikes).</p>
"""
        
        # Show top spikes
        if len(spikes['topSpikes']) > 0:
            html += """
                <h3 style="margin-bottom: 16px; color: #2c3e50;">Top Power Spikes</h3>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date/Time</th>
                                <th>Meter</th>
                                <th>Peak Power</th>
                                <th>Excess vs Baseline</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
"""
            
            for spike in spikes['topSpikes'][:10]:
                spike_time = datetime.fromisoformat(spike['timestamp'].replace('Z', '+00:00'))
                html += f"""
                            <tr>
                                <td>{spike_time.strftime('%b %d, %I:%M %p')}</td>
                                <td>{spike['channelName']}</td>
                                <td>{spike['peakPower']:.1f} kW</td>
                                <td class="priority-high">+{spike['excessKw']:.1f} kW ({spike['percentAboveThreshold']:.0f}%)</td>
                                <td>{spike['durationMinutes']} min</td>
                            </tr>
"""
            
            html += """
                        </tbody>
                    </table>
                </div>
"""
    else:
        html += """
                <div class="no-issues">
                    <div class="icon">✅</div>
                    <div>No unusual power spikes or anomalies detected this week.</div>
                </div>
"""
    
    html += """
            </div>
"""
    
    # QUICK WINS & RECOMMENDATIONS
    html += """
            <!-- QUICK WINS & RECOMMENDATIONS -->
            <div class="section">
                <div class="section-header">
                    <div class="section-icon">💡</div>
                    <div class="section-title">Quick Wins & Recommendations</div>
                </div>
"""
    
    if len(quick_wins) > 0:
        html += f"""
                <p style="margin-bottom: 24px;">Based on this week's data, we've identified <strong>{len(quick_wins)} actionable recommendations</strong> to improve energy efficiency and reduce costs.</p>
"""
        
        for i, win in enumerate(quick_wins, 1):
            priority = win['priority']
            title = win['title']
            impact = win['impact']
            
            # Format impact values
            weekly_kwh = f"{impact['weeklyKwh']:.0f} kWh" if isinstance(impact.get('weeklyKwh'), (int, float)) else impact.get('weeklyKwh', 'N/A')
            weekly_cost = f"${impact['weeklyCost']:.0f}" if isinstance(impact.get('weeklyCost'), (int, float)) else impact.get('weeklyCost', 'N/A')
            annual_cost = f"${impact['annualCost']:,.0f}" if isinstance(impact.get('annualCost'), (int, float)) else impact.get('annualCost', 'N/A')
            
            html += f"""
                <div class="recommendation-card {priority}">
                    <div class="recommendation-header">
                        <div class="recommendation-title">{i}. {title}</div>
                        <span class="recommendation-badge {priority}">{priority}</span>
                    </div>
                    
                    <div class="recommendation-impact">
                        <div class="impact-item">
                            <span class="impact-label">Weekly Impact</span>
                            <span class="impact-value">{weekly_kwh}</span>
                        </div>
                        <div class="impact-item">
                            <span class="impact-label">Weekly Savings</span>
                            <span class="impact-value">{weekly_cost}</span>
                        </div>
                        <div class="impact-item">
                            <span class="impact-label">Annual Potential</span>
                            <span class="impact-value">{annual_cost}</span>
                        </div>
                        <div class="impact-item">
                            <span class="impact-label">Effort</span>
                            <span class="impact-value">{win['effort']}</span>
                        </div>
                        <div class="impact-item">
                            <span class="impact-label">Owner</span>
                            <span class="impact-value">{win['owner']}</span>
                        </div>
                    </div>
                    
                    <div class="recommendation-actions">
                        <strong>Recommended Actions:</strong>
                        <ul>
"""
            
            for rec in win['recommendations']:
                html += f"""
                            <li>{rec}</li>
"""
            
            html += """
                        </ul>
                    </div>
                </div>
"""
    else:
        html += """
                <div class="no-issues">
                    <div class="icon">✅</div>
                    <div>System is operating efficiently. Continue monitoring for optimization opportunities.</div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="footer">
            <div class="logo">⚡ Argo Energy Solutions</div>
            <div>Automated Weekly Energy Report</div>
            <div style="margin-top: 8px;">
                Generated on """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w') as f:
        f.write(html)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate customer-ready weekly energy report'
    )
    parser.add_argument('--site', type=int, required=True, help='Site/Organization ID')
    parser.add_argument('--output', type=str, help='Output HTML file path')
    parser.add_argument('--json', action='store_true', help='Also save JSON report')
    
    args = parser.parse_args()
    
    print("🎯 Generating Customer-Ready Weekly Report\n")
    print(f"Site ID: {args.site}")
    
    # Get database connection
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        return 1
    
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        
        # Get report period
        period = get_last_complete_week('America/New_York')
        baseline = get_baseline_period(period['start'], 4)
        
        print(f"\n📅 Report Period: {period['start'].date()} to {period['end'].date()}")
        print(f"📊 Baseline: {baseline['start'].date()} to {baseline['end'].date()}")
        
        # Fetch data
        print("\n📡 Fetching data from database...")
        org_name, report_data = fetch_report_data(conn, args.site, period['start'], period['end'])
        _, baseline_data = fetch_report_data(conn, args.site, baseline['start'], baseline['end'])
        
        print(f"✅ Fetched {len(report_data)} channels")
        print(f"   Report: {sum(len(c['readings']) for c in report_data):,} readings")
        print(f"   Baseline: {sum(len(c['readings']) for c in baseline_data):,} readings")
        
        # Run analytics
        print("\n🔬 Running analytics...")
        config = DEFAULT_CONFIG
        
        sensor_health = analyze_sensor_health_for_site(report_data, config, 900)
        print(f"   ⚠️  Sensor health: {sensor_health['totalIssues']} issues")
        
        after_hours = analyze_after_hours_waste(report_data, baseline_data, config, 900)
        print(f"   🌙 After-hours waste: {after_hours['summary']['totalExcessKwh']:.1f} kWh")
        
        anomalies = analyze_anomalies(report_data, baseline_data, config, 900)
        print(f"   📊 Anomalies: {anomalies['totalAnomalyEvents']} events")
        
        spikes = analyze_spikes(report_data, baseline_data, config, 900)
        print(f"   📈 Spikes: {spikes['totalSpikeEvents']} events")
        
        analytics_results = {
            'sensorHealth': sensor_health,
            'afterHoursWaste': after_hours,
            'anomalies': anomalies,
            'spikes': spikes,
        }
        
        quick_wins = generate_quick_wins(analytics_results, config)
        print(f"   💡 Quick wins: {len(quick_wins)} recommendations")
        
        # Build complete data structure
        report_data_dict = {
            'metadata': {
                'organizationName': org_name,
                'organizationId': str(args.site),
                'generatedAt': datetime.now().isoformat(),
                'reportType': 'customer',
            },
            'period': {
                'start': period['start'].isoformat(),
                'end': period['end'].isoformat(),
                'label': format_date_range(period['start'], period['end']),
            },
            'sensorHealth': sensor_health,
            'afterHoursWaste': after_hours,
            'anomalies': anomalies,
            'spikes': spikes,
            'quickWins': quick_wins,
        }
        
        # Generate HTML report
        print("\n📄 Generating HTML report...")
        
        if args.output:
            output_path = args.output
        else:
            # Auto-generate filename
            date_str = period['start'].strftime('%Y%m%d')
            output_path = f"reports/weekly-report-{args.site}-{date_str}.html"
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else 'reports', exist_ok=True)
        
        html_path = generate_html_report(report_data_dict, org_name, report_data_dict['period'], output_path)
        
        print(f"✅ HTML report saved: {html_path}")
        
        # Save JSON if requested
        if args.json:
            json_path = output_path.replace('.html', '.json')
            with open(json_path, 'w') as f:
                json.dump(report_data_dict, f, indent=2, default=str)
            print(f"✅ JSON report saved: {json_path}")
        
        print("\n🎉 Report generation complete!")
        print(f"\n📧 Customer-ready report: {html_path}")
        print("   Ready to send to Facilities/Operations and Energy Manager")
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
