#!/usr/bin/env python3
"""
Test multiple readings endpoint variations to find the one that returns 200.

Usage:
    python backend/python_scripts/ingest/test_readings_variations.py
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

API_URL_ORIGINAL = 'https://core.eniscope.com'
API_URL_ALT = 'https://core-lb.prod.best.energy'
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


def run_test(label: str, url: str, headers: dict):
    """Send a GET and print the status + response."""
    print(f"\n{'═' * 70}")
    print(f"🧪  {label}")
    print(f"    GET {url}")
    print('═' * 70)

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"    Status: {resp.status_code}\n")

        try:
            data = resp.json()
            formatted = json.dumps(data, indent=2, default=str)
            if len(formatted) > 6000:
                print(formatted[:6000])
                print(f"\n    ... (truncated – {len(formatted):,} chars total)")
            else:
                print(formatted)

            # Quick hit check
            is_list = isinstance(data, list)
            is_dict = isinstance(data, dict)
            has_items = False
            if is_list and len(data) > 0:
                has_items = True
            elif is_dict:
                for k in ('readings', 'records', 'data', 'result', 'items', 'values'):
                    v = data.get(k)
                    if isinstance(v, list) and len(v) > 0:
                        has_items = True
                        break

            if has_items:
                print(f"\n    ✅ GOT DATA!")
            elif resp.status_code == 200:
                print(f"\n    ⚠️  200 OK but response appears empty.")
            else:
                print(f"\n    ❌ No data (HTTP {resp.status_code}).")

        except Exception:
            text = resp.text[:2000]
            print(f"    (Not JSON) Raw text:\n{text}")

    except Exception as e:
        print(f"    ❌ Request failed: {e}")


def main():
    headers = _build_headers()

    print("⚡ Eniscope Readings – Variation Tests")
    print(f"   Channel: {CHANNEL_ID}")
    print(f"   Auth:    Basic Auth ✓\n")

    # ── Test 1: Alt domain with date strings ────────────────────────────────
    url1 = (
        f"{API_URL_ALT}/readings/{CHANNEL_ID}"
        f"?action=summarize&res=3600"
        f"&daterange[]=2025-02-01&daterange[]=2025-02-02"
        f"&fields[]=E&fields[]=P&fields[]=V"
    )
    run_test("Test 1: Alt domain (core-lb.prod.best.energy) + date strings", url1, headers)

    # ── Test 2: Original domain with Unix timestamps ────────────────────────
    url2 = (
        f"{API_URL_ORIGINAL}/readings/{CHANNEL_ID}"
        f"?action=summarize&res=3600"
        f"&daterange[]=1738368000&daterange[]=1738454400"
        f"&fields[]=E&fields[]=P&fields[]=V"
    )
    run_test("Test 2: Original domain + Unix timestamps (Feb 1–2)", url2, headers)

    # ── Test 3: Minimal – predefined range string ───────────────────────────
    url3 = (
        f"{API_URL_ORIGINAL}/readings/{CHANNEL_ID}"
        f"?action=summarize&res=3600"
        f"&daterange=today"
        f"&fields[]=E"
    )
    run_test("Test 3: Minimal – daterange=today (predefined string)", url3, headers)

    # ── Bonus Test 4: Alt domain + Unix timestamps ──────────────────────────
    url4 = (
        f"{API_URL_ALT}/readings/{CHANNEL_ID}"
        f"?action=summarize&res=3600"
        f"&daterange[]=1738368000&daterange[]=1738454400"
        f"&fields[]=E&fields[]=P&fields[]=V"
    )
    run_test("Test 4 (Bonus): Alt domain + Unix timestamps", url4, headers)

    # ── Bonus Test 5: Alt domain + minimal today ────────────────────────────
    url5 = (
        f"{API_URL_ALT}/readings/{CHANNEL_ID}"
        f"?action=summarize&res=3600"
        f"&daterange=today"
        f"&fields[]=E"
    )
    run_test("Test 5 (Bonus): Alt domain + daterange=today", url5, headers)

    print(f"\n{'═' * 70}")
    print("✅ All tests complete. Check which returned data above.")
    print('═' * 70 + '\n')


if __name__ == '__main__':
    main()
