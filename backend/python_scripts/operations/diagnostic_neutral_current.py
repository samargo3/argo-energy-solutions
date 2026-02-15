#!/usr/bin/env python3
"""
Diagnostic: Neutral Current (In) Availability for Wilson Center

Checks whether neutral current data is returned by the Eniscope API and
populated in the readings table for Wilson Center WCDS channels.

Run: python backend/python_scripts/operations/diagnostic_neutral_current.py
     npm run py:diagnostic:neutral-current  # if added to package.json
"""
import os
import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _PKG_ROOT.parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / '.env', override=False)

# Wilson Center WCDS channels (hardware installed 2025-04-29)
WCDS_CHANNELS = [
    162119, 162120, 162121, 162122, 162123,
    162285, 162319, 162320,
]


def check_database():
    """Query readings table for neutral_current_a population per channel."""
    import psycopg2
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set")
        return None

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("""
        SELECT channel_id, COUNT(*) as total, COUNT(neutral_current_a) as with_neutral
        FROM readings
        WHERE channel_id = ANY(%s)
        GROUP BY channel_id
        ORDER BY channel_id
    """, (WCDS_CHANNELS,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def check_api(site_id: str = '23271', channel_id: int = 162285, date_str: str = '2025-05-15'):
    """Fetch one day of readings from Eniscope API with In in fields and report."""
    import base64
    import hashlib
    import requests
    from datetime import datetime

    api_url = (os.getenv('ENISCOPE_API_URL') or os.getenv('VITE_ENISCOPE_API_URL', 'https://core.eniscope.com')).rstrip('/')
    api_key = os.getenv('ENISCOPE_API_KEY') or os.getenv('VITE_ENISCOPE_API_KEY')
    email = os.getenv('ENISCOPE_EMAIL') or os.getenv('VITE_ENISCOPE_EMAIL')
    password = os.getenv('ENISCOPE_PASSWORD') or os.getenv('VITE_ENISCOPE_PASSWORD')

    if not all([api_key, email, password]):
        print("❌ Missing Eniscope env vars (ENISCOPE_API_KEY, EMAIL, PASSWORD)")
        return None

    pw_md5 = hashlib.md5(password.encode()).hexdigest()
    auth_b64 = base64.b64encode(f"{email}:{pw_md5}".encode()).decode()
    headers = {
        'X-Eniscope-API': api_key,
        'Authorization': f'Basic {auth_b64}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    dt = datetime.strptime(date_str, '%Y-%m-%d')
    ts_from = int(dt.timestamp())
    ts_to = ts_from + 86400
    field_params = '&'.join(f'fields[]={f}' for f in ['E', 'P', 'In', 'I'])
    url = (
        f"{api_url}/readings/{channel_id}"
        f"?action=summarize&res=3600"
        f"&daterange[]={ts_from}&daterange[]={ts_to}"
        f"&{field_params}"
    )

    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

    records = data.get('records') or data.get('data') or data.get('readings') or []
    has_in = sum(1 for rec in records if rec.get('In') is not None)
    return {'total': len(records), 'with_In': has_in, 'sample': records[0] if records else None}


def main():
    print("🔍 Neutral Current (In) Availability Diagnostic — Wilson Center")
    print("=" * 60)

    # 1. Database check
    print("\n1. Database: readings.neutral_current_a per WCDS channel")
    rows = check_database()
    if rows is None:
        print("   Skipped (no DATABASE_URL)")
    elif not rows:
        print("   No readings found for WCDS channels. Run ingestion first.")
    else:
        total_readings = 0
        total_with_neutral = 0
        for ch_id, total, with_neutral in rows:
            pct = (with_neutral / total * 100) if total else 0
            status = "✅" if with_neutral > 0 else "❌"
            print(f"   {status} Channel {ch_id}: {with_neutral:,}/{total:,} with neutral ({pct:.1f}%)")
            total_readings += total
            total_with_neutral += with_neutral
        overall = (total_with_neutral / total_readings * 100) if total_readings else 0
        print(f"\n   Overall: {total_with_neutral:,}/{total_readings:,} readings have neutral_current_a ({overall:.1f}%)")
        if total_with_neutral == 0:
            print("   → CONCLUSION: Neutral current (In) NOT available from Wilson Center hardware.")

    # 2. API check (optional — requires credentials)
    print("\n2. API: Direct fetch with fields[]=In for channel 162285")
    api_result = check_api()
    if api_result is None:
        print("   Skipped (missing credentials or API error)")
    else:
        total, with_in, sample = api_result['total'], api_result['with_In'], api_result['sample']
        if total == 0:
            print("   No records returned for test date.")
        else:
            pct = (with_in / total * 100) if total else 0
            print(f"   Records: {with_in}/{total} have 'In' in response ({pct:.1f}%)")
            if sample and 'In' in sample:
                print(f"   Sample In value: {sample['In']}")
            else:
                print("   Sample record keys:", list(sample.keys()) if sample else "N/A")
            if with_in == 0:
                print("   → CONCLUSION: API does not return In for this channel.")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
