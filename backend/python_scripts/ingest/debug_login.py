import os
import hashlib
from pathlib import Path

import requests
from dotenv import load_dotenv


# Governance: Path Resiliency
_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent

# Override=True ensures we reload the latest .env changes
load_dotenv(_PROJECT_ROOT / ".env", override=True)


# Configuration
API_URL = os.getenv("VITE_ENISCOPE_API_URL")
API_KEY = os.getenv("VITE_ENISCOPE_API_KEY")
EMAIL = os.getenv("VITE_ENISCOPE_EMAIL")
PASSWORD = os.getenv("VITE_ENISCOPE_PASSWORD")

# Trim accidental whitespace from sensitive values
EMAIL = EMAIL.strip() if EMAIL else EMAIL
PASSWORD = PASSWORD.strip() if PASSWORD else PASSWORD


def test_login() -> None:
    print(f"🔐 Testing Login for {EMAIL}...")

    if not PASSWORD:
        print("❌ Password missing.")
        return

    if not API_URL:
        print("❌ API_URL missing.")
        return

    if not API_KEY:
        print("❌ API_KEY missing.")
        return

    base_url = API_URL.rstrip("/")

    # Hash password
    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()

    # Login parameters (API key usually required here too)
    params = {
        "action": "login",
        "username": EMAIL,
        "password": password_md5,
        "apikey": API_KEY,
        "format": "json",
    }

    # Headers to bypass WAF
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
        "X-Eniscope-API": API_KEY,
    }

    try:
        # Use a Session object
        s = requests.Session()
        target_url = f"{base_url}/api"

        print(f"   POSTing to: {target_url} (action=login)")
        # Note: Some APIs prefer POST for login, some GET. We try POST first.
        response = s.post(target_url, params=params, headers=headers, timeout=30)

        print(f"   Response Status: {response.status_code}")

        try:
            data = response.json()
            print(f"\n📦 RESPONSE:\n{data}")

            # Check 1: Token in Headers
            header_token = response.headers.get("x-eniscope-token")

            # Check 2: Token in Body (sometimes called 'token' or 'session_id')
            body_token = data.get("token") or data.get("session_id")

            if header_token:
                print(f"\n✅ SUCCESS! Token found in Headers: {header_token[:15]}...")
            elif body_token:
                print(f"\n✅ SUCCESS! Token found in Body: {body_token[:15]}...")
            elif data.get("status") == "success" or data.get("Status") == "Success":
                print("\n✅ SUCCESS! Logged in (Check cookies if no token visible).")
            else:
                print("\n❌ LOGIN FAILED. Server message likely explains why.")
        except Exception:  # noqa: BLE001
            print(f"   Raw Text: {response.text[:500]}")
    except Exception as e:  # noqa: BLE001
        print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    test_login()

