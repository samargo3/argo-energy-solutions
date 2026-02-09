#!/usr/bin/env python3
"""
Eniscope Data Ingestion to PostgreSQL (Neon)

Day-by-day looper: fetches one day at a time using the validated
daterange=YYYY-MM-DD parameter format to avoid 500 errors.

Usage:
    # Last N days (default 90) — Kitchen Main channel
    python ingest_to_postgres.py --site 23271 --days 90

    # Exact date window (for backfill)
    python ingest_to_postgres.py --site 23271 --start-date 2025-01-01 --end-date 2025-02-09

    # Specific channel
    python ingest_to_postgres.py --site 23271 --days 30 --channel 162285
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

# Default resolution in seconds (1 hour). Hourly is the most stable for the API.
# Override via ENISCOPE_RESOLUTION env var or --resolution CLI flag.
DEFAULT_RESOLUTION = int(os.getenv('ENISCOPE_RESOLUTION', '3600'))

# Default channel for backfill (Kitchen Main Panel — known good data).
DEFAULT_CHANNEL_ID = int(os.getenv('ENISCOPE_DEFAULT_CHANNEL', '162285'))

# The 8 Wilson Center WCDS channels (hardware installed 2025-04-29).
WCDS_CHANNELS = [
    162119,  # RTU-2_WCDS_Wilson Ctr
    162120,  # RTU-3_WCDS_Wilson Ctr
    162121,  # AHU-2_WCDS_Wilson Ctr
    162122,  # AHU-1A_WCDS_Wilson Ctr
    162123,  # AHU-1B_WCDS_Wilson Ctr
    162285,  # CDPK_Kitchen Main Panel(s)_WCDS_Wilson Ctr
    162319,  # CDKH_Kitchen Panel(small)_WCDS_Wilson Ctr
    162320,  # RTU-1_WCDS_Wilson Ctr
]

# Channels that consistently return 500 "Invalid Parameter" errors.
# These are virtual/reference channels without actual readings data.
# They are skipped during ingestion to avoid wasting ~12s per channel per day on retries.
SKIP_CHANNELS = {
    162127,  # WCDS Reference Site — virtual reference, no readings
    162141,  # Argo Home Test Site — test channel, no readings
    162277,  # Air Sense_Main Kitchen_WCDS_Wilson — sensor type, no E/P/V fields
}


def _load_password_safely() -> str:
    """Load password from env; reject empty/missing values to avoid auth issues."""
    raw = os.getenv('VITE_ENISCOPE_PASSWORD')
    if not raw or not raw.strip():
        raise ValueError(
            'VITE_ENISCOPE_PASSWORD is missing. Set it in .env (no credentials in code).'
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
        """Make request with Basic Auth header and exponential backoff.
        
        Use this for endpoints where requests-style param encoding is fine
        (e.g. /organizations, /channels, /devices).
        """
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
    
    def _make_raw_request_with_retry(self, full_url: str, retries: int = 3) -> requests.Response:
        """Make request using a pre-built URL (no param encoding by requests).
        
        The Eniscope /readings endpoint requires bracket-style array params
        (fields[]=E&fields[]=P) which requests can mangle. This method takes
        a fully constructed URL and sends it as-is.
        """
        for attempt in range(retries):
            try:
                response = requests.get(
                    full_url,
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
                elif e.response.status_code == 500 and attempt < retries - 1:
                    delay = 2 ** (attempt + 2)  # 4s, 8s
                    print(f"\n   Server error (500). Waiting {delay}s before retry...")
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception(f"Failed after {retries} retries")
    
    def get_meters(self, organization_id: str = None) -> List[Dict]:
        """Get meters. If organization_id is None, fetches all accessible meters."""
        params = {}
        if organization_id:
            params['organization'] = organization_id
        response = self._make_request_with_retry(
            f'{self.base_url}/meters',
            params=params
        )

        data = response.json()

        # Handle various response formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('meters') or data.get('data') or data.get('items') or []
        return []

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
    
    def get_readings(self, channel_id: int, date_str: str,
                     fields: List[str] = None, resolution: int = None) -> List[Dict]:
        """Get readings for a single day using Unix Timestamps (from/to).
        
        API v1 requires integer timestamps for history, not date strings.
        """
        if resolution is None:
            resolution = DEFAULT_RESOLUTION
        if fields is None:
            fields = ['E', 'P', 'V']

        # 1. Convert 'YYYY-MM-DD' string to Unix Timestamps (Start & End of day)
        dt_start = datetime.strptime(date_str, "%Y-%m-%d")
        dt_end = dt_start + timedelta(days=1)
        ts_from = int(dt_start.timestamp())
        ts_to = int(dt_end.timestamp())

        # 2. Build URL — use daterange[] array syntax with Unix timestamps
        # The API echoes 'from'/'to' in the response but ignores our from=/to= params.
        # Try the array bracket syntax that works for fields: daterange[]=start&daterange[]=end
        field_params = '&'.join(f'fields[]={f}' for f in fields)
        url = (
            f'{self.base_url}/readings/{channel_id}'
            f'?action=summarize'
            f'&res={resolution}'
            f'&daterange[]={ts_from}'
            f'&daterange[]={ts_to}'
            f'&{field_params}'
        )
        
        # Uncomment for deep debugging:
        # print(f"   [DEBUG] URL: {url}")

        try:
            response = self._make_raw_request_with_retry(url)
            data = response.json()
        except Exception as e:
            print(f"   ⚠️  Request failed: {e}")
            return []
        
        # 3. Extract Records
        readings = data.get('records') or data.get('data') or data.get('readings') or []
        
        # 4. Normalize
        normalized = []
        for r in readings:
            ts = r.get('ts') or r.get('t') or r.get('timestamp')
            if ts is None:
                continue
            
            normalized.append({
                'timestamp': ts,
                'energy_kwh': r.get('E') / 1000.0 if r.get('E') is not None else 0,
                'power_kw': r.get('P') / 1000.0 if r.get('P') is not None else 0,
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

    def upsert_meter(self, meter_id: int, meter_name: str, org_id: str,
                     device_id: int = None, data_type: str = None,
                     ct_ratio: str = None, voltage_scale: str = None,
                     channel_count: int = None, interface_name: str = None,
                     interface_id: int = None, uuid: str = None,
                     parent_id: int = None, registered: int = None,
                     expires: int = None, status: str = None) -> bool:
        """Insert or update meter."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO meters (meter_id, device_id, meter_name, data_type,
                                      ct_ratio, voltage_scale, channel_count,
                                      interface_name, interface_id, organization_id,
                                      uuid, parent_id, registered, expires, status,
                                      updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (meter_id)
                    DO UPDATE SET
                        device_id = EXCLUDED.device_id,
                        meter_name = EXCLUDED.meter_name,
                        data_type = EXCLUDED.data_type,
                        ct_ratio = EXCLUDED.ct_ratio,
                        voltage_scale = EXCLUDED.voltage_scale,
                        channel_count = EXCLUDED.channel_count,
                        interface_name = EXCLUDED.interface_name,
                        interface_id = EXCLUDED.interface_id,
                        updated_at = NOW()
                """, (meter_id, device_id, meter_name, data_type, ct_ratio,
                      voltage_scale, channel_count, interface_name, interface_id,
                      org_id, uuid, parent_id, registered, expires, status))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"   ⚠️  Error storing meter {meter_id}: {e}")
            self.conn.rollback()
            return False

    def upsert_channel(self, channel_id: int, channel_name: str, org_id: str,
                      device_id: int = None, meter_id: int = None) -> bool:
        """Insert or update channel."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO channels (channel_id, channel_name, organization_id,
                                        device_id, meter_id, channel_type, unit, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (channel_id)
                    DO UPDATE SET
                        channel_name = EXCLUDED.channel_name,
                        device_id = EXCLUDED.device_id,
                        meter_id = EXCLUDED.meter_id,
                        updated_at = NOW()
                """, (channel_id, channel_name, org_id, device_id, meter_id, 'energy', 'kWh'))
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
    channel_ids: Optional[List[int]] = None,
    wcds_only: bool = False,
):
    """Main ingestion function — day-by-day looper.
    
    Fetches one day at a time per channel using daterange=YYYY-MM-DD,
    which is the only parameter format the API accepts without 500 errors.
    """
    res = resolution if resolution is not None else DEFAULT_RESOLUTION

    # Resolve date range
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            print("❌ --start-date must be on or before --end-date")
            sys.exit(1)
    else:
        days = days if days is not None else 90
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

    num_days = (end_date - start_date).days + 1
    range_label = f"{start_date} → {end_date} ({num_days} days)"

    if wcds_only:
        channel_mode = "WCDS-only (8 Wilson Center channels)"
    elif channel_ids:
        channel_mode = f"specific: {channel_ids}"
    else:
        channel_mode = "all site channels (auto-discover)"

    print("🌐 Eniscope → PostgreSQL Data Ingestion (Day-by-Day Looper)\n")
    print(f"📊 Site ID:    {site_id}")
    print(f"📅 Range:      {range_label}")
    print(f"📐 Resolution: {res}s ({res // 60} min)")
    print(f"🔌 Channels:   {channel_mode}\n")

    # Check environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        sys.exit(1)

    # Initialize client
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

            # ── Sync metadata: Meters ───────────────────────────────────
            print("📏 Fetching meters...")
            meters = client.get_meters(None)
            print(f"✅ Found {len(meters)} meters (all organizations)")

            meter_map = {}
            for meter in meters:
                meter_id = meter.get('meterId')
                if not meter_id:
                    continue

                device_id = meter.get('deviceId')
                meter_name = meter.get('deviceName') or f"Meter {meter_id}"
                data_type = meter.get('dataType')
                ct_ratio = meter.get('ct')
                voltage_scale = meter.get('vs')
                channel_count = int(meter.get('channels')) if meter.get('channels') else None
                iface = meter.get('interface') if isinstance(meter.get('interface'), dict) else {}
                interface_name = iface.get('interfaceName')
                interface_id = iface.get('deviceTypeInterfaceId')

                meter_org_id = meter.get('organizationId') or site_id
                if db.upsert_meter(
                    int(meter_id),
                    meter_name,
                    str(meter_org_id),
                    device_id=int(device_id) if device_id else None,
                    data_type=data_type,
                    ct_ratio=ct_ratio,
                    voltage_scale=voltage_scale,
                    channel_count=channel_count,
                    interface_name=interface_name,
                    interface_id=int(interface_id) if interface_id else None,
                    uuid=meter.get('uuId'),
                    parent_id=int(meter.get('parentId')) if meter.get('parentId') else None,
                    registered=int(meter.get('registered')) if meter.get('registered') else None,
                    expires=int(meter.get('expires')) if meter.get('expires') else None,
                    status=meter.get('status'),
                ):
                    meter_map[int(meter_id)] = True

            print(f"✅ {len(meter_map)} meters stored\n")

            # ── Sync metadata: Channels & Devices ───────────────────────
            print("🔌 Fetching channels...")
            channels = client.get_channels(site_id)
            print(f"✅ Found {len(channels)} channels\n")

            for channel in channels:
                channel_id = channel.get('channelId') or channel.get('dataChannelId')
                channel_name = channel.get('channelName') or channel.get('name') or f"Channel {channel_id}"
                if not channel_id:
                    continue

                device_id = channel.get('deviceId')
                device_name = channel.get('deviceName')
                device_type = channel.get('deviceTypeName') or channel.get('deviceType')
                uuid = channel.get('uuId') or channel.get('uuid')
                meter_id = channel.get('meterId')

                if device_id:
                    db.upsert_device(
                        int(device_id),
                        device_name or f"Device {device_id}",
                        device_type or 'Unknown',
                        uuid or '',
                        site_id,
                    )

                db.upsert_channel(
                    int(channel_id),
                    channel_name,
                    site_id,
                    device_id=int(device_id) if device_id else None,
                    meter_id=int(meter_id) if meter_id else None,
                )

            print(f"✅ Metadata sync complete\n")

            # ── Resolve target channels for readings ────────────────────
            # Build a lookup from API channels for name resolution
            api_channel_map = {}
            for c in channels:
                cid = c.get('channelId') or c.get('dataChannelId')
                cname = c.get('channelName') or c.get('name') or f'Channel {cid}'
                if cid:
                    api_channel_map[int(cid)] = cname

            if wcds_only:
                # Only the 8 Wilson Center WCDS channels
                fetch_channels = [
                    {'id': cid, 'name': api_channel_map.get(cid, f'WCDS Channel {cid}')}
                    for cid in WCDS_CHANNELS
                ]
            elif channel_ids:
                # User specified explicit channel IDs via --channel
                fetch_channels = [
                    {'id': cid, 'name': api_channel_map.get(cid, f'Channel {cid}')}
                    for cid in channel_ids
                    if cid not in SKIP_CHANNELS
                ]
            else:
                # Auto-discover: use ALL channels from the API for this site
                fetch_channels = [
                    {'id': int(cid), 'name': cname}
                    for cid, cname in api_channel_map.items()
                    if int(cid) not in SKIP_CHANNELS
                ]

            skipped = SKIP_CHANNELS - {ch['id'] for ch in fetch_channels}
            print(f"🎯 Target channels ({len(fetch_channels)}):")
            for ch in fetch_channels:
                print(f"   • {ch['id']}: {ch['name']}")
            if skipped:
                print(f"\n   ⏭️  Skipping {len(skipped)} broken channel(s): {sorted(skipped)}")
            print()

            # ── Day-by-day ingestion loop ───────────────────────────────
            print("📥 Fetching readings (day-by-day)...\n")

            total_readings = 0
            total_errors = 0
            start_time = time.time()
            current = start_date

            while current <= end_date:
                date_str = current.isoformat()  # 'YYYY-MM-DD'

                for ch in fetch_channels:
                    try:
                        readings = client.get_readings(
                            ch['id'],
                            date_str,
                            fields=['E', 'P', 'V'],
                            resolution=res,
                        )
                        fetched = len(readings)
                        inserted = db.insert_readings(ch['id'], readings)
                        total_readings += inserted

                        # Progress: show fetched vs inserted to spot dedup
                        print(f"   {date_str}  ch:{ch['id']} ({ch['name']})  →  fetched={fetched}, new={inserted}", flush=True)

                        # Be polite to the API
                        time.sleep(1)

                    except Exception as e:
                        total_errors += 1
                        print(f"   {date_str}  ch:{ch['id']} ({ch['name']})  ❌  {e}")

                current += timedelta(days=1)

            # ── Summary ─────────────────────────────────────────────────
            duration = time.time() - start_time

            print(f"\n✅ Ingestion complete!")
            print(f"   Days processed: {num_days}")
            print(f"   Total readings: {total_readings:,}")
            print(f"   Errors:         {total_errors}")
            print(f"   Duration:       {duration:.1f}s\n")

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
            print("   1. Run with more channels: --channel 162285 162290 ...")
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
    parser = argparse.ArgumentParser(description='Ingest Eniscope data to PostgreSQL (day-by-day)')
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
        help='Resolution in seconds (default: 3600 = hourly). Override with ENISCOPE_RESOLUTION.'
    )
    parser.add_argument(
        '--channel',
        type=int,
        nargs='+',
        default=None,
        help='Channel ID(s) to fetch. If omitted, ALL channels for the site are auto-discovered.'
    )
    parser.add_argument(
        '--wcds-only',
        action='store_true',
        default=False,
        help='Only fetch the 8 Wilson Center WCDS channels (overrides --channel).'
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
        channel_ids=args.channel,
        wcds_only=args.wcds_only,
    )


if __name__ == '__main__':
    main()
