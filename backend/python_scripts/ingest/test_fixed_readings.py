#!/usr/bin/env python3
"""
Test readings fetch with manually constructed query string.

The Eniscope API expects array params with brackets (fields[]=E&fields[]=P).
Python requests can mangle these, so we build the URL by hand.

Usage:
    python backend/python_scripts/ingest/test_fixed_readings.py
    python backend/python_scripts/ingest/test_fixed_readings.py --channel 162285 --from 2025-02-01 --to 2025-02-02
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


def build_url(channel_id: str, date_from: str, date_to: str, resolution: int, fields: list) -> str:
    """Manually construct the URL with bracket-style array params."""
    base = f"{API_URL}/readings/{channel_id}"

    parts = [
        'action=summarize',
        f'res={resolution}',
        f'daterange[]={date_from}',
        f'daterange[]={date_to}',
    ]
    for f in fields:
        parts.append(f'fields[]={f}')

    return f"{base}?{'&'.join(parts)}"


def main():
    parser = argparse.ArgumentParser(description='Test readings with manual query string (bracket params)')
    parser.add_argument('--channel', default='162285', help='Channel ID (default: 162285)')
    parser.add_argument('--from', dest='date_from', default='2025-02-01', help='Start date YYYY-MM-DD')
    parser.add_argument('--to', dest='date_to', default='2025-02-02', help='End date YYYY-MM-DD')
    parser.add_argument('--res', type=int, default=3600, help='Resolution in seconds (default: 3600)')
    args = parser.parse_args()

    fields = ['E', 'P', 'V']
    headers = _build_headers()

    url = build_url(args.channel, args.date_from, args.date_to, args.res, fields)

    print("⚡ Eniscope Fixed Readings Test")
    print(f"   Channel:    {args.channel}")
    print(f"   Range:      {args.date_from} → {args.date_to}")
    print(f"   Resolution: {args.res}s")
    print(f"   Fields:     {fields}")
    print(f"   Auth:       Basic Auth ✓")
    print(f"\n📤 Constructed URL:\n   {url}\n")

    try:
        # Send with NO params dict — the URL already has everything
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"📥 Status: {resp.status_code}\n")

        try:
            data = resp.json()
            formatted = json.dumps(data, indent=2, default=str)

            if len(formatted) > 10000:
                print(formatted[:10000])
                print(f"\n... (truncated – full response is {len(formatted):,} chars)")
            else:
                print(formatted)

            # Quick structure analysis
            print(f"\n{'─' * 60}")
            print("📊 Structure:")
            if isinstance(data, list):
                print(f"   Type: list ({len(data)} items)")
                if data:
                    first = data[0]
                    if isinstance(first, dict):
                        print(f"   Keys: {list(first.keys())}")
                        print(f"   Sample: {json.dumps(first, indent=4, default=str)[:400]}")
                    else:
                        print(f"   First item: {first}")
                if len(data) > 0:
                    print(f"\n   ✅ SUCCESS — got {len(data)} reading(s)!")
                else:
                    print(f"\n   ⚠️  Empty list — no readings for this range.")
            elif isinstance(data, dict):
                print(f"   Type: dict")
                print(f"   Keys: {list(data.keys())}")
                for key in ('readings', 'records', 'data', 'result', 'items', 'values'):
                    val = data.get(key)
                    if isinstance(val, list):
                        print(f"   '{key}' array: {len(val)} items")
                        if val:
                            first = val[0]
                            if isinstance(first, dict):
                                print(f"   Keys: {list(first.keys())}")
                                print(f"   Sample: {json.dumps(first, indent=4, default=str)[:400]}")
                            print(f"\n   ✅ SUCCESS — got {len(val)} reading(s)!")
                        break
            print('─' * 60)

        except Exception:
            print(f"(Not JSON) Raw text:\n{resp.text[:2000]}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    print()


if __name__ == '__main__':
    main()
