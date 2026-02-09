#!/usr/bin/env python3
"""
Test using subprocess to run the EXACT curl command from the support ticket.
This helps identify if Python requests library is doing something different.
"""
import os
import subprocess
import json
from dotenv import load_dotenv
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
load_dotenv(_PROJECT_ROOT / '.env', override=True)

API_KEY = os.getenv('VITE_ENISCOPE_API_KEY')

print("🧪 Testing with EXACT curl command from support ticket\n")
print(f"API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
print("=" * 70)

# Test 1: Exact replica of Attempt 1 from ticket
print("\n🔬 Test 1: Key Only (exact replica of support ticket)")
curl_cmd = [
    'curl', '-v',
    f'https://core.eniscope.com/api?action=summarize&apikey={API_KEY}&id=23271'
]
print(f"Command: {' '.join(curl_cmd[:2])} 'https://core.eniscope.com/api?action=summarize&apikey=b800...&id=23271'")

try:
    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
    print(f"\nExit code: {result.returncode}")
    print(f"\nSTDERR (headers):")
    print(result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
    print(f"\nSTDOUT (body):")
    print(result.stdout[:500] if len(result.stdout) > 500 else result.stdout)

    if "401" in result.stderr or "Unauthorized" in result.stdout:
        print("\n❌ 401 Unauthorized - API key rejected")
    elif result.stdout and result.returncode == 0:
        print("\n✅ Request succeeded!")
        try:
            data = json.loads(result.stdout)
            print(f"Response type: {type(data)}")
            if isinstance(data, list):
                print(f"Records: {len(data)}")
        except:
            pass
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("\n💡 NEXT STEPS:")
print("   1. Check if API key has 'API Access' permission enabled")
print("   2. Verify user 'craig@argoenergysolutions.com' has permissions")
print("   3. Ask Best.Energy to check server logs for this API key")
print("   4. Consider regenerating the API key with explicit permissions")
