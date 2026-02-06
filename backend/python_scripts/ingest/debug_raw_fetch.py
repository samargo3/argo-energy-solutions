import sys
import os
import requests
import hashlib
from datetime import datetime
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

    # 1. Sanity Check Credentials
    if not PASSWORD:
        print("❌ Password not found in .env")
        return
    
    pass_len = len(PASSWORD)
    print(f"   ℹ️  Loaded Password: {PASSWORD[:2]}... (Length: {pass_len})")

    # 2. Authenticate
    if not API_URL:
        print("❌ API_URL is missing")
        return
        
    base_url = API_URL.rstrip('/')
    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()
    
    # Headers: Keep User-Agent to avoid 403 WAF blocking
    headers = {
        'X-Eniscope-API': API_KEY,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }

    # Params: PUT APIKEY BACK IN HERE. The App likely needs it.
    params = {
        'apikey': API_KEY,         # <--- RESTORED THIS
        'username': EMAIL,
        'password': password_md5,
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
        print(f"   Requesting: {target_url} (Auth: Params + Headers)")
        response = requests.get(target_url, headers=headers, params=params, timeout=30)
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 401:
             print("\n❌ 401 UNAUTHORIZED.")
             print("   Debug Info:")
             print(f"   - Email Sent: {EMAIL}")
             print(f"   - MD5 Sent:   {password_md5}")
             print(f"   - API Key:    {API_KEY[:4]}...")
        
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