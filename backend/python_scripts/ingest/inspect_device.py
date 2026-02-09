#!/usr/bin/env python3
"""
Inspect a single Eniscope device – dump raw JSON to find channel/point IDs.

Usage:
    python backend/python_scripts/ingest/inspect_device.py
    python backend/python_scripts/ingest/inspect_device.py --device 111413
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


def probe(url: str, headers: dict, label: str):
    """GET a URL, print status and pretty-printed JSON."""
    print(f"\n{'─' * 70}")
    print(f"🔎  {label}")
    print(f"    GET {url}")
    print('─' * 70)

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"    Status: {resp.status_code}\n")

        if resp.status_code == 404:
            print("    ⚠️  404 Not Found – endpoint does not exist.\n")
            return

        # Try to parse as JSON
        try:
            data = resp.json()
            print(json.dumps(data, indent=2, default=str))
        except Exception:
            print(f"    (Not JSON) Raw text:\n{resp.text[:2000]}")

    except Exception as e:
        print(f"    ❌ Request failed: {e}")


def main():
    parser = argparse.ArgumentParser(description='Inspect a single Eniscope device (raw JSON)')
    parser.add_argument('--device', default='111413', help='Device ID to inspect (default: 111413)')
    args = parser.parse_args()

    device_id = args.device
    headers = _build_headers()

    print(f"🔬 Eniscope Device Inspector")
    print(f"   Device ID: {device_id}")
    print(f"   Base URL:  {API_URL}")

    # Probe a series of likely endpoints
    endpoints = [
        (f'{API_URL}/devices/{device_id}',          f'/devices/{device_id}'),
        (f'{API_URL}/devices/{device_id}/channels',  f'/devices/{device_id}/channels'),
        (f'{API_URL}/devices/{device_id}/points',    f'/devices/{device_id}/points'),
        (f'{API_URL}/devices/{device_id}/inputs',    f'/devices/{device_id}/inputs'),
        (f'{API_URL}/channels',                      f'/channels?device={device_id} (query param)'),
        (f'{API_URL}/points',                        f'/points?device={device_id} (query param)'),
    ]

    for url, label in endpoints:
        params = {}
        # For the query-param variants, add device filter
        if label.endswith('(query param)'):
            params = {'device': device_id}
            resp_url = url
        else:
            resp_url = url

        print(f"\n{'─' * 70}")
        print(f"🔎  {label}")
        print(f"    GET {resp_url}" + (f"?device={device_id}" if params else ""))
        print('─' * 70)

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            print(f"    Status: {resp.status_code}\n")

            if resp.status_code == 404:
                print("    ⚠️  404 Not Found – skipping.\n")
                continue

            try:
                data = resp.json()
                formatted = json.dumps(data, indent=2, default=str)
                # Truncate very large responses but show enough to find structure
                if len(formatted) > 5000:
                    print(formatted[:5000])
                    print(f"\n    ... (truncated – full response is {len(formatted):,} chars)")
                else:
                    print(formatted)
            except Exception:
                text = resp.text[:2000]
                print(f"    (Not JSON) Raw text:\n{text}")

        except Exception as e:
            print(f"    ❌ Request failed: {e}")

    print(f"\n{'═' * 70}")
    print("✅ Done. Look for keys like 'channels', 'points', 'inputs', 'dataChannels'")
    print("   in the JSON above to find your channel/point IDs.")
    print('═' * 70 + '\n')


if __name__ == '__main__':
    main()
