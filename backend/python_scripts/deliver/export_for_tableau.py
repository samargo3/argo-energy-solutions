#!/usr/bin/env python3
"""
Export Neon data to Excel/CSV for Tableau

All queries go through Layer 3 Business Views (v_readings_enriched,
v_meters) to respect Argo data governance — Deliver modules never
query raw tables directly.

Works without PostgreSQL driver - Tableau can read Excel/CSV natively.
"""

import os
import sys
import psycopg2
import csv
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env')


def export_to_csv(output_dir='exports/tableau'):
    """Export energy data to Tableau-friendly CSV files.

    All queries use v_readings_enriched (Layer 3 Business View).
    """
    
    print("🔄 Exporting data for Tableau...")
    print("=" * 70)
    
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Export Readings (last 90 days for performance)
    print("\n📊 Exporting readings (last 90 days)...")
    cur.execute("""
        SELECT 
            timestamp,
            meter_id   AS channel_id,
            meter_name AS channel_name,
            device_id,
            device_name,
            device_type,
            device_uuid,
            site_id    AS organization_id,
            site_name  AS organization_name,
            energy_kwh,
            power_kw,
            voltage_v,
            current_a,
            power_factor,
            DATE_PART('year', timestamp) as year,
            DATE_PART('month', timestamp) as month,
            DATE_PART('day', timestamp) as day,
            DATE_PART('hour', timestamp) as hour,
            DATE_PART('dow', timestamp) as day_of_week,
            CASE 
                WHEN DATE_PART('dow', timestamp) IN (0, 6) THEN 'Weekend'
                ELSE 'Weekday'
            END as day_type,
            CASE 
                WHEN DATE_PART('hour', timestamp) BETWEEN 8 AND 17 THEN 'Business Hours'
                ELSE 'After Hours'
            END as time_category
        FROM v_readings_enriched
        WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
        ORDER BY timestamp DESC
    """)
    
    readings_file = os.path.join(output_dir, 'tableau_readings.csv')
    with open(readings_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Timestamp', 'Channel ID', 'Channel Name', 'Device ID', 'Device Name',
            'Device Type', 'Device UUID', 'Organization ID', 'Organization',
            'Energy (kWh)', 'Power (kW)', 'Voltage (V)', 'Current (A)', 
            'Power Factor', 'Year', 'Month', 'Day', 'Hour', 
            'Day of Week', 'Day Type', 'Time Category'
        ])
        
        count = 0
        for row in cur.fetchall():
            writer.writerow(row)
            count += 1
    
    print(f"   ✅ Exported {count:,} readings to {readings_file}")
    
    # 2. Export Channel Summary
    print("\n📊 Exporting channel summary...")
    cur.execute("""
        SELECT 
            meter_id   AS channel_id,
            meter_name AS channel_name,
            device_id,
            device_name,
            device_type,
            device_uuid,
            site_id    AS organization_id,
            site_name  AS organization_name,
            COUNT(*)   AS reading_count,
            MIN(timestamp) as first_reading,
            MAX(timestamp) as last_reading,
            AVG(power_kw) as avg_power_kw,
            MAX(power_kw) as peak_power_kw,
            SUM(energy_kwh) as total_energy_kwh,
            AVG(voltage_v) as avg_voltage,
            AVG(power_factor) as avg_power_factor,
            SUM(energy_kwh) * 0.12 as estimated_cost_usd
        FROM v_readings_enriched
        WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY meter_id, meter_name, device_id, device_name,
                 device_type, device_uuid, site_id, site_name
        ORDER BY total_energy_kwh DESC NULLS LAST
    """)
    
    summary_file = os.path.join(output_dir, 'tableau_channel_summary.csv')
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Channel ID', 'Channel Name', 'Device ID', 'Device Name', 
            'Device Type', 'Device UUID', 'Organization ID', 'Organization',
            'Reading Count', 'First Reading', 'Last Reading',
            'Avg Power (kW)', 'Peak Power (kW)', 'Total Energy (kWh)',
            'Avg Voltage (V)', 'Avg Power Factor', 'Estimated Cost ($)'
        ])
        
        count = 0
        for row in cur.fetchall():
            writer.writerow(row)
            count += 1
    
    print(f"   ✅ Exported {count} channels to {summary_file}")
    
    # 3. Export Daily Aggregates (faster for Tableau)
    print("\n📊 Exporting daily aggregates...")
    cur.execute("""
        SELECT 
            DATE(timestamp) as date,
            meter_name AS channel_name,
            site_id    AS organization_id,
            site_name  AS organization_name,
            COUNT(*) as reading_count,
            AVG(power_kw) as avg_power_kw,
            MAX(power_kw) as peak_power_kw,
            SUM(energy_kwh) as daily_energy_kwh,
            AVG(voltage_v) as avg_voltage,
            AVG(power_factor) as avg_power_factor,
            SUM(energy_kwh) * 0.12 as daily_cost_usd
        FROM v_readings_enriched
        WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE(timestamp), meter_name, site_id, site_name
        ORDER BY date DESC, daily_energy_kwh DESC
    """)
    
    daily_file = os.path.join(output_dir, 'tableau_daily_summary.csv')
    with open(daily_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Date', 'Channel Name', 'Organization ID', 'Organization',
            'Reading Count', 'Avg Power (kW)', 'Peak Power (kW)', 
            'Daily Energy (kWh)', 'Avg Voltage (V)', 'Avg Power Factor',
            'Daily Cost ($)'
        ])
        
        count = 0
        for row in cur.fetchall():
            writer.writerow(row)
            count += 1
    
    print(f"   ✅ Exported {count:,} daily records to {daily_file}")
    
    # 4. Export Hourly Patterns (for time-of-day analysis)
    print("\n📊 Exporting hourly patterns...")
    cur.execute("""
        SELECT 
            DATE_PART('hour', timestamp) as hour_of_day,
            DATE_PART('dow', timestamp) as day_of_week,
            meter_name AS channel_name,
            AVG(power_kw) as avg_power_kw,
            COUNT(*) as reading_count
        FROM v_readings_enriched
        WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY hour_of_day, day_of_week, meter_name
        ORDER BY hour_of_day, day_of_week
    """)
    
    hourly_file = os.path.join(output_dir, 'tableau_hourly_patterns.csv')
    with open(hourly_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Hour of Day', 'Day of Week', 'Channel Name', 
            'Avg Power (kW)', 'Reading Count'
        ])
        
        count = 0
        for row in cur.fetchall():
            writer.writerow(row)
            count += 1
    
    print(f"   ✅ Exported {count:,} hourly patterns to {hourly_file}")
    
    cur.close()
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ EXPORT COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Files created in '{output_dir}/' folder:")
    print(f"   1. tableau_readings.csv         - Detailed readings (last 90 days)")
    print(f"   2. tableau_channel_summary.csv  - Channel statistics")
    print(f"   3. tableau_daily_summary.csv    - Daily aggregates")
    print(f"   4. tableau_hourly_patterns.csv  - Hour-of-day patterns")
    print("\n📊 How to use in Tableau:")
    print("   1. Open Tableau Desktop")
    print("   2. Connect → Text File")
    print("   3. Select all 4 CSV files")
    print("   4. Join tables as needed")
    print("   5. Start building dashboards!")
    print("\n💡 Tip: Start with 'tableau_daily_summary.csv' for fastest performance")
    print()


