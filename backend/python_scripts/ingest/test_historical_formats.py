#!/usr/bin/env python3
"""
Test different date parameter formats to find one that works for historical data.

Usage:
    python backend/python_scripts/ingest/test_historical_formats.py
"""
from __future__ import annotations

import os
import sys
import json
import base64
import hashlib
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

BASE_URL = 'https://core.eniscope.com'
CHANNEL_ID = '162285'

API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)


def _build_headers() -> dict:
    if not all([API_KEY, EMAIL, PASSWORD]):
        print("❌ Missing env vars.")
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


def run_test(label: str, query_string: str, headers: dict):
    """Send a manually constructed GET and print the result."""
    url = f"{BASE_URL}/readings/{CHANNEL_ID}?{query_string}"

    print(f"\n{'═' * 70}")
    print(f"🧪  {label}")
    print(f"    {url}")
    print('═' * 70)

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"    Status: {resp.status_code}")

        try:
            data = resp.json()
            formatted = json.dumps(data, indent=2, default=str)

            # Show a manageable amount
            if len(formatted) > 4000:
                print(f"\n{formatted[:4000]}")
                print(f"\n    ... ({len(formatted):,} chars total)")
            else:
                print(f"\n{formatted}")

            # Quick data check
            count = 0
            if isinstance(data, list):
                count = len(data)
            elif isinstance(data, dict):
                for k in ('readings', 'records', 'data', 'result', 'items', 'values'):
                    v = data.get(k)
                    if isinstance(v, list):
                        count = len(v)
                        break

            if resp.status_code == 200 and count > 0:
                print(f"\n    ✅ SUCCESS — {count} reading(s) returned!")
            elif resp.status_code == 200:
                print(f"\n    ⚠️  200 OK but no readings in response.")
            else:
                print(f"\n    ❌ HTTP {resp.status_code}")

        except Exception:
            print(f"    Raw text: {resp.text[:1000]}")

    except Exception as e:
        print(f"    ❌ Request failed: {e}")


def main():
    headers = _build_headers()

    print("⚡ Historical Date Format Tests")
    print(f"   Channel: {CHANNEL_ID}")
    print(f"   Auth:    Basic Auth ✓")

    # Test 1: Single date string (no brackets)
    run_test(
        "Test 1: daterange=2025-02-01 (single date, no brackets)",
        "action=summarize&res=3600&fields[]=E&daterange=2025-02-01",
        headers,
    )

    # Test 2: Comma-separated range
    run_test(
        "Test 2: daterange=2025-02-01,2025-02-02 (comma separated)",
        "action=summarize&res=3600&fields[]=E&daterange=2025-02-01,2025-02-02",
        headers,
    )

    # Test 3: Standard REST from/to params
    run_test(
        "Test 3: from=2025-02-01&to=2025-02-02 (standard REST)",
        "action=summarize&res=3600&fields[]=E&from=2025-02-01&to=2025-02-02",
        headers,
    )

    # Test 4: Named range
    run_test(
        "Test 4: daterange=last_week (named range)",
        "action=summarize&res=3600&fields[]=E&daterange=last_week",
        headers,
    )

    # Bonus Test 5: yesterday (another named range)
    run_test(
        "Test 5 (Bonus): daterange=yesterday",
        "action=summarize&res=3600&fields[]=E&daterange=yesterday",
        headers,
    )

    # Bonus Test 6: last_month
    run_test(
        "Test 6 (Bonus): daterange=last_month",
        "action=summarize&res=3600&fields[]=E&daterange=last_month",
        headers,
    )

    print(f"\n{'═' * 70}")
    print("✅ All tests complete. Check which returned historical data.")
    print('═' * 70 + '\n')


if __name__ == '__main__':
    main()
