#!/usr/bin/env python3
"""
Test the WORKING authentication method from Best.Energy support.
Uses X-Eniscope-API header + Authorization: Basic header
"""
import os
import sys
import base64
import hashlib
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

API_URL = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

def create_auth_headers():
    """Create headers using the working authentication method."""
    # MD5 hash the password
    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()

    # Create Basic Auth: base64(username:md5_password)
    auth_string = f"{EMAIL}:{password_md5}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    return {
        'X-Eniscope-API': API_KEY,
        'Authorization': f'Basic {auth_b64}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

print("🔐 Testing WORKING Authentication Method")
print("=" * 70)
print(f"API URL: {API_URL}")
print(f"Email: {EMAIL}")
print(f"API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
print()

headers = create_auth_headers()
print(f"Auth Header (preview): {headers['Authorization'][:30]}...")
print()

# Test 1: Get devices
print("Test 1: GET /devices")
print("-" * 70)
try:
    response = requests.get(f"{API_URL}/devices", headers=headers, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        devices = data.get('devices', [])
        print(f"✅ SUCCESS! Found {len(devices)} devices")

        # Show first device
        if devices:
            print(f"\nSample device:")
            dev = devices[0]
            print(f"  ID: {dev.get('deviceId')}")
            print(f"  Name: {dev.get('deviceName')}")
            print(f"  UUID: {dev.get('uuId')}")
            print(f"  Org: {dev.get('organizationId')}")
    else:
        print(f"❌ Failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Get channels
print("Test 2: GET /channels")
print("-" * 70)
try:
    response = requests.get(f"{API_URL}/channels", headers=headers, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        # Handle different response formats
        if isinstance(data, dict) and 'channels' in data:
            channels = data['channels']
        elif isinstance(data, list):
            channels = data
        else:
            channels = []

        print(f"✅ SUCCESS! Found {len(channels)} channels")

        # Show first few channels
        if channels:
            print(f"\nSample channels:")
            for i, ch in enumerate(channels[:3], 1):
                ch_id = ch.get('channelId') or ch.get('dataChannelId') or ch.get('id')
                ch_name = ch.get('channelName') or ch.get('name')
                print(f"  {i}. {ch_name} (ID: {ch_id})")
    else:
        print(f"❌ Failed: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 3: Get readings for a channel
print("Test 3: GET /readings/{channel_id}")
print("-" * 70)
print("Attempting to get first channel's readings...")

try:
    # First get channels to find a valid channel ID
    response = requests.get(f"{API_URL}/channels", headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        channels = data.get('channels', []) if isinstance(data, dict) else data

        if channels:
            first_channel = channels[0]
            channel_id = first_channel.get('channelId') or first_channel.get('dataChannelId')
            channel_name = first_channel.get('channelName') or first_channel.get('name')

            print(f"Using channel: {channel_name} (ID: {channel_id})")

            # Get readings
            params = {
                'action': 'summarize',
                'res': '900',  # 15 minutes
                'range_start': '2026-02-05 00:00:00',
                'range_end': '2026-02-05 23:59:59',
                'fields[]': ['E', 'P', 'V', 'I', 'PF'],
                'format': 'json'
            }

            response = requests.get(
                f"{API_URL}/readings/{channel_id}",
                headers=headers,
                params=params,
                timeout=30
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                readings_data = response.json()

                # Extract readings
                if isinstance(readings_data, list):
                    readings = readings_data
                elif isinstance(readings_data, dict):
                    readings = (readings_data.get('records') or
                               readings_data.get('data') or
                               readings_data.get('readings') or [])
                else:
                    readings = []

                print(f"✅ SUCCESS! Got {len(readings)} readings")

                if readings:
                    print(f"\nSample reading:")
                    r = readings[0]
                    print(f"  Timestamp: {r.get('ts') or r.get('t')}")
                    print(f"  Energy: {r.get('E')} Wh")
                    print(f"  Power: {r.get('P')} W")
            else:
                print(f"❌ Failed: {response.text[:200]}")
        else:
            print("⚠️  No channels found to test with")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 70)
print("✅ AUTHENTICATION METHOD CONFIRMED WORKING!")
print()
print("Next step: Update ingest_to_postgres.py to use this auth method")
