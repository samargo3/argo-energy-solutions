#!/usr/bin/env python3
"""
Test raw readings fetch for a single channel – proves we can pull real data.

Usage:
    python backend/python_scripts/ingest/test_raw_readings.py
    python backend/python_scripts/ingest/test_raw_readings.py --channel 162285 --from 2025-02-01 --to 2025-02-02 --res 3600
"""
from __future__ import annotations

import os
import sys
import json
import base64
import hashlib
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Governance: Path Resiliency
_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env', override=True)

# ── Config ──────────────────────────────────────────────────────────────────

API_URL = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com').rstrip('/')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)


def _build_headers() -> dict:
    if not all([API_KEY, EMAIL, PASSWORD]):
        print("❌ Missing env vars. Need: VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL, VITE_ENISCOPE_PASSWORD")
        sys.exit(1)

    password_md5 = hashlib.md5(PASSWORD.strip().encode()).hexdigest()
    auth_str = f"{EMAIL}:{password_md5}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()

    return {
        'User-Agent': USER_AGENT,
        'X-Eniscope-API': API_KEY,
        'Authorization': f'Basic {auth_b64}',
        'Accept': 'application/json',
    }


def fetch_readings(headers: dict, channel_id: str, date_from: str, date_to: str, resolution: int):
    """Try multiple endpoint/param patterns to fetch readings."""

    # The patterns we'll try, in order of likelihood based on the Core API v1 docs
    attempts = [
        {
            'label': '/readings?channel_id={id}&from=...&to=...&res=...',
            'url': f'{API_URL}/readings',
            'params': {
                'channel_id': channel_id,
                'from': f'{date_from} 00:00:00',
                'to': f'{date_to} 00:00:00',
                'res': str(resolution),
            },
        },
        {
            'label': '/readings/{id}?from=...&to=...&res=...',
            'url': f'{API_URL}/readings/{channel_id}',
            'params': {
                'from': f'{date_from} 00:00:00',
                'to': f'{date_to} 00:00:00',
                'res': str(resolution),
            },
        },
        {
            'label': '/readings/{id}?action=summarize&daterange[]&res=...',
            'url': f'{API_URL}/readings/{channel_id}',
            'params': {
                'action': 'summarize',
                'res': str(resolution),
                'daterange[]': [date_from, date_to],
                'fields[]': ['E', 'P', 'V', 'I', 'PF'],
            },
        },
        {
            'label': '/channels/{id}/readings?from=...&to=...',
            'url': f'{API_URL}/channels/{channel_id}/readings',
            'params': {
                'from': f'{date_from} 00:00:00',
                'to': f'{date_to} 00:00:00',
                'res': str(resolution),
            },
        },
    ]

    for attempt in attempts:
        print(f"\n{'─' * 70}")
        print(f"🔎  {attempt['label']}")
        print(f"    GET {attempt['url']}")
        print(f"    Params: {json.dumps(attempt['params'], default=str)}")
        print('─' * 70)

        try:
            resp = requests.get(
                attempt['url'],
                headers=headers,
                params=attempt['params'],
                timeout=30,
            )
            print(f"    Status: {resp.status_code}\n")

            if resp.status_code == 404:
                print("    ⚠️  404 Not Found – trying next pattern...\n")
                continue

            if resp.status_code == 401:
                print("    ❌ 401 Unauthorized – auth issue.\n")
                continue

            # Try to parse JSON
            try:
                data = resp.json()
            except Exception:
                print(f"    (Not JSON) Raw text:\n{resp.text[:2000]}")
                continue

            # Pretty-print the full response
            formatted = json.dumps(data, indent=2, default=str)
            if len(formatted) > 8000:
                print(formatted[:8000])
                print(f"\n    ... (truncated – full response is {len(formatted):,} chars)")
            else:
                print(formatted)

            # Quick analysis of the structure
            print(f"\n{'─' * 70}")
            print("📊 Structure Analysis:")
            print('─' * 70)

            if isinstance(data, list):
                print(f"    Type: list ({len(data)} items)")
                if data:
                    first = data[0]
                    print(f"    First item keys: {list(first.keys()) if isinstance(first, dict) else type(first).__name__}")
                    print(f"    First item: {json.dumps(first, indent=6, default=str)[:500]}")
            elif isinstance(data, dict):
                print(f"    Type: dict")
                print(f"    Top-level keys: {list(data.keys())}")
                # Look for the readings array
                for key in ('readings', 'records', 'data', 'result', 'items', 'values'):
                    val = data.get(key)
                    if isinstance(val, list) and val:
                        print(f"    Found '{key}' array: {len(val)} items")
                        first = val[0]
                        print(f"    First item keys: {list(first.keys()) if isinstance(first, dict) else type(first).__name__}")
                        print(f"    First item: {json.dumps(first, indent=6, default=str)[:500]}")
                        break
            else:
                print(f"    Type: {type(data).__name__}")

            # If we got data, no need to try more patterns
            has_data = False
            if isinstance(data, list) and len(data) > 0:
                has_data = True
            elif isinstance(data, dict):
                for key in ('readings', 'records', 'data', 'result', 'items', 'values'):
                    val = data.get(key)
                    if isinstance(val, list) and len(val) > 0:
                        has_data = True
                        break

            if has_data:
                print(f"\n    ✅ Got readings! This pattern works.\n")
                return data
            else:
                print(f"\n    ⚠️  Response was empty or had no readings. Trying next pattern...\n")

        except Exception as e:
            print(f"    ❌ Request failed: {e}")

    print("\n❌ No endpoint pattern returned readings.")
    return None


def main():
    parser = argparse.ArgumentParser(description='Test raw readings fetch from Eniscope')
    parser.add_argument('--channel', default='162285', help='Channel ID (default: 162285 – Kitchen Main Panel)')
    parser.add_argument('--from', dest='date_from', default='2025-02-01', help='Start date YYYY-MM-DD (default: 2025-02-01)')
    parser.add_argument('--to', dest='date_to', default='2025-02-02', help='End date YYYY-MM-DD (default: 2025-02-02)')
    parser.add_argument('--res', type=int, default=3600, help='Resolution in seconds (default: 3600 = hourly)')
    args = parser.parse_args()

    headers = _build_headers()

    print("⚡ Eniscope Raw Readings Test")
    print(f"   Channel:    {args.channel}")
    print(f"   Date range: {args.date_from} → {args.date_to}")
    print(f"   Resolution: {args.res}s ({args.res // 60} min)")
    print(f"   Base URL:   {API_URL}")
    print(f"   Auth:       Basic Auth ✓")

    fetch_readings(headers, args.channel, args.date_from, args.date_to, args.res)

    print("═" * 70)
    print("Done.")
    print("═" * 70 + "\n")


if __name__ == '__main__':
    main()