def export_custom_date_range(start_date, end_date, output_dir='exports/tableau'):
    """Export specific date range via v_readings_enriched (Layer 3)."""
    
    print(f"🔄 Exporting data from {start_date} to {end_date}...")
    
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    os.makedirs(output_dir, exist_ok=True)
    
    cur.execute("""
        SELECT 
            timestamp,
            meter_id   AS channel_id,
            meter_name AS channel_name,
            device_id,
            device_name,
            device_type,
            device_uuid,
            site_id    AS organization_id,
            site_name  AS organization_name,
            energy_kwh,
            power_kw,
            voltage_v,
            power_factor
        FROM v_readings_enriched
        WHERE timestamp >= %s AND timestamp <= %s
        ORDER BY timestamp
    """, (start_date, end_date))
    
    filename = f'tableau_custom_{start_date}_{end_date}.csv'
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Timestamp', 'Channel ID', 'Channel Name', 'Device ID', 'Device Name',
            'Device Type', 'Device UUID', 'Organization ID', 'Organization',
            'Energy (kWh)', 'Power (kW)', 'Voltage (V)', 'Power Factor'
        ])
        
        count = 0
        for row in cur.fetchall():
            writer.writerow(row)
            count += 1
    
    print(f"✅ Exported {count:,} readings to {filepath}")
    
    cur.close()
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--custom':
        # Custom date range
        if len(sys.argv) < 4:
            print("Usage: python export_for_tableau.py --custom START_DATE END_DATE")
            print("Example: python export_for_tableau.py --custom 2025-11-01 2025-12-31")
            sys.exit(1)
        
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        export_custom_date_range(start_date, end_date)
    else:
        # Default: last 90 days
        export_to_csv()
