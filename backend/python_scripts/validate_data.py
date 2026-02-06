#!/usr/bin/env python3
"""
Data Validation Script for Argo Energy Solutions

Performs comprehensive checks on the Neon PostgreSQL database to ensure:
- Data completeness
- Data quality
- Schema integrity
- Anomaly detection
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DataValidator:
    """Comprehensive data validation for energy readings"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(self.db_url)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def run_all_checks(self) -> Dict:
        """Run all validation checks and return results"""
        print("=" * 70)
        print("🔍 DATA VALIDATION CHECKS")
        print("=" * 70)
        print()
        
        self.check_schema_integrity()
        self.check_data_completeness()
        self.check_data_quality()
        self.check_temporal_continuity()
        self.check_channel_health()
        self.check_value_ranges()
        self.check_ingestion_logs()
        
        return {
            'issues': self.issues,
            'warnings': self.warnings,
            'stats': self.stats,
            'passed': len(self.issues) == 0
        }
    
    def check_schema_integrity(self):
        """Verify database schema is correct"""
        print("📋 Checking Schema Integrity...")
        cur = self.conn.cursor()
        
        # Check required tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ('organizations', 'channels', 'readings', 'ingestion_logs')
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        required_tables = ['organizations', 'channels', 'readings', 'ingestion_logs']
        missing_tables = set(required_tables) - set(tables)
        
        if missing_tables:
            self.issues.append(f"Missing tables: {', '.join(missing_tables)}")
        else:
            print("   ✅ All required tables exist")
        
        # Check timestamp columns are TIMESTAMPTZ
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND column_name LIKE '%time%'
            AND data_type NOT IN ('timestamp with time zone', 'text')
        """)
        wrong_types = cur.fetchall()
        
        if wrong_types:
            for table, col, dtype in wrong_types:
                self.warnings.append(f"{table}.{col} is {dtype}, should be TIMESTAMPTZ")
        else:
            print("   ✅ Timestamp columns using TIMESTAMPTZ")
        
        cur.close()
        print()
    
    def check_data_completeness(self):
        """Check for data gaps and missing readings"""
        print("📊 Checking Data Completeness...")
        cur = self.conn.cursor()
        
        # Get date range
        cur.execute("""
            SELECT 
                DATE(MIN(timestamp)) as first_date,
                DATE(MAX(timestamp)) as last_date,
                COUNT(*) as total_readings,
                COUNT(DISTINCT channel_id) as total_channels,
                COUNT(DISTINCT DATE(timestamp)) as days_with_data
            FROM readings
        """)
        first_date, last_date, total_readings, total_channels, days_with_data = cur.fetchone()
        
        self.stats['first_date'] = str(first_date)
        self.stats['last_date'] = str(last_date)
        self.stats['total_readings'] = total_readings
        self.stats['total_channels'] = total_channels
        
        print(f"   📅 Date range: {first_date} to {last_date}")
        print(f"   📊 Total readings: {total_readings:,}")
        print(f"   🔌 Active channels: {total_channels}")
        
        # Calculate expected days
        if first_date and last_date:
            expected_days = (last_date - first_date).days + 1
            if days_with_data < expected_days:
                missing_days = expected_days - days_with_data
                self.warnings.append(f"{missing_days} days missing data out of {expected_days} expected")
                print(f"   ⚠️  {missing_days} days with missing data")
            else:
                print(f"   ✅ All {days_with_data} days have data")
        
        # Check for channels with no recent data (last 24 hours)
        cur.execute("""
            SELECT c.channel_id, c.channel_name
            FROM channels c
            LEFT JOIN (
                SELECT channel_id, MAX(timestamp) as last_reading
                FROM readings
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY channel_id
            ) r ON c.channel_id = r.channel_id
            WHERE r.last_reading IS NULL
        """)
        stale_channels = cur.fetchall()
        
        if stale_channels:
            self.warnings.append(f"{len(stale_channels)} channels have no data in last 24 hours")
            print(f"   ⚠️  {len(stale_channels)} channels with no recent data")
        else:
            print(f"   ✅ All channels have recent data (last 24h)")
        
        cur.close()
        print()
    
    def check_data_quality(self):
        """Check for data quality issues"""
        print("🔬 Checking Data Quality...")
        cur = self.conn.cursor()
        
        # Check for NULL values in key columns
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE energy_kwh IS NULL) as null_energy,
                COUNT(*) FILTER (WHERE power_kw IS NULL) as null_power,
                COUNT(*) FILTER (WHERE energy_kwh < 0) as negative_energy,
                COUNT(*) FILTER (WHERE power_kw < 0) as negative_power
            FROM readings
        """)
        null_energy, null_power, neg_energy, neg_power = cur.fetchone()
        
        total_issues = null_energy + null_power + neg_energy + neg_power
        
        if null_energy > 0:
            self.warnings.append(f"{null_energy:,} readings with NULL energy_kwh")
            print(f"   ⚠️  {null_energy:,} readings with NULL energy")
        
        if null_power > 0:
            self.warnings.append(f"{null_power:,} readings with NULL power_kw")
            print(f"   ⚠️  {null_power:,} readings with NULL power")
        
        if neg_energy > 0:
            self.issues.append(f"{neg_energy:,} readings with NEGATIVE energy_kwh")
            print(f"   ❌ {neg_energy:,} readings with NEGATIVE energy")
        
        if neg_power > 0:
            self.issues.append(f"{neg_power:,} readings with NEGATIVE power_kw")
            print(f"   ❌ {neg_power:,} readings with NEGATIVE power")
        
        if total_issues == 0:
            print(f"   ✅ No NULL or negative values found")
        
        # Check for duplicate readings
        cur.execute("""
            SELECT channel_id, timestamp, COUNT(*)
            FROM readings
            GROUP BY channel_id, timestamp
            HAVING COUNT(*) > 1
            LIMIT 5
        """)
        duplicates = cur.fetchall()
        
        if duplicates:
            dup_count = len(duplicates)
            self.issues.append(f"{dup_count} duplicate readings found")
            print(f"   ❌ {dup_count} duplicate readings detected")
        else:
            print(f"   ✅ No duplicate readings")
        
        # Check for extreme outliers
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE power_kw > 1000) as extreme_power,
                COUNT(*) FILTER (WHERE voltage_v > 600 OR voltage_v < 100) as extreme_voltage
            FROM readings
            WHERE power_kw IS NOT NULL OR voltage_v IS NOT NULL
        """)
        extreme_power, extreme_voltage = cur.fetchone()
        
        if extreme_power > 0:
            self.warnings.append(f"{extreme_power:,} readings with power > 1000 kW")
            print(f"   ⚠️  {extreme_power:,} readings with extremely high power (>1000 kW)")
        
        if extreme_voltage > 0:
            self.warnings.append(f"{extreme_voltage:,} readings with unusual voltage")
            print(f"   ⚠️  {extreme_voltage:,} readings with unusual voltage")
        
        if extreme_power == 0 and extreme_voltage == 0:
            print(f"   ✅ No extreme outliers detected")
        
        cur.close()
        print()
    
    def check_temporal_continuity(self):
        """Check for gaps in time series data"""
        print("⏰ Checking Temporal Continuity...")
        cur = self.conn.cursor()
        
        # Find large gaps (> 1 hour) in readings for each channel
        cur.execute("""
            WITH time_gaps AS (
                SELECT 
                    channel_id,
                    timestamp,
                    LAG(timestamp) OVER (PARTITION BY channel_id ORDER BY timestamp) as prev_timestamp,
                    timestamp - LAG(timestamp) OVER (PARTITION BY channel_id ORDER BY timestamp) as gap
                FROM readings
            )
            SELECT 
                channel_id,
                COUNT(*) as gap_count,
                MAX(gap) as largest_gap
            FROM time_gaps
            WHERE gap > INTERVAL '1 hour'
            GROUP BY channel_id
            ORDER BY gap_count DESC
            LIMIT 5
        """)
        gaps = cur.fetchall()
        
        if gaps:
            print(f"   ⚠️  Found data gaps > 1 hour in {len(gaps)} channels:")
            for channel_id, gap_count, largest_gap in gaps[:3]:
                print(f"      Channel {channel_id}: {gap_count} gaps (largest: {largest_gap})")
            self.warnings.append(f"Data gaps detected in {len(gaps)} channels")
        else:
            print(f"   ✅ No significant time gaps detected")
        
        cur.close()
        print()
    
    def check_channel_health(self):
        """Check individual channel health"""
        print("🔌 Checking Channel Health...")
        cur = self.conn.cursor()
        
        # Get channel statistics
        cur.execute("""
            SELECT 
                c.channel_id,
                c.channel_name,
                COUNT(r.timestamp) as reading_count,
                MIN(r.timestamp) as first_reading,
                MAX(r.timestamp) as last_reading,
                AVG(r.power_kw) as avg_power,
                STDDEV(r.power_kw) as stddev_power
            FROM channels c
            LEFT JOIN readings r ON c.channel_id = r.channel_id
            GROUP BY c.channel_id, c.channel_name
            ORDER BY reading_count DESC
        """)
        channels = cur.fetchall()
        
        self.stats['channel_count'] = len(channels)
        
        inactive_channels = [ch for ch in channels if ch[2] == 0]  # reading_count = 0
        
        if inactive_channels:
            print(f"   ⚠️  {len(inactive_channels)} channels have no readings")
            for ch in inactive_channels[:3]:
                print(f"      {ch[1]} (ID: {ch[0]})")
            self.warnings.append(f"{len(inactive_channels)} inactive channels")
        else:
            print(f"   ✅ All {len(channels)} channels have readings")
        
        # Check for channels with suspiciously low variance
        flat_channels = [ch for ch in channels if ch[2] > 100 and ch[6] and ch[6] < 0.01]
        
        if flat_channels:
            print(f"   ⚠️  {len(flat_channels)} channels with unusually flat readings")
            self.warnings.append(f"{len(flat_channels)} channels with flat readings (possible sensor issue)")
        
        cur.close()
        print()
    
    def check_value_ranges(self):
        """Check if values are within expected ranges"""
        print("📏 Checking Value Ranges...")
        cur = self.conn.cursor()
        
        # Get min/max/avg for key metrics
        cur.execute("""
            SELECT 
                MIN(power_kw) as min_power,
                MAX(power_kw) as max_power,
                AVG(power_kw) as avg_power,
                MIN(voltage_v) as min_voltage,
                MAX(voltage_v) as max_voltage,
                MIN(power_factor) as min_pf,
                MAX(power_factor) as max_pf
            FROM readings
            WHERE power_kw IS NOT NULL
        """)
        result = cur.fetchone()
        
        if result:
            min_power, max_power, avg_power, min_v, max_v, min_pf, max_pf = result
            
            print(f"   Power:   {min_power:.2f} kW → {max_power:.2f} kW (avg: {avg_power:.2f} kW)")
            
            if min_v and max_v:
                print(f"   Voltage: {min_v:.1f} V → {max_v:.1f} V")
                if min_v < 100 or max_v > 600:
                    self.warnings.append(f"Voltage outside typical range (100-600V)")
            
            if min_pf and max_pf:
                print(f"   Power Factor: {min_pf:.2f} → {max_pf:.2f}")
                if min_pf < -1 or max_pf > 1:
                    self.issues.append(f"Power factor outside valid range (-1 to 1)")
            
            # Store stats
            self.stats['min_power'] = float(min_power) if min_power else None
            self.stats['max_power'] = float(max_power) if max_power else None
            self.stats['avg_power'] = float(avg_power) if avg_power else None
        
        cur.close()
        print()
    
    def check_ingestion_logs(self):
        """Check ingestion logs for failures"""
        print("📝 Checking Ingestion Logs...")
        cur = self.conn.cursor()
        
        # Get recent ingestion stats
        cur.execute("""
            SELECT 
                COUNT(*) as total_runs,
                COUNT(*) FILTER (WHERE status = 'success') as successful,
                COUNT(*) FILTER (WHERE status = 'failure') as failed,
                MAX(end_time) as last_run
            FROM ingestion_logs
            WHERE end_time > NOW() - INTERVAL '7 days'
        """)
        total, success, failed, last_run = cur.fetchone()
        
        if total == 0:
            self.warnings.append("No ingestion logs in last 7 days")
            print(f"   ⚠️  No ingestion activity in last 7 days")
        else:
            print(f"   📊 Last 7 days: {total} runs, {success} successful, {failed} failed")
            print(f"   🕐 Last run: {last_run}")
            
            if failed > 0:
                # Get recent failures
                cur.execute("""
                    SELECT start_time, error_message
                    FROM ingestion_logs
                    WHERE status = 'failure'
                    AND end_time > NOW() - INTERVAL '7 days'
                    ORDER BY start_time DESC
                    LIMIT 3
                """)
                failures = cur.fetchall()
                
                print(f"   ⚠️  Recent failures:")
                for time, error in failures:
                    error_preview = error[:60] + '...' if error and len(error) > 60 else error
                    print(f"      {time}: {error_preview}")
                
                self.warnings.append(f"{failed} ingestion failures in last 7 days")
            else:
                print(f"   ✅ No failures in last 7 days")
        
        cur.close()
        print()
    
    def print_summary(self):
        """Print validation summary"""
        print("=" * 70)
        print("📋 VALIDATION SUMMARY")
        print("=" * 70)
        print()
        
        if len(self.issues) == 0 and len(self.warnings) == 0:
            print("✅ ALL CHECKS PASSED! Data quality is excellent.")
            print()
            return True
        
        if self.issues:
            print(f"❌ ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   • {issue}")
            print()
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        
        if len(self.issues) == 0:
            print("✅ No critical issues found. Warnings are informational.")
            return True
        else:
            print("❌ Critical issues detected. Please review and fix.")
            return False


def main():
    """Main execution"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    validator = DataValidator(db_url)
    
    try:
        validator.connect()
        validator.run_all_checks()
        passed = validator.print_summary()
        validator.close()
        
        # Exit with appropriate code
        sys.exit(0 if passed else 1)
    
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
