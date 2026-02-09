#!/usr/bin/env python3
"""
Test ingesting a SINGLE channel to isolate the issue.
"""
import os
import sys
import base64
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

API_URL = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')
DB_URL = os.getenv('DATABASE_URL')

# Create auth headers
password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
auth_string = f"{EMAIL}:{password_md5}"
auth_b64 = base64.b64encode(auth_string.encode()).decode()

headers = {
    'X-Eniscope-API': API_KEY,
    'Authorization': f'Basic {auth_b64}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

print("🧪 Single Channel Ingestion Test")
print("=" * 70)

# Test with channel 158694 (Dryer) - we know this works
channel_id = 158694
channel_name = "Dryer"

print(f"Channel: {channel_name} (ID: {channel_id})")
print(f"Date: 2026-02-05")
print()

# Get readings
params = {
    'action': 'summarize',
    'res': '900',
    'range_start': '2026-02-05 00:00:00',
    'range_end': '2026-02-05 23:59:59',
    'fields[]': ['E', 'P', 'V', 'I', 'PF'],
    'format': 'json'
}

print("📥 Fetching readings...")
response = requests.get(
    f"{API_URL}/readings/{channel_id}",
    headers=headers,
    params=params,
    timeout=30
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    readings = data if isinstance(data, list) else data.get('readings', [])

    print(f"✅ Got {len(readings)} readings")

    if readings:
        # Normalize readings
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

        print(f"\nSample reading:")
        print(f"  {normalized[0]}")

        # Insert into database
        print(f"\n💾 Inserting into database...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        inserted = 0
        for r in normalized:
            if r['timestamp'] is None:
                continue

            try:
                ts = datetime.fromtimestamp(r['timestamp']) if isinstance(r['timestamp'], (int, float)) else datetime.fromisoformat(str(r['timestamp']))

                cur.execute("""
                    INSERT INTO readings (channel_id, timestamp, energy_kwh, power_kw,
                                        voltage_v, current_a, power_factor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (channel_id, timestamp) DO NOTHING
                """, (channel_id, ts, r['energy_kwh'], r['power_kw'],
                      r['voltage_v'], r['current_a'], r['power_factor']))

                if cur.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"   Error: {e}")
                continue

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Inserted {inserted} new readings")
        print(f"   (Duplicates skipped: {len(normalized) - inserted})")
    else:
        print("⚠️  No readings in response")
else:
    print(f"❌ Failed: {response.text[:500]}")

print()
print("=" * 70)
print("If this works, the issue is with how ingest_to_postgres.py")
print("is handling the channels or parameters.")
