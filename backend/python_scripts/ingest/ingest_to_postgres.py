#!/usr/bin/env python3
"""
Eniscope Data Ingestion to PostgreSQL (Neon)

Pulls data from Eniscope API and stores it in PostgreSQL database.

Usage:
    # Last N days (default)
    python ingest_to_postgres.py --site 23271 --days 90

    # Exact date window (for backfill)
    python ingest_to_postgres.py --site 23271 --start-date 2025-04-01 --end-date 2025-11-30
"""

import os
import sys
import argparse
import base64
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import requests
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
# Override=True ensures we reload the latest .env (matches debug script)
load_dotenv(_PROJECT_ROOT / '.env', override=True)

# Default resolution in seconds (15 min). Override via ENISCOPE_RESOLUTION or --resolution.
DEFAULT_RESOLUTION = int(os.getenv('ENISCOPE_RESOLUTION', '900'))


def _load_password_safely() -> str:
    """Load password from env; reject placeholders (e.g. $$$) to avoid 403/auth issues."""
    raw = os.getenv('VITE_ENISCOPE_PASSWORD')
    if not raw or not raw.strip():
        raise ValueError(
            'VITE_ENISCOPE_PASSWORD is missing. Set it in .env (no credentials in code).'
        )
    if '$$$' in raw:
        raise ValueError(
            'VITE_ENISCOPE_PASSWORD looks like a placeholder (contains $$$). '
            'Replace with the real value in .env.'
        )
    return raw.strip()


class EniscopeClient:
    """Client for Eniscope API with Basic Auth, stealth headers, and rate limiting."""
    
    # Stealth headers to avoid 403 WAF blocking (same as debug_raw_fetch.py)
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )
    
    def __init__(self):
        self.base_url = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com').rstrip('/')
        self.api_key = os.getenv('VITE_ENISCOPE_API_KEY')
        self.email = os.getenv('VITE_ENISCOPE_EMAIL')
        self.password = _load_password_safely()
        
        if not all([self.api_key, self.email]):
            raise ValueError('Missing required env: VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL')
        
        self.password_md5 = hashlib.md5(self.password.encode()).hexdigest()
        self.session_token = None
        self.cached_organizations = None
        
        # Basic Auth header: base64("username:md5password")
        auth_str = f"{self.email}:{self.password_md5}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        
        # Every request: stealth headers + Basic Auth (matches curl from support)
        self._headers = {
            'User-Agent': self.USER_AGENT,
            'X-Eniscope-API': self.api_key,
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json',
        }
    
    def authenticate(self) -> List[Dict]:
        """Authenticate and return organizations list."""
        if self.cached_organizations:
            return self.cached_organizations
        
        response = requests.get(
            f'{self.base_url}/organizations',
            headers=self._headers,
            timeout=30,
        )
        response.raise_for_status()
        
        self.session_token = response.headers.get('x-eniscope-token') or response.headers.get('X-Eniscope-Token')
        self.cached_organizations = response.json()
        
        return self.cached_organizations
    
    def _make_request_with_retry(self, url: str, params: Dict = None, retries: int = 3) -> requests.Response:
        """Make request with Basic Auth header and exponential backoff."""
        for attempt in range(retries):
            try:
                response = requests.get(
                    url,
                    params=params or {},
                    headers=self._headers,
                    timeout=30,
                )
                response.raise_for_status()
                return response
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and attempt < retries - 1:
                    delay = 2 ** (attempt + 3)  # 8s, 16s, 32s
                    print(f"\n   Rate limited. Waiting {delay}s before retry...")
                    time.sleep(delay)
                elif e.response.status_code in (401, 419) and attempt < retries - 1:
                    self.session_token = None
                    self.authenticate()
                else:
                    raise
        
        raise Exception(f"Failed after {retries} retries")
    
    def get_channels(self, organization_id: str) -> List[Dict]:
        """Get channels for an organization."""
        response = self._make_request_with_retry(
            f'{self.base_url}/channels',
            params={'organization': organization_id}
        )
        
        data = response.json()
        
        # Handle various response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('channels') or data.get('data') or data.get('items') or []
        return []
    
    def get_readings(self, channel_id: int, start_date: str, end_date: str, 
                     fields: List[str] = None, resolution: int = None) -> List[Dict]:
        """Get readings for a channel. Resolution default 15 min (900s), configurable."""
        if resolution is None:
            resolution = DEFAULT_RESOLUTION
        if fields is None:
            fields = ['E', 'P', 'V', 'I', 'PF']
        
        # Convert dates to Unix timestamps
        start_ts = int(datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp())
        end_ts = int(datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp())
        
        params = {
            'action': 'summarize',
            'res': str(resolution),
            'daterange[]': [start_ts, end_ts],
            'fields[]': fields
        }
        
        response = self._make_request_with_retry(
            f'{self.base_url}/readings/{channel_id}',
            params=params
        )
        
        data = response.json()
        
        # Extract readings array
        readings = []
        if isinstance(data, list):
            readings = data
        elif isinstance(data, dict):
            readings = (data.get('records') or data.get('data') or 
                       data.get('result') or data.get('readings') or [])
        
        # Normalize and convert units (Wh -> kWh, W -> kW)
        normalized = []
        for r in readings:
            normalized.append({
                'timestamp': r.get('ts') or r.get('t') or r.get('timestamp'),
                'energy_kwh': r.get('E') / 1000 if r.get('E') is not None else None,
                'power_kw': r.get('P') / 1000 if r.get('P') is not None else None,
                'voltage_v': r.get('V'),
                'current_a': r.get('I'),
                'power_factor': r.get('PF')
            })
        
        return normalized


