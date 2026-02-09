#!/usr/bin/env python3
"""
Test different authentication approaches to identify which works.
Based on Best.Energy support guidance: "Walk up with your key, ask for data, and leave."
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
import hashlib

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

API_URL = os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

print("🧪 Testing Eniscope API Authentication Approaches\n")
print(f"API URL: {API_URL}")
print(f"API Key: {API_KEY[:4]}...{API_KEY[-4:] if API_KEY else 'MISSING'}")
print(f"Site ID: 23271\n")
print("=" * 70)

# Common headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}


def test_approach_1():
    """Approach 1: API Key Only (as header + param) - Recommended by support"""
    print("\n🔬 Test 1: API Key Only (Header + Param)")
    print("   Method: GET /api?action=summarize&apikey=...&id=23271")

    test_headers = {**headers, 'X-Eniscope-API': API_KEY}
    params = {
        'action': 'summarize',
        'apikey': API_KEY,
        'id': '23271',
        'res': '900',
        'range_start': '2025-04-29 00:00:00',
        'range_end': '2025-04-29 23:59:59',
        'format': 'json'
    }

    try:
        response = requests.get(
            f"{API_URL}/api",
            headers=test_headers,
            params=params,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Response type: {type(data)}")
            if isinstance(data, list):
                print(f"   Records returned: {len(data)}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def test_approach_2():
    """Approach 2: API Key Only (param only, no header)"""
    print("\n🔬 Test 2: API Key Only (Param Only)")
    print("   Method: GET /api?action=summarize&apikey=...")

    params = {
        'action': 'summarize',
        'apikey': API_KEY,
        'id': '23271',
        'res': '900',
        'range_start': '2025-04-29 00:00:00',
        'range_end': '2025-04-29 23:59:59',
        'format': 'json'
    }

    try:
        response = requests.get(
            f"{API_URL}/api",
            headers=headers,
            params=params,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Response type: {type(data)}")
            if isinstance(data, list):
                print(f"   Records returned: {len(data)}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def test_approach_3():
    """Approach 3: Legacy (API Key + Username + MD5 Password) - Old method"""
    print("\n🔬 Test 3: Legacy Auth (Key + Username + MD5 Password)")
    print("   Method: GET /api with all credentials")

    if not PASSWORD:
        print("   ⚠️  SKIPPED: VITE_ENISCOPE_PASSWORD not set")
        return False

    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
    test_headers = {**headers, 'X-Eniscope-API': API_KEY}
    params = {
        'action': 'summarize',
        'apikey': API_KEY,
        'username': EMAIL,
        'password': password_md5,
        'id': '23271',
        'res': '900',
        'range_start': '2025-04-29 00:00:00',
        'range_end': '2025-04-29 23:59:59',
        'format': 'json'
    }

    try:
        response = requests.get(
            f"{API_URL}/api",
            headers=test_headers,
            params=params,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Response type: {type(data)}")
            if isinstance(data, list):
                print(f"   Records returned: {len(data)}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


def test_approach_4():
    """Approach 4: Try /organizations endpoint (used by ingest script)"""
    print("\n🔬 Test 4: /organizations Endpoint (Current Ingest Method)")
    print("   Method: GET /organizations with credentials")

    if not PASSWORD:
        print("   ⚠️  SKIPPED: VITE_ENISCOPE_PASSWORD not set")
        return False

    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
    test_headers = {**headers, 'X-Eniscope-API': API_KEY}
    params = {
        'apikey': API_KEY,
        'username': EMAIL,
        'password': password_md5
    }

    try:
        response = requests.get(
            f"{API_URL}/organizations",
            headers=test_headers,
            params=params,
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Response type: {type(data)}")
            return True
        else:
            print(f"   ❌ FAILED: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    if not API_KEY:
        print("❌ VITE_ENISCOPE_API_KEY not set in .env")
        exit(1)

    results = {
        "Key Only (Header+Param)": test_approach_1(),
        "Key Only (Param)": test_approach_2(),
        "Legacy (Key+User+Pass)": test_approach_3(),
        "/organizations": test_approach_4(),
    }

    print("\n" + "=" * 70)
    print("\n📊 RESULTS SUMMARY:\n")
    for approach, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"   {approach:30} {status}")

    print("\n💡 RECOMMENDATION:")
    if results["Key Only (Header+Param)"] or results["Key Only (Param)"]:
        print("   ✅ Use API Key Only approach (Test 1 or 2)")
        print("   🔧 Update ingest_to_postgres.py to remove username/password")
    else:
        print("   ⚠️  No approach worked - contact Best.Energy support")
        print("   📧 Verify API key has correct permissions for Org 23271")
