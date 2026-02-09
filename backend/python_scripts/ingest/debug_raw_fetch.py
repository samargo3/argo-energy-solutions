"""
Debug Eniscope API probe – uses Basic Auth (matches curl from support).
"""
import os
import base64
import hashlib
import requests
from dotenv import load_dotenv
from pathlib import Path

# Governance: Path Resiliency
_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
# Override=True ensures we reload the latest .env changes
load_dotenv(_PROJECT_ROOT / '.env', override=True)

# Configuration
API_URL = os.getenv('VITE_ENISCOPE_API_URL')
API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')
EMAIL = os.getenv('VITE_ENISCOPE_EMAIL')
PASSWORD = os.getenv('VITE_ENISCOPE_PASSWORD')

def get_raw_data(site_id, date_str):
    print(f"🔍 Probing Eniscope API for Site {site_id} on {date_str}...")
    print("   Auth: Basic Auth header (matches curl from support)")

    # 1. Sanity Check Credentials
    if not all([API_KEY, EMAIL, PASSWORD]):
        print("❌ Missing env vars. Need: VITE_ENISCOPE_API_KEY, VITE_ENISCOPE_EMAIL, VITE_ENISCOPE_PASSWORD")
        return

    if not API_URL:
        print("❌ API_URL is missing")
        return

    print(f"   ℹ️  API Key: {API_KEY[:4]}... (Length: {len(API_KEY)})")
    print(f"   ℹ️  Email:   {EMAIL}")

    base_url = API_URL.rstrip('/')

    # Basic Auth header: base64("email:md5password")
    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
    auth_str = f"{EMAIL}:{password_md5}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'X-Eniscope-API': API_KEY,
        'Authorization': f'Basic {auth_b64}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }

    # Params: no credentials — auth is in the header now
    params = {
        'format': 'json',
        'action': 'summarize',
        'id': site_id,
        'res': '900',  # 15-minute resolution
        'range_start': f"{date_str} 00:00:00",
        'range_end': f"{date_str} 23:59:59",
        'fields[]': ['energy', 'power']
    }

    try:
        target_url = f"{base_url}/api"
        print(f"   Requesting: GET {target_url}")
        response = requests.get(target_url, headers=headers, params=params, timeout=30)
        print(f"   Response Status: {response.status_code}")

        if response.status_code == 401:
            print("\n❌ 401 UNAUTHORIZED. Basic Auth was rejected.")
            print("   Debug Info:")
            print(f"   - API Key: {API_KEY[:4]}...")
            print(f"   - Email:   {EMAIL}")
            print(f"   - MD5:     {password_md5[:8]}...")
        
        try:
            data = response.json()
            print(f"\n📦 RAW RESPONSE SAMPLE (First 1000 chars):\n{str(data)[:1000]}")
            
            if isinstance(data, list) and len(data) == 0:
                print("\n⚠️  WARNING: API returned an empty list [].")
        except Exception:
            print(f"   Raw Text: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    site_id = os.getenv("DEBUG_SITE_ID", "23271")
    target_date = os.getenv("DEBUG_DATE", "2025-05-15")
    get_raw_data(site_id, target_date)