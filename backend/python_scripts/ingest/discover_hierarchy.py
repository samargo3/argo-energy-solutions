#!/usr/bin/env python3
"""
Eniscope Hierarchy Discovery (Stage 1 – Ingest)

Maps the device → point hierarchy so we know exactly which IDs to pull
raw readings from.

Usage:
    python backend/python_scripts/ingest/discover_hierarchy.py
    python backend/python_scripts/ingest/discover_hierarchy.py --site 23271
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
from typing import Optional, Union, List, Dict
from dotenv import load_dotenv

# Governance: Path Resiliency
_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))
load_dotenv(_PROJECT_ROOT / '.env', override=True)

# ── Auth (matches working curl / ingest_to_postgres.py) ─────────────────────

API_URL = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com').rstrip('/')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)


def _build_headers() -> dict:
    """Build request headers with Basic Auth + X-Eniscope-API."""
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


def _get(url: str, headers: dict, params: dict = None, label: str = '') -> dict | list | None:
    """GET helper with error handling. Returns parsed JSON or None."""
    try:
        resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
        print(f"   {label or url}  →  {resp.status_code}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP {e.response.status_code}: {e.response.text[:300]}")
        return None
    except Exception as e:
        print(f"   ❌ {e}")
        return None


# ── Step 1: Discover Devices ────────────────────────────────────────────────

def discover_devices(headers: dict, site_id: str | None) -> list:
    """Try multiple endpoint patterns to find devices."""
    print("\n🔎 Step 1: Discovering devices...\n")

    endpoints = [
        (f'{API_URL}/devices', {}, '/devices'),
    ]
    if site_id:
        endpoints.insert(0, (f'{API_URL}/devices', {'organization': site_id}, f'/devices?organization={site_id}'))

    for url, params, label in endpoints:
        data = _get(url, headers, params, label)
        if data is not None:
            devices = _normalize_list(data, 'devices')
            if devices:
                return devices

    print("   ⚠️  No devices found via /devices endpoint.")
    return []


def _normalize_list(data, key: str) -> list:
    """Extract a list from various API response shapes."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get(key) or data.get('data') or data.get('items') or data.get('result') or []
    return []


# ── Step 2: Discover Points (Channels) ──────────────────────────────────────

def discover_points(headers: dict, device_id: str | int) -> list:
    """Try /points and /devices/{id}/points to find channels."""
    endpoints = [
        (f'{API_URL}/devices/{device_id}/points', {}, f'/devices/{device_id}/points'),
        (f'{API_URL}/points', {'device': device_id}, f'/points?device={device_id}'),
        (f'{API_URL}/points', {}, '/points (all)'),
    ]

    for url, params, label in endpoints:
        data = _get(url, headers, params, label)
        if data is not None:
            points = _normalize_list(data, 'points')
            if points:
                return points

    return []


# ── Output ──────────────────────────────────────────────────────────────────

def print_devices(devices: list):
    print(f"\n📋 Found {len(devices)} device(s):\n")
    print(f"   {'ID':<12} {'Name':<35} {'Type':<20} {'UUID'}")
    print(f"   {'─'*12} {'─'*35} {'─'*20} {'─'*36}")
    for d in devices:
        did = d.get('id') or d.get('deviceId') or d.get('device_id') or '?'
        name = d.get('name') or d.get('deviceName') or d.get('device_name') or '—'
        dtype = d.get('type') or d.get('deviceTypeName') or d.get('deviceType') or '—'
        uuid = d.get('uuId') or d.get('uuid') or d.get('serial') or '—'
        print(f"   {str(did):<12} {name:<35} {dtype:<20} {uuid}")


def print_points(points: list, device_label: str):
    print(f"\n🔌 Points for {device_label}:  ({len(points)} found)\n")
    print(f"   {'ID':<12} {'Name':<40} {'Unit':<10} {'Type'}")
    print(f"   {'─'*12} {'─'*40} {'─'*10} {'─'*20}")
    for p in points:
        pid = p.get('id') or p.get('pointId') or p.get('channelId') or p.get('dataChannelId') or '?'
        name = p.get('name') or p.get('pointName') or p.get('channelName') or '—'
        unit = p.get('unit') or p.get('units') or p.get('unitOfMeasure') or '—'
        ptype = p.get('type') or p.get('pointType') or p.get('channelType') or '—'
        print(f"   {str(pid):<12} {name:<40} {unit:<10} {ptype}")


def print_summary(devices: list, device_points: dict):
    """Print a clean summary for copy-pasting into ingestion config."""
    print("\n" + "═" * 70)
    print("📊 HIERARCHY SUMMARY (for ingestion)")
    print("═" * 70)

    for d in devices:
        did = d.get('id') or d.get('deviceId') or d.get('device_id') or '?'
        name = d.get('name') or d.get('deviceName') or d.get('device_name') or '—'
        points = device_points.get(str(did), [])
        print(f"\n   Device: {name}  (ID: {did})")
        if points:
            for p in points:
                pid = p.get('id') or p.get('pointId') or p.get('channelId') or p.get('dataChannelId') or '?'
                pname = p.get('name') or p.get('pointName') or p.get('channelName') or '—'
                unit = p.get('unit') or p.get('units') or '—'
                print(f"      └─ Point {pid}: {pname}  [{unit}]")
        else:
            print(f"      └─ (no points discovered)")

    print("\n" + "═" * 70 + "\n")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Discover Eniscope device/point hierarchy')
    parser.add_argument('--site', default='23271', help='Organization / Site ID (default: 23271)')
    args = parser.parse_args()

    print("🗺️  Eniscope Hierarchy Discovery")
    print(f"   Base URL: {API_URL}")
    print(f"   Site ID:  {args.site}")

    headers = _build_headers()
    print(f"   Auth:     Basic Auth ✓")

    # Step 1 — Devices
    devices = discover_devices(headers, args.site)

    if not devices:
        # Fallback: try /organizations first, then /channels (what ingest_to_postgres uses)
        print("\n   Falling back to /organizations + /channels path...")
        orgs_data = _get(f'{API_URL}/organizations', headers, label='/organizations')
        channels_data = _get(f'{API_URL}/channels', headers, {'organization': args.site},
                             f'/channels?organization={args.site}')
        if channels_data:
            channels = _normalize_list(channels_data, 'channels')
            print(f"\n📋 Found {len(channels)} channel(s) via /channels:\n")
            print(f"   {'ID':<12} {'Name':<40} {'DeviceID':<12} {'DeviceName'}")
            print(f"   {'─'*12} {'─'*40} {'─'*12} {'─'*30}")
            for c in channels:
                cid = c.get('channelId') or c.get('dataChannelId') or c.get('id') or '?'
                name = c.get('channelName') or c.get('name') or '—'
                dev_id = c.get('deviceId') or '—'
                dev_name = c.get('deviceName') or '—'
                print(f"   {str(cid):<12} {name:<40} {str(dev_id):<12} {dev_name}")
        print()
        return

    print_devices(devices)

    # Step 2 — Points for each device
    device_points = {}
    for d in devices:
        did = d.get('id') or d.get('deviceId') or d.get('device_id')
        name = d.get('name') or d.get('deviceName') or d.get('device_name') or f'Device {did}'

        if not did:
            continue

        print(f"\n🔎 Step 2: Discovering points for '{name}' (ID: {did})...\n")
        points = discover_points(headers, did)
        device_points[str(did)] = points

        if points:
            print_points(points, f"{name} (ID: {did})")
        else:
            print(f"   ⚠️  No points found for device {did}")

    # Summary
    print_summary(devices, device_points)


if __name__ == '__main__':
    main()
