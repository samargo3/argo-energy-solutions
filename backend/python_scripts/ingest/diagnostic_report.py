#!/usr/bin/env python3
"""
Comprehensive Diagnostic Report for Best.Energy API Access
Generates a detailed report of API configuration and connectivity tests.
"""
import os
import sys
import hashlib
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

def mask_secret(secret, show_chars=4):
    """Mask sensitive data while showing first/last chars for verification."""
    if not secret or len(secret) < show_chars * 2:
        return "***"
    return f"{secret[:show_chars]}...{secret[-show_chars:]}"

print("=" * 80)
print("🔍 ENISCOPE API DIAGNOSTIC REPORT")
print("=" * 80)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Environment Configuration
print("📋 ENVIRONMENT CONFIGURATION")
print("-" * 80)

API_URL = os.getenv('VITE_ENISCOPE_API_URL')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')
DB_URL = os.getenv('DATABASE_URL')

config = {
    'VITE_ENISCOPE_API_URL': API_URL,
    'VITE_ENISCOPE_API_KEY': mask_secret(API_KEY) if API_KEY else 'NOT SET',
    'VITE_ENISCOPE_EMAIL': EMAIL if EMAIL else 'NOT SET',
    'VITE_ENISCOPE_PASSWORD': '***' if PASSWORD else 'NOT SET',
    'DATABASE_URL': 'configured' if DB_URL else 'NOT SET',
}

for key, value in config.items():
    status = "✅" if value and value != 'NOT SET' else "❌"
    print(f"{status} {key:30} {value}")

print()

# 2. API Key Details
print("🔑 API KEY DETAILS")
print("-" * 80)
if API_KEY:
    print(f"Full Key (for support):  {API_KEY}")
    print(f"Masked Key:              {mask_secret(API_KEY)}")
    print(f"Key Length:              {len(API_KEY)} chars")
    print(f"Key Format:              {'Valid (32 hex)' if len(API_KEY) == 32 else 'Unexpected length'}")
else:
    print("❌ API Key not configured")

print()

# 3. Password Hash (for legacy auth troubleshooting)
print("🔐 PASSWORD HASH (Legacy Auth)")
print("-" * 80)
if PASSWORD:
    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
    print(f"MD5 Hash: {password_md5}")
    print(f"Length:   {len(password_md5)} chars")
else:
    print("⚠️  Password not set (not needed for key-only auth)")

print()

# 4. Connectivity Tests
print("🌐 CONNECTIVITY TESTS")
print("-" * 80)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

# Test 1: Base URL reachability
print("\nTest 1: Base URL Reachability")
print(f"  Target: {API_URL}")
try:
    response = requests.get(API_URL, headers=headers, timeout=10)
    print(f"  Status: {response.status_code}")
    print(f"  Result: ✅ Server reachable")
except Exception as e:
    print(f"  Result: ❌ {e}")

# Test 2: /api endpoint with key only
print("\nTest 2: /api Endpoint (Key Only - Recommended Method)")
print(f"  Target: {API_URL}/api")
print(f"  Auth:   API Key only (no username/password)")
try:
    params = {
        'action': 'summarize',
        'apikey': API_KEY,
        'id': '23271',
        'res': '900',
        'range_start': '2025-04-29 00:00:00',
        'range_end': '2025-04-29 23:59:59',
        'format': 'json'
    }
    response = requests.get(
        f"{API_URL}/api",
        headers={**headers, 'X-Eniscope-API': API_KEY},
        params=params,
        timeout=30
    )
    print(f"  Status: {response.status_code}")
    print(f"  Body:   {response.text[:100] if response.text else '(empty)'}")

    if response.status_code == 200:
        print(f"  Result: ✅ SUCCESS - API key works!")
    elif response.status_code == 401:
        print(f"  Result: ❌ 401 Unauthorized - API key rejected")
    elif response.status_code == 403:
        print(f"  Result: ❌ 403 Forbidden - API key lacks permissions")
    else:
        print(f"  Result: ⚠️  Unexpected status code")
except Exception as e:
    print(f"  Result: ❌ {e}")

# Test 3: /organizations endpoint (legacy)
if PASSWORD:
    print("\nTest 3: /organizations Endpoint (Legacy Method)")
    print(f"  Target: {API_URL}/organizations")
    print(f"  Auth:   API Key + Username + MD5 Password")
    try:
        password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
        params = {
            'apikey': API_KEY,
            'username': EMAIL,
            'password': password_md5
        }
        response = requests.get(
            f"{API_URL}/organizations",
            headers={**headers, 'X-Eniscope-API': API_KEY},
            params=params,
            timeout=30
        )
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Result: ✅ SUCCESS - Legacy auth works!")
            print(f"  Orgs:   {len(data) if isinstance(data, list) else 'Unknown'}")
        elif response.status_code == 401:
            print(f"  Result: ❌ 401 Unauthorized - Credentials rejected")
        elif response.status_code == 403:
            print(f"  Result: ❌ 403 Forbidden - Account lacks permissions")
        else:
            print(f"  Result: ⚠️  Unexpected status code")
    except Exception as e:
        print(f"  Result: ❌ {e}")

print()

# 5. Database Connectivity
print("💾 DATABASE CONNECTIVITY")
print("-" * 80)
if DB_URL:
    print(f"Database: {DB_URL.split('@')[1] if '@' in DB_URL else 'configured'}")
    try:
        import psycopg2
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM readings")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"Result:   ✅ Connected successfully")
        print(f"Readings: {count:,} records in database")
    except Exception as e:
        print(f"Result:   ❌ {e}")
else:
    print("Result:   ⚠️  DATABASE_URL not configured")

print()

# 6. Recommendations
print("=" * 80)
print("💡 RECOMMENDATIONS")
print("=" * 80)

if API_KEY and (not PASSWORD or not EMAIL):
    print("✅ Using key-only auth (recommended)")
elif API_KEY and PASSWORD and EMAIL:
    print("⚠️  Both key-only and legacy credentials configured")
    print("   Recommendation: Remove username/password, use key-only")
else:
    print("❌ API credentials incomplete")

print()
print("📧 NEXT STEPS FOR SUPPORT TICKET:")
print()
print("1. Share this diagnostic report with Best.Energy support")
print("2. Ask them to verify 'API Access' permission is enabled for:")
print(f"   - API Key: {API_KEY if API_KEY else 'NOT SET'}")
print(f"   - User:    {EMAIL if EMAIL else 'NOT SET'}")
print("3. Request they check server logs for rejection reasons")
print("4. If needed, regenerate API key with explicit permissions")
print()
print("=" * 80)
