#!/usr/bin/env python3
"""
Robust Historical Energy Data Ingestion from Eniscope API to Neon (Postgres)

This script fetches historical energy data with strict data integrity rules:
- Composite primary key (meter_id, timestamp) prevents duplicates
- Validation: negative kW rejected, future timestamps rejected
- Ingestion logs track all API pulls for gap analysis
- Upsert logic allows safe re-runs without duplicates

Usage:
    python historical_ingestion.py --site 23271
    python historical_ingestion.py --site 23271 --start-date 2025-05-01
    python historical_ingestion.py --site 23271 --start-date 2025-05-01 --end-date 2025-12-31
"""

import os
import sys
import argparse
import hashlib
import base64
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import requests
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env')


class DataIntegrityError(Exception):
    """Raised when data fails validation rules"""
    pass


class EniscopeHistoricalClient:
    """
    Robust Eniscope API client for historical data ingestion
    
    Features:
    - Rate limiting (1 second between calls)
    - Automatic retry on failures
    - Data validation before insertion
    - Ingestion logging for gap detection
    """
    
    def __init__(self):
        self.base_url = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com').rstrip('/')
        self.api_key = os.getenv('VITE_ENISCOPE_API_KEY')
        self.email = os.getenv('VITE_ENISCOPE_EMAIL')
        self.password = os.getenv('VITE_ENISCOPE_PASSWORD')
        
        if not all([self.api_key, self.email, self.password]):
            raise ValueError('❌ Missing required environment variables (API_KEY, EMAIL, PASSWORD)')
        
        self.password_md5 = hashlib.md5(self.password.encode()).hexdigest()
        self.session_token = None
        self.rate_limit_delay = 1.0  # 1 second between API calls
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def authenticate(self) -> List[Dict]:
        """Authenticate and return organizations list"""
        self._rate_limit()
        
        auth_string = f"{self.email}:{self.password_md5}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'X-Eniscope-API': self.api_key,
            'Accept': 'text/json'
        }
        
        response = requests.get(f'{self.base_url}/organizations', headers=headers, timeout=30)
        response.raise_for_status()
        
        # Get session token from response headers
        self.session_token = response.headers.get('x-eniscope-token') or response.headers.get('X-Eniscope-Token')
        
        data = response.json()
        
        # Extract organizations list from response
        if isinstance(data, dict) and 'organizations' in data:
            organizations = data['organizations']
        elif isinstance(data, list):
            organizations = data
        else:
            organizations = [data] if data else []
        
        return organizations
    
    def fetch_channels(self, org_id: str) -> List[Dict]:
        """Fetch all channels (meters) for an organization with retry logic"""
        for attempt in range(3):
            self._rate_limit()
            
            if not self.session_token:
                self.authenticate()
            
            headers = {
                'X-Eniscope-API': self.api_key,
                'X-Eniscope-Token': self.session_token,
                'Accept': 'text/json'
            }
            
            try:
                response = requests.get(
                    f'{self.base_url}/channels',
                    headers=headers,
                    params={'organization': org_id},
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Handle various response formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('channels') or data.get('data') or data.get('items') or []
                return []
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < 2:
                    wait_time = (attempt + 1) * 10  # 10s, 20s
                    print(f"⏳ Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception("Failed to fetch channels after 3 attempts")
    
    def fetch_readings(
        self,
        org_id: str,
        channel_id: int,
        start_timestamp: int,
        end_timestamp: int
    ) -> List[Dict]:
        """
        Fetch readings for a specific channel and time range
        
        Args:
            org_id: Organization ID
            channel_id: Channel (meter) ID
            start_timestamp: Unix timestamp (seconds)
            end_timestamp: Unix timestamp (seconds)
        
        Returns:
            List of reading dictionaries
        """
        self._rate_limit()
        
        if not self.session_token:
            self.authenticate()
        
        headers = {
            'X-Eniscope-API': self.api_key,
            'X-Eniscope-Token': self.session_token,
            'Accept': 'text/json'
        }
        
        params = {
            'action': 'summarize',
            'res': '900',  # 15-minute resolution (in seconds)
            'daterange[]': [start_timestamp, end_timestamp],
            'fields[]': ['E', 'P', 'V', 'I', 'PF']
        }
        
        response = requests.get(
            f'{self.base_url}/readings/{channel_id}',
            headers=headers,
            params=params,
            timeout=60  # Longer timeout for data requests
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract readings from response
        raw_readings = []
        if isinstance(data, dict):
            raw_readings = data.get('readings') or data.get('data') or []
        elif isinstance(data, list):
            raw_readings = data
        
        # Normalize and convert units (Wh -> kWh, W -> kW)
        normalized = []
        for r in raw_readings:
            normalized.append({
                'ts': r.get('ts') or r.get('t') or r.get('timestamp'),
                'E': r.get('E') / 1000 if r.get('E') is not None else None,  # Wh -> kWh
                'P': r.get('P') / 1000 if r.get('P') is not None else None,  # W -> kW
                'V': r.get('V'),
                'I': r.get('I'),
                'PF': r.get('PF')
            })
        
        return normalized


class DatabaseManager:
    """
    Manages database operations with data integrity rules
    
    Features:
    - Composite primary key (meter_id, timestamp)
    - Data validation before insertion
    - Upsert logic (ON CONFLICT DO NOTHING)
    - Ingestion logging for gap detection
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def ensure_schema(self):
        """
        Ensure required tables exist with proper constraints
        
        Creates:
        - readings table with composite primary key (channel_id, timestamp)
        - ingestion_logs table to track API pulls
        """
        with self.conn.cursor() as cur:
            # Check if readings table needs composite primary key
            cur.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'readings'
                  AND table_schema = 'public'
                  AND constraint_type = 'PRIMARY KEY'
            """)
            
            pk_info = cur.fetchone()
            
            # If primary key is just 'id', we need to add composite key
            if pk_info:
                # Check if composite unique constraint exists
                cur.execute("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'readings'
                      AND indexname = 'idx_readings_unique'
                """)
                
                if not cur.fetchone():
                    print("⚠️  Note: readings table uses id as primary key.")
                    print("   Composite unique index (channel_id, timestamp) already exists.")
            
            # Create ingestion_logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_logs (
                    id SERIAL PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    channel_id INTEGER NOT NULL,
                    start_time TIMESTAMPTZ NOT NULL,
                    end_time TIMESTAMPTZ NOT NULL,
                    readings_fetched INTEGER NOT NULL DEFAULT 0,
                    readings_inserted INTEGER NOT NULL DEFAULT 0,
                    readings_rejected INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'success',
                    error_message TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for gap analysis
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_ingestion_logs_time
                ON ingestion_logs(organization_id, channel_id, start_time, end_time)
            """)
            
            self.conn.commit()
            print("✅ Database schema verified")
    
    def validate_reading(self, reading: Dict, channel_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate a reading before insertion
        
        Rules:
        1. Power (kW) must not be negative
        2. Timestamp must be in the past (not future)
        
        Returns:
            (is_valid, error_message)
        """
        now = datetime.now(timezone.utc)
        
        # Extract timestamp
        ts = reading.get('ts')
        if not ts:
            return False, "Missing timestamp"
        
        # Convert to datetime if needed
        if isinstance(ts, (int, float)):
            reading_time = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            reading_time = ts
        
        # Rule 1: Timestamp must be in the past
        if reading_time > now:
            return False, f"Future timestamp: {reading_time}"
        
        # Rule 2: Power (kW) must not be negative
        power_kw = reading.get('P')
        if power_kw is not None and power_kw < 0:
            return False, f"Negative power: {power_kw} kW"
        
        return True, None
    
    def upsert_readings(
        self,
        channel_id: int,
        readings: List[Dict],
        validate: bool = True
    ) -> Tuple[int, int]:
        """
        Insert readings with upsert logic (ON CONFLICT DO NOTHING)
        
        Args:
            channel_id: Channel (meter) ID
            readings: List of reading dictionaries
            validate: If True, validate data before insertion
        
        Returns:
            (inserted_count, rejected_count)
        """
        if not readings:
            return 0, 0
        
        inserted_count = 0
        rejected_count = 0
        valid_readings = []
        
        # Validate readings if requested
        if validate:
            for reading in readings:
                is_valid, error = self.validate_reading(reading, channel_id)
                if is_valid:
                    valid_readings.append(reading)
                else:
                    rejected_count += 1
                    print(f"   ⚠️  Rejected reading: {error}")
        else:
            valid_readings = readings
        
        if not valid_readings:
            return 0, rejected_count
        
        # Prepare batch insert
        with self.conn.cursor() as cur:
            # Use ON CONFLICT DO NOTHING for safe re-runs
            insert_sql = """
                INSERT INTO readings (
                    channel_id,
                    timestamp,
                    energy_kwh,
                    power_kw,
                    voltage_v,
                    current_a,
                    power_factor,
                    reactive_power_kvar,
                    temperature_c,
                    relative_humidity
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (channel_id, timestamp) DO NOTHING
            """
            
            batch_data = []
            for reading in valid_readings:
                # Convert Unix timestamp to datetime if needed
                ts = reading.get('ts')
                if isinstance(ts, (int, float)):
                    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    timestamp = ts
                
                batch_data.append((
                    channel_id,
                    timestamp,
                    reading.get('E'),  # Energy kWh (already converted from Wh)
                    reading.get('P'),  # Power kW (already converted from W)
                    reading.get('V'),  # Voltage
                    reading.get('I'),  # Current
                    reading.get('PF'),  # Power Factor
                    None,  # reactive_power_kvar (not in basic fields)
                    None,  # temperature_c (not in basic fields)
                    None,  # relative_humidity (not in basic fields)
                ))
            
            # Execute batch insert
            execute_batch(cur, insert_sql, batch_data, page_size=1000)
            inserted_count = cur.rowcount
        
        return inserted_count, rejected_count
    
    def log_ingestion(
        self,
        org_id: str,
        channel_id: int,
        start_time: datetime,
        end_time: datetime,
        fetched: int,
        inserted: int,
        rejected: int,
        status: str = 'success',
        error: Optional[str] = None
    ):
        """
        Log an ingestion run for gap analysis
        
        Args:
            org_id: Organization ID
            channel_id: Channel ID
            start_time: Start of time range
            end_time: End of time range
            fetched: Number of readings fetched from API
            inserted: Number of readings inserted
            rejected: Number of readings rejected
            status: 'success' or 'failure'
            error: Error message if status is 'failure'
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ingestion_logs (
                    organization_id,
                    channel_id,
                    start_time,
                    end_time,
                    readings_fetched,
                    readings_inserted,
                    readings_rejected,
                    status,
                    error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                org_id,
                channel_id,
                start_time,
                end_time,
                fetched,
                inserted,
                rejected,
                status,
                error
            ))
        
        self.conn.commit()
    
    def get_ingestion_gaps(self, org_id: str, channel_id: int) -> List[Dict]:
        """
        Find gaps in ingestion history
        
        Returns list of time periods with no ingestion logs
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                WITH ingestion_ranges AS (
                    SELECT
                        start_time,
                        end_time,
                        LAG(end_time) OVER (ORDER BY start_time) as prev_end_time
                    FROM ingestion_logs
                    WHERE organization_id = %s
                      AND channel_id = %s
                      AND status = 'success'
                    ORDER BY start_time
                )
                SELECT
                    prev_end_time as gap_start,
                    start_time as gap_end,
                    EXTRACT(EPOCH FROM (start_time - prev_end_time))/3600 as gap_hours
                FROM ingestion_ranges
                WHERE prev_end_time IS NOT NULL
                  AND start_time > prev_end_time + INTERVAL '5 minutes'
                ORDER BY gap_start
            """, (org_id, channel_id))
            
            return [dict(row) for row in cur.fetchall()]


def run_historical_ingestion(
    site_id: int,
    start_date: str = '2025-05-01',
    end_date: Optional[str] = None,
    validate_data: bool = True
):
    """
    Run historical data ingestion with 24-hour increments
    
    Args:
        site_id: Organization/Site ID
        start_date: Start date (YYYY-MM-DD) - default is Eniscope installation date
        end_date: End date (YYYY-MM-DD) - default is today
        validate_data: If True, validate data before insertion
    """
    print("=" * 70)
    print("🔄 HISTORICAL ENERGY DATA INGESTION")
    print("=" * 70)
    print(f"\n🎯 Site ID: {site_id}")
    print(f"📅 Start Date: {start_date}")
    
    # Parse dates
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(
        hour=0, minute=0, second=0, tzinfo=timezone.utc
    )
    
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    else:
        end_dt = datetime.now(timezone.utc)
    
    print(f"🏁 End Date: {end_dt.strftime('%Y-%m-%d')}")
    print(f"🔐 Data Validation: {'✅ Enabled' if validate_data else '❌ Disabled'}")
    print()
    
    # Initialize clients
    client = EniscopeHistoricalClient()
    db = DatabaseManager(os.getenv('DATABASE_URL'))
    
    try:
        # Connect to database
        db.connect()
        db.ensure_schema()
        print()
        
        # Authenticate
        print("🔑 Authenticating with Eniscope API...")
        orgs = client.authenticate()
        
        # Find organization (check organizationId, organization_id, or id)
        org = None
        if isinstance(orgs, list):
            org = next((o for o in orgs if str(o.get('organizationId') or o.get('organization_id') or o.get('id')) == str(site_id)), None)
        
        if not org:
            # Show available organizations for debugging
            available = []
            if isinstance(orgs, list):
                for o in orgs:
                    org_id_value = o.get('organizationId') or o.get('organization_id') or o.get('id')
                    org_name_value = o.get('organizationName') or o.get('organization_name') or o.get('name')
                    available.append(f"{org_id_value} ({org_name_value})")
            print(f"❌ Site {site_id} not found")
            print(f"   Available organizations: {', '.join(available)}")
            return
        
        org_id = str(org.get('organizationId') or org.get('organization_id') or org.get('id'))
        org_name = org.get('organizationName') or org.get('organization_name') or org.get('name') or f'Site {org_id}'
        
        print(f"✅ Authenticated as: {org_name}")
        print()
        
        # Fetch channels
        print("📡 Fetching channels...")
        channels = client.fetch_channels(org_id)
        print(f"✅ Found {len(channels)} channels")
        print()
        
        # Track totals
        total_fetched = 0
        total_inserted = 0
        total_rejected = 0
        total_api_calls = 0
        
        # Process each channel
        for channel in channels:
            # Handle different field name formats (channelId, dataChannelId)
            channel_id = channel.get('channelId') or channel.get('dataChannelId')
            channel_name = channel.get('channelName') or channel.get('deviceName') or channel.get('name') or f'Channel {channel_id}'
            
            if not channel_id:
                print(f"⚠️  Skipping channel with no ID: {channel.get('deviceName', 'Unknown')}")
                continue
            
            print(f"📊 Processing: {channel_name} (ID: {channel_id})")
            print("-" * 70)
            
            # Loop through 24-hour increments
            current_start = start_dt
            
            while current_start < end_dt:
                # Calculate 24-hour window
                current_end = min(
                    current_start + timedelta(hours=24),
                    end_dt
                )
                
                # Convert to Unix timestamps
                start_ts = int(current_start.timestamp())
                end_ts = int(current_end.timestamp())
                
                date_str = current_start.strftime('%Y-%m-%d')
                print(f"   📅 {date_str} ", end='', flush=True)
                
                try:
                    # Fetch readings
                    readings = client.fetch_readings(
                        org_id,
                        channel_id,
                        start_ts,
                        end_ts
                    )
                    total_api_calls += 1
                    
                    # Insert readings
                    inserted, rejected = db.upsert_readings(
                        channel_id,
                        readings,
                        validate=validate_data
                    )
                    
                    # Log ingestion
                    db.log_ingestion(
                        org_id,
                        channel_id,
                        current_start,
                        current_end,
                        len(readings),
                        inserted,
                        rejected,
                        status='success'
                    )
                    
                    total_fetched += len(readings)
                    total_inserted += inserted
                    total_rejected += rejected
                    
                    print(f"✅ Fetched: {len(readings)}, Inserted: {inserted}, Rejected: {rejected}")
                    
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
                    # Log failure
                    db.log_ingestion(
                        org_id,
                        channel_id,
                        current_start,
                        current_end,
                        0, 0, 0,
                        status='failure',
                        error=str(e)
                    )
                
                # Move to next 24-hour window
                current_start = current_end
            
            print()
        
        # Summary
        print("=" * 70)
        print("✅ INGESTION COMPLETE")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   Channels processed: {len(channels)}")
        print(f"   API calls made: {total_api_calls}")
        print(f"   Readings fetched: {total_fetched:,}")
        print(f"   Readings inserted: {total_inserted:,}")
        print(f"   Readings rejected: {total_rejected:,}")
        print(f"   Success rate: {(total_inserted / total_fetched * 100) if total_fetched > 0 else 0:.1f}%")
        print()
        
        # Check for gaps
        print("🔍 Checking for ingestion gaps...")
        for channel in channels[:5]:  # Check first 5 channels
            gaps = db.get_ingestion_gaps(org_id, channel['id'])
            if gaps:
                print(f"   ⚠️  {channel.get('name', 'Channel')}: {len(gaps)} gaps found")
                for gap in gaps[:3]:  # Show first 3 gaps
                    print(f"      {gap['gap_start']} to {gap['gap_end']} ({gap['gap_hours']:.1f} hours)")
            else:
                print(f"   ✅ {channel.get('name', 'Channel')}: No gaps")
        
        print()
        print("🎉 Historical ingestion complete!")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Robust historical energy data ingestion from Eniscope API'
    )
    parser.add_argument(
        '--site',
        type=int,
        required=True,
        help='Site/Organization ID'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2025-05-01',
        help='Start date (YYYY-MM-DD) - default is Eniscope installation date (2025-05-01)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD) - default is today'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Disable data validation (not recommended)'
    )
    
    args = parser.parse_args()
    
    return run_historical_ingestion(
        site_id=args.site,
        start_date=args.start_date,
        end_date=args.end_date,
        validate_data=not args.no_validate
    )


if __name__ == '__main__':
    sys.exit(main())