class PostgresDB:
    """PostgreSQL database operations."""
    
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self.conn.autocommit = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
    
    def upsert_organization(self, org_id: str, org_name: str):
        """Insert or update organization."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO organizations (organization_id, organization_name, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (organization_id) 
                DO UPDATE SET organization_name = EXCLUDED.organization_name, updated_at = NOW()
            """, (org_id, org_name))
        self.conn.commit()
    
    def upsert_device(self, device_id: int, device_name: str, device_type: str, 
                     uuid: str, org_id: str) -> bool:
        """Insert or update device."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO devices (device_id, device_name, device_type, 
                                       serial_number, organization_id, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (device_id)
                    DO UPDATE SET 
                        device_name = EXCLUDED.device_name,
                        device_type = EXCLUDED.device_type,
                        serial_number = EXCLUDED.serial_number,
                        updated_at = NOW()
                """, (device_id, device_name, device_type, uuid, org_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"   ⚠️  Error storing device {device_id}: {e}")
            self.conn.rollback()
            return False
    
    def upsert_channel(self, channel_id: int, channel_name: str, org_id: str, 
                      device_id: int = None) -> bool:
        """Insert or update channel."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO channels (channel_id, channel_name, organization_id, 
                                        device_id, channel_type, unit, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (channel_id)
                    DO UPDATE SET 
                        channel_name = EXCLUDED.channel_name,
                        device_id = EXCLUDED.device_id,
                        updated_at = NOW()
                """, (channel_id, channel_name, org_id, device_id, 'energy', 'kWh'))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"   ⚠️  Error storing channel {channel_id}: {e}")
            self.conn.rollback()
            return False
    
    def insert_readings(self, channel_id: int, readings: List[Dict]) -> int:
        """Batch insert readings."""
        if not readings:
            return 0
        
        inserted = 0
        batch_size = 1000
        
        with self.conn.cursor() as cur:
            for i in range(0, len(readings), batch_size):
                batch = readings[i:i + batch_size]
                
                # Filter out readings with null timestamps
                valid_batch = [
                    (channel_id,
                     datetime.fromtimestamp(r['timestamp']) if isinstance(r['timestamp'], (int, float)) 
                     else datetime.fromisoformat(str(r['timestamp']).replace('Z', '+00:00')),
                     r['energy_kwh'],
                     r['power_kw'],
                     r['voltage_v'],
                     r['current_a'],
                     r['power_factor'])
                    for r in batch
                    if r.get('timestamp') is not None
                ]
                
                if not valid_batch:
                    continue
                
                try:
                    execute_batch(cur, """
                        INSERT INTO readings (channel_id, timestamp, energy_kwh, power_kw,
                                            voltage_v, current_a, power_factor)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (channel_id, timestamp) DO NOTHING
                    """, valid_batch)
                    
                    inserted += cur.rowcount
                except Exception as e:
                    print(f"   Error inserting batch: {e}")
                    self.conn.rollback()
                    continue
        
        self.conn.commit()
        return inserted
    
    def get_total_readings(self) -> int:
        """Get total number of readings in database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM readings")
            return cur.fetchone()[0]


def ingest_data(
    site_id: str,
    days: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    resolution: Optional[int] = None,
):
    """Main ingestion function. Use either (start_date, end_date) or days."""
    res = resolution if resolution is not None else DEFAULT_RESOLUTION
    use_explicit_range = start_date is not None and end_date is not None

    if use_explicit_range:
        if start_date > end_date:
            print("❌ --start-date must be on or before --end-date")
            sys.exit(1)
        num_days = (end_date - start_date).days + 1
        range_label = f"{start_date} → {end_date} ({num_days} days)"
    else:
        days = days if days is not None else 90
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        start_date = start_dt.date()
        end_date = end_dt.date()
        range_label = f"last {days} days (→ {end_date})"

    print("🌐 Eniscope → PostgreSQL Data Ingestion\n")
    print(f"📊 Site ID: {site_id}")
    print(f"📅 Range: {range_label}")
    print(f"📐 Resolution: {res}s\n")

    # Check environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        sys.exit(1)

    # Initialize clients
    client = EniscopeClient()

    try:
        # Authenticate
        orgs = client.authenticate()
        print("✅ Authenticated with Eniscope\n")

        # Get organization
        print("📋 Fetching organization...")
        org = None
        if isinstance(orgs, list):
            org = next((o for o in orgs if str(o.get('organization_id') or o.get('id')) == site_id),
                      orgs[0] if orgs else None)
        elif isinstance(orgs, dict):
            orgs_list = orgs.get('organizations') or orgs.get('data') or [orgs]
            org = next((o for o in orgs_list if str(o.get('organization_id') or o.get('id')) == site_id),
                      orgs_list[0] if orgs_list else None)

        if not org:
            print(f"❌ Organization {site_id} not found")
            sys.exit(1)

        org_name = org.get('organization_name') or org.get('name') or f"Site {site_id}"
        print(f"✅ Organization: {org_name}\n")

        # Connect to database
        with PostgresDB(db_url) as db:
            print("✅ Connected to PostgreSQL\n")

            # Store organization
            db.upsert_organization(site_id, org_name)

            # Get channels
            print("🔌 Fetching channels...")
            channels = client.get_channels(site_id)
            print(f"✅ Found {len(channels)} channels\n")

            # Store channels and devices
            valid_channels = []
            for channel in channels:
                channel_id = channel.get('channelId') or channel.get('dataChannelId')
                channel_name = channel.get('channelName') or channel.get('name') or f"Channel {channel_id}"

                if not channel_id:
                    continue

                # Extract device information
                device_id = channel.get('deviceId')
                device_name = channel.get('deviceName')
                device_type = channel.get('deviceTypeName') or channel.get('deviceType')
                uuid = channel.get('uuId') or channel.get('uuid')

                # Store device if present
                if device_id:
                    db.upsert_device(
                        int(device_id),
                        device_name or f"Device {device_id}",
                        device_type or 'Unknown',
                        uuid or '',
                        site_id
                    )

                # Store channel with device link
                if db.upsert_channel(int(channel_id), channel_name, site_id,
                                    int(device_id) if device_id else None):
                    valid_channels.append({
                        'id': int(channel_id),
                        'name': channel_name
                    })

            print(f"✅ {len(valid_channels)} valid channels stored\n")
            print("📥 Fetching readings...\n")

            total_readings = 0
            start_time = time.time()

            if use_explicit_range:
                # Iterate day-by-day over the explicit range (backfill-friendly)
                current = start_date
                day_count = 0
                while current <= end_date:
                    day_start = datetime.combine(current, datetime.min.time())
                    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
                    day_count += 1
                    for i, channel in enumerate(valid_channels, 1):
                        try:
                            readings = client.get_readings(
                                channel['id'],
                                day_start.isoformat(),
                                day_end.isoformat(),
                                fields=['E', 'P', 'V', 'I', 'PF'],
                                resolution=res
                            )
                            inserted = db.insert_readings(channel['id'], readings)
                            total_readings += inserted
                            time.sleep(1.5)
                        except Exception as e:
                            print(f"   [{current}] {channel['name']}: ❌ {e}")
                    if day_count % 10 == 0 or current == end_date:
                        print(f"   … through {current} ({total_readings:,} readings so far)")
                    current += timedelta(days=1)
            else:
                # Single range: last N days (original behavior)
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)

                for i, channel in enumerate(valid_channels, 1):
                    print(f"   [{i}/{len(valid_channels)}] {channel['name']}... ", end='', flush=True)
                    try:
                        readings = client.get_readings(
                            channel['id'],
                            start_dt.isoformat(),
                            end_dt.isoformat(),
                            fields=['E', 'P', 'V', 'I', 'PF'],
                            resolution=res
                        )
                        inserted = db.insert_readings(channel['id'], readings)
                        total_readings += inserted
                        print(f"✅ {inserted:,} readings")
                        time.sleep(1.5)
                    except Exception as e:
                        print(f"❌ {e}")

            duration = time.time() - start_time

            print(f"\n✅ Ingestion complete!")
            print(f"   Total readings: {total_readings:,}")
            print(f"   Duration: {duration:.1f}s\n")

            # Verify
            total_in_db = db.get_total_readings()
            print(f"📊 Total readings in database: {total_in_db:,}\n")

            # Refresh materialized views so analytics stay current
            try:
                from govern.refresh_views import refresh_materialized_views
                print("🔄 Refreshing materialized views...")
                if refresh_materialized_views(verbose=True):
                    print("   ✅ Views refreshed.\n")
                else:
                    print("   ⚠️  Some view refreshes skipped or failed.\n")
            except Exception as e:
                print(f"   ⚠️  View refresh skipped: {e}\n")

            print("💡 Next steps:")
            print("   1. Enable TimescaleDB: See docs/setup/NEON_SETUP_GUIDE.md")
            print("   2. Set up daily sync: Add to crontab")
            print("   3. Query your data with Python!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _parse_date(s: str) -> date:
    """Parse YYYY-MM-DD to date."""
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid date '{s}'; use YYYY-MM-DD.")


def main():
    parser = argparse.ArgumentParser(description='Ingest Eniscope data to PostgreSQL')
    parser.add_argument('--site', default='23271', help='Site ID (default: 23271)')
    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='Days of data to fetch from today (default: 90). Ignored if --start-date/--end-date set.'
    )
    parser.add_argument(
        '--start-date',
        metavar='YYYY-MM-DD',
        default=None,
        help='Start of date window (use with --end-date for backfill).'
    )
    parser.add_argument(
        '--end-date',
        metavar='YYYY-MM-DD',
        default=None,
        help='End of date window (use with --start-date for backfill).'
    )
    parser.add_argument(
        '--resolution',
        type=int,
        default=None,
        help='Resolution in seconds (default: 900 = 15 min). Override with ENISCOPE_RESOLUTION.'
    )

    args = parser.parse_args()

    # Logic priority: explicit range overrides --days
    start_date = None
    end_date = None
    if args.start_date is not None or args.end_date is not None:
        if args.start_date is None or args.end_date is None:
            print("❌ Provide both --start-date and --end-date for a date range.")
            sys.exit(1)
        start_date = _parse_date(args.start_date)
        end_date = _parse_date(args.end_date)
    days = args.days if args.days is not None else 90

    ingest_data(
        site_id=args.site,
        days=days,
        start_date=start_date,
        end_date=end_date,
        resolution=args.resolution,
    )


if __name__ == '__main__':
    main()
