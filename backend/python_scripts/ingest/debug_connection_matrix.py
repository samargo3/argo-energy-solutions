import os
import hashlib
from pathlib import Path

import requests
from dotenv import load_dotenv


# Governance: Path Resiliency
_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=True)


API_KEY = os.getenv("VITE_ENISCOPE_API_KEY")
EMAIL = os.getenv("VITE_ENISCOPE_EMAIL")
PASSWORD = os.getenv("VITE_ENISCOPE_PASSWORD")

# Trim accidental whitespace
EMAIL = EMAIL.strip() if EMAIL else EMAIL
PASSWORD = PASSWORD.strip() if PASSWORD else PASSWORD


def run_matrix() -> None:
    print("🕵️‍♂️ Starting Connection Matrix Probe...")

    if not PASSWORD:
        print("❌ Password missing.")
        return

    if not EMAIL:
        print("❌ Email missing.")
        return

    if not API_KEY:
        print("❌ API key missing.")
        return

    password_md5 = hashlib.md5(PASSWORD.encode()).hexdigest()

    # 1. Define the Variations
    env_url = os.getenv("VITE_ENISCOPE_API_URL") or ""
    env_url = env_url.rstrip("/") if env_url else ""

    endpoints = [
        env_url,  # Your current config (may be empty)
        "https://api.best.energy",
        "https://core.eniscope.com",
    ]
    # Deduplicate and drop empties while preserving order
    seen = set()
    endpoints = [
        e for e in endpoints if e and (e not in seen and not seen.add(e))  # type: ignore[arg-type]
    ]

    methods = ["GET", "POST"]

    # Base payload
    payload = {
        "action": "login",
        "username": EMAIL,
        "password": password_md5,
        "apikey": API_KEY,
        "format": "json",
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Eniscope-API": API_KEY,
    }

    print(f"{'ENDPOINT':<30} | {'METHOD':<5} | {'TYPE':<10} | {'STATUS':<6} | {'RESULT'}")
    print("-" * 80)

    for base_url in endpoints:
        url = f"{base_url}/api"

        for method in methods:
            # Strategy 1: Params (Query String) - Standard for GET, sometimes POST
            try:
                if method == "GET":
                    r = requests.get(url, params=payload, headers=headers, timeout=10)
                else:
                    r = requests.post(url, params=payload, headers=headers, timeout=10)

                status = r.status_code
                try:
                    data = r.json()
                    token = (
                        data.get("token")
                        or data.get("session_id")
                        or r.headers.get("x-eniscope-token")
                    )
                    if token:
                        result = "✅ TOKEN FOUND"
                    else:
                        result = "❌ No Token"
                    if status == 401:
                        result = "⛔ 401 Auth"
                    elif status == 403:
                        result = "⛔ 403 Forbidden"
                except Exception:  # noqa: BLE001
                    result = "⚠️ Non-JSON"

                print(f"{base_url:<30} | {method:<5} | {'Params':<10} | {status:<6} | {result}")
            except Exception as e:  # noqa: BLE001
                print(
                    f"{base_url:<30} | {method:<5} | {'Params':<10} | "
                    f"{'ERR':<6} | {str(e)[:60]}"
                )

            # Strategy 2: JSON Body (POST only)
            if method == "POST":
                try:
                    r = requests.post(url, json=payload, headers=headers, timeout=10)
                    status = r.status_code
                    try:
                        data = r.json()
                        token = (
                            data.get("token")
                            or data.get("session_id")
                            or r.headers.get("x-eniscope-token")
                        )
                        if token:
                            result = "✅ TOKEN FOUND"
                        else:
                            result = "❌ No Token"
                        if status == 401:
                            result = "⛔ 401 Auth"
                        elif status == 403:
                            result = "⛔ 403 Forbidden"
                    except Exception:  # noqa: BLE001
                        result = "⚠️ Non-JSON"
                    print(f"{base_url:<30} | {method:<5} | {'JSON':<10} | {status:<6} | {result}")
                except Exception as e:  # noqa: BLE001
                    print(
                        f"{base_url:<30} | {method:<5} | {'JSON':<10} | "
                        f"{'ERR':<6} | {str(e)[:60]}"
                    )


if __name__ == "__main__":
    run_matrix()

