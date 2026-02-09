#!/usr/bin/env python3
"""
API Endpoint Discovery
Explores all available Eniscope API endpoints and documents capabilities.

Following Argo Energy governance: Stage 1 (Ingest)
"""
import os
import sys
import base64
import hashlib
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

API_URL = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

# Create auth headers
password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
auth_b64 = base64.b64encode(f"{EMAIL}:{password_md5}".encode()).decode()

headers = {
    'X-Eniscope-API': API_KEY,
    'Authorization': f'Basic {auth_b64}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

print("🔍 ENISCOPE API DISCOVERY")
print("=" * 70)
print(f"API URL: {API_URL}")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Known endpoints to test
endpoints = {
    '/organizations': {
        'description': 'List all organizations',
        'test_params': None,
        'expected_usage': 'Map to organizations table'
    },
    '/devices': {
        'description': 'List all devices',
        'test_params': None,
        'expected_usage': 'Map to devices table'
    },
    '/channels': {
        'description': 'List all channels',
        'test_params': None,
        'expected_usage': 'Map to channels table'
    },
    '/readings': {
        'description': 'Readings endpoint (requires channel ID)',
        'test_params': {'note': 'Requires /{channel_id}'},
        'expected_usage': 'Map to readings table'
    },
    '/sites': {
        'description': 'Site information (if available)',
        'test_params': None,
        'expected_usage': 'Potential site-level metadata'
    },
    '/meters': {
        'description': 'Meter information (if available)',
        'test_params': None,
        'expected_usage': 'Potential meter metadata'
    },
    '/users': {
        'description': 'User account information',
        'test_params': None,
        'expected_usage': 'User management'
    },
    '/reports': {
        'description': 'Pre-built reports (if available)',
        'test_params': None,
        'expected_usage': 'Report generation'
    },
    '/alerts': {
        'description': 'Alert configurations (if available)',
        'test_params': None,
        'expected_usage': 'Alert management'
    }
}

results = {}

for endpoint, info in endpoints.items():
    print(f"Testing: {endpoint}")
    print(f"  Purpose: {info['description']}")

    try:
        response = requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=10)

        status_code = response.status_code
        results[endpoint] = {
            'status': status_code,
            'description': info['description'],
            'expected_usage': info['expected_usage'],
            'available': status_code in [200, 201],
        }

        if response.status_code == 200:
            try:
                data = response.json()

                # Analyze response structure
                if isinstance(data, dict):
                    keys = list(data.keys())
                    results[endpoint]['response_type'] = 'dict'
                    results[endpoint]['keys'] = keys
                    results[endpoint]['sample_count'] = len(data.get('data', [])) if 'data' in data else None

                    print(f"  ✅ Available - Dict with keys: {keys[:5]}")

                    # Show sample data structure
                    if keys:
                        first_key = keys[0]
                        sample_value = data[first_key]
                        if isinstance(sample_value, list) and sample_value:
                            print(f"     Sample ({first_key}): {len(sample_value)} items")
                            if isinstance(sample_value[0], dict):
                                print(f"     Item structure: {list(sample_value[0].keys())[:5]}")

                elif isinstance(data, list):
                    results[endpoint]['response_type'] = 'list'
                    results[endpoint]['count'] = len(data)

                    print(f"  ✅ Available - List with {len(data)} items")

                    if data and isinstance(data[0], dict):
                        results[endpoint]['item_structure'] = list(data[0].keys())
                        print(f"     Item structure: {list(data[0].keys())[:8]}")

                else:
                    results[endpoint]['response_type'] = type(data).__name__
                    print(f"  ✅ Available - Returns: {type(data).__name__}")

            except json.JSONDecodeError:
                results[endpoint]['response_type'] = 'non-json'
                print(f"  ⚠️  Returns non-JSON response")

        elif response.status_code == 404:
            print(f"  ❌ Not Found (404)")
        elif response.status_code == 401:
            print(f"  🔒 Unauthorized (401)")
        elif response.status_code == 403:
            print(f"  🔒 Forbidden (403)")
        else:
            print(f"  ⚠️  Status: {response.status_code}")

    except requests.exceptions.Timeout:
        print(f"  ⏱️  Timeout")
        results[endpoint] = {
            'status': 'timeout',
            'description': info['description'],
            'available': False
        }
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        results[endpoint] = {
            'status': 'error',
            'description': info['description'],
            'available': False,
            'error': str(e)
        }

    print()

# Summary
print("=" * 70)
print("📋 DISCOVERY SUMMARY")
print("=" * 70)

available = [ep for ep, res in results.items() if res.get('available')]
unavailable = [ep for ep, res in results.items() if not res.get('available')]

print(f"\n✅ Available Endpoints ({len(available)}):")
for ep in available:
    desc = results[ep]['description']
    resp_type = results[ep].get('response_type', 'unknown')
    print(f"   {ep:30} - {desc}")
    print(f"   {'':30}   Returns: {resp_type}")

print(f"\n❌ Unavailable Endpoints ({len(unavailable)}):")
for ep in unavailable:
    status = results[ep].get('status', 'unknown')
    print(f"   {ep:30} - Status: {status}")

# Data capture recommendations
print(f"\n💡 RECOMMENDATIONS:")
print("-" * 70)

print("\n1. CURRENTLY CAPTURED:")
for ep in ['/organizations', '/devices', '/channels', '/readings']:
    if ep in available:
        print(f"   ✅ {ep:20} - Already mapped to database")

print("\n2. POTENTIALLY USEFUL (Not Currently Captured):")
for ep in available:
    if ep not in ['/organizations', '/devices', '/channels', '/readings']:
        usage = results[ep]['expected_usage']
        print(f"   🆕 {ep:20} - {usage}")

print("\n3. NEXT STEPS:")
print("   a. Review available endpoints and decide what to capture")
print("   b. Update ingestion scripts to capture new data sources")
print("   c. Create database tables/views for new data types")
print("   d. Document API field mappings")

# Save results
output_dir = _PROJECT_ROOT / 'docs'
output_dir.mkdir(exist_ok=True)
output_file = output_dir / 'api_discovery_results.json'

with open(output_file, 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'api_url': API_URL,
        'summary': {
            'total_tested': len(endpoints),
            'available': len(available),
            'unavailable': len(unavailable)
        },
        'endpoints': results
    }, f, indent=2)

print(f"\n💾 Full results saved to: {output_file}")
print()
print("=" * 70)
