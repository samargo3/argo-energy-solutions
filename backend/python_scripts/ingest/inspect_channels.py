#!/usr/bin/env python3
"""
Inspect Eniscope channels for specific devices.

Tries multiple endpoint patterns to find channel IDs, then falls back
to the meteringPoints array nested inside the device object.

Usage:
    python backend/python_scripts/ingest/inspect_channels.py
    python backend/python_scripts/ingest/inspect_channels.py --devices 111413 111937
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

# Default devices to scan
DEFAULT_DEVICES = [
    ('111413', 'Eniscope Argo House – Main Hub'),
    ('111937', 'A/C 3 – Specific Appliance'),
]


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


def _get_json(url: str, headers: dict, params: dict = None, label: str = ''):
    """GET and return (status_code, parsed_json_or_None)."""
    try:
        resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
        tag = label or url
        print(f"      {tag}  →  {resp.status_code}")
        if resp.status_code in (404, 405):
            return resp.status_code, None
        resp.raise_for_status()
        return resp.status_code, resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"      ❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
        return e.response.status_code, None
    except Exception as e:
        print(f"      ❌ {e}")
        return 0, None


def _extract_list(data, *keys) -> list:
    """Pull a list from a dict by trying multiple keys, or return data if already a list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in keys:
            val = data.get(k)
            if isinstance(val, list):
                return val
        # Maybe the whole dict is a single item
        return [data] if data.get('id') or data.get('channelId') else []
    return []


# ── Channel discovery ───────────────────────────────────────────────────────

def find_channels_for_device(device_id: str, headers: dict) -> list:
    """Try several endpoint patterns to find channels for a device."""

    # Pattern 1: /channels?device_id={ID}
    status, data = _get_json(
        f'{API_URL}/channels', headers,
        params={'device_id': device_id},
        label=f'/channels?device_id={device_id}'
    )
    channels = _extract_list(data, 'channels', 'data', 'items', 'result') if data else []
    if channels:
        return channels

    # Pattern 2: /channels?device={ID}
    status, data = _get_json(
        f'{API_URL}/channels', headers,
        params={'device': device_id},
        label=f'/channels?device={device_id}'
    )
    channels = _extract_list(data, 'channels', 'data', 'items', 'result') if data else []
    if channels:
        return channels

    # Pattern 3: /devices/{ID}/channels
    status, data = _get_json(
        f'{API_URL}/devices/{device_id}/channels', headers,
        label=f'/devices/{device_id}/channels'
    )
    channels = _extract_list(data, 'channels', 'data', 'items', 'result') if data else []
    if channels:
        return channels

    # Pattern 4: /devices/{ID}/points
    status, data = _get_json(
        f'{API_URL}/devices/{device_id}/points', headers,
        label=f'/devices/{device_id}/points'
    )
    channels = _extract_list(data, 'points', 'data', 'items', 'result') if data else []
    if channels:
        return channels

    return []


def find_metering_points_fallback(device_id: str, headers: dict) -> list:
    """Fallback: GET /devices/{ID} and extract meteringPoints from the device object."""
    print(f"      Fallback: inspecting /devices/{device_id} for nested meteringPoints...")
    status, data = _get_json(
        f'{API_URL}/devices/{device_id}', headers,
        label=f'/devices/{device_id}'
    )
    if not data or not isinstance(data, dict):
        return []

    # Try common nesting patterns
    for key in ('meteringPoints', 'metering_points', 'channels', 'points',
                'inputs', 'dataChannels', 'data_channels'):
        nested = data.get(key)
        if isinstance(nested, list) and nested:
            print(f"      ✓ Found '{key}' array ({len(nested)} items)")
            return nested

    # If nothing matched, dump the top-level keys so we can see what's there
    print(f"      ⚠️  No known channel array found. Top-level keys: {list(data.keys())}")
    print(f"      Raw (first 3000 chars):\n{json.dumps(data, indent=2, default=str)[:3000]}")
    return []


# ── Output ──────────────────────────────────────────────────────────────────

def print_channel_table(device_id: str, device_label: str, channels: list):
    """Print a clean table of channels."""
    print(f"\n   {'ID':<12} {'Name':<40} {'Unit':<10} {'Description'}")
    print(f"   {'─' * 12} {'─' * 40} {'─' * 10} {'─' * 40}")

    for ch in channels:
        cid = (ch.get('id') or ch.get('channelId') or ch.get('dataChannelId')
               or ch.get('pointId') or '?')
        name = (ch.get('name') or ch.get('channelName') or ch.get('pointName')
                or ch.get('label') or '—')
        unit = (ch.get('unit') or ch.get('units') or ch.get('unitOfMeasure')
                or ch.get('uom') or '—')
        desc = (ch.get('description') or ch.get('desc') or ch.get('type')
                or ch.get('channelType') or ch.get('pointType') or '—')
        print(f"   {str(cid):<12} {name:<40} {unit:<10} {desc}")


def print_summary(results: list):
    """Print the final mapping summary."""
    print(f"\n{'═' * 70}")
    print("📊 CHANNEL MAP SUMMARY")
    print('═' * 70)

    for device_id, device_label, channels in results:
        print(f"\n   Device {device_id} ({device_label})")
        if not channels:
            print("      └─ (no channels found)")
            continue
        for ch in channels:
            cid = (ch.get('id') or ch.get('channelId') or ch.get('dataChannelId')
                   or ch.get('pointId') or '?')
            name = (ch.get('name') or ch.get('channelName') or ch.get('pointName')
                    or ch.get('label') or '—')
            unit = (ch.get('unit') or ch.get('units') or ch.get('unitOfMeasure')
                    or ch.get('uom') or '')
            unit_tag = f" [{unit}]" if unit and unit != '—' else ''
            print(f"      └─ Channel {cid}: {name}{unit_tag}")

    print(f"\n{'═' * 70}\n")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Inspect Eniscope channels for specific devices')
    parser.add_argument(
        '--devices', nargs='+', default=None,
        help='Device IDs to scan (default: 111413 111937)'
    )
    args = parser.parse_args()

    # Build device list
    if args.devices:
        devices = [(d, f'Device {d}') for d in args.devices]
    else:
        devices = DEFAULT_DEVICES

    headers = _build_headers()

    print("🔌 Eniscope Channel Inspector")
    print(f"   Base URL:  {API_URL}")
    print(f"   Devices:   {', '.join(d[0] for d in devices)}")
    print(f"   Auth:      Basic Auth ✓\n")

    results = []

    for device_id, device_label in devices:
        print(f"{'─' * 70}")
        print(f"🔎 Scanning: {device_label} (ID: {device_id})")
        print(f"{'─' * 70}")

        channels = find_channels_for_device(device_id, headers)

        if not channels:
            channels = find_metering_points_fallback(device_id, headers)

        if channels:
            print_channel_table(device_id, device_label, channels)
        else:
            print(f"\n   ⚠️  No channels found for device {device_id}")

        results.append((device_id, device_label, channels))
        print()

    print_summary(results)


if __name__ == '__main__':
    main()
