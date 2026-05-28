#!/usr/bin/env python3
"""
import_trades.py — Bulk import MT5 history trades into your trading journal.

Usage:
    python import_trades.py                        # uses trades.json in same folder
    python import_trades.py my_trades.json         # specify a custom file
    python import_trades.py --url http://localhost:5000  # custom server URL

Setup (first time only):
    pip install requests
    Copy your credentials into the CONFIG block below.
"""

import sys
import json
import requests

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL   = "http://localhost:5500"   # Change to your server URL if deployed
USERNAME   = "trader"                  # Your journal username
PASSWORD   = "password123"             # Your journal password
# ─────────────────────────────────────────────────────────────────────────────

LOGIN_URL  = f"{BASE_URL}/auth/login"
IMPORT_URL = f"{BASE_URL}/journal/import"


def login(session: requests.Session) -> bool:
    """Log in and store the session cookie."""
    print(f"🔐 Logging in as '{USERNAME}'...")

    # First GET to grab CSRF token from the login page
    resp = session.get(LOGIN_URL)
    resp.raise_for_status()

    # Parse CSRF token from the form (Flask-WTF injects it as a hidden input)
    import re
    match = re.search(r'name="csrf_token"[^>]+value="([^"]+)"', resp.text)
    csrf_token = match.group(1) if match else ''

    payload = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrf_token': csrf_token
    }

    resp = session.post(LOGIN_URL, data=payload, allow_redirects=True)

    if 'logout' in resp.text.lower() or resp.url.endswith('/'):
        print("   ✅ Login successful.")
        return True
    else:
        print("   ❌ Login failed. Check USERNAME and PASSWORD in the CONFIG block.")
        return False


def import_trades(session: requests.Session, trades: list) -> None:
    """POST the trades JSON array to the import endpoint."""
    print(f"\n📤 Importing {len(trades)} trade(s) to {IMPORT_URL}...")

    resp = session.post(
        IMPORT_URL,
        json=trades,                            # sends Content-Type: application/json
        headers={'X-Requested-With': 'XMLHttpRequest'}
    )

    try:
        result = resp.json()
    except Exception:
        print(f"   ❌ Server returned non-JSON response (HTTP {resp.status_code}):")
        print(f"   {resp.text[:300]}")
        return

    if result.get('status') == 'success':
        print(f"\n   ✅ Import complete!")
        print(f"   📊 Imported  : {result.get('imported')} trades")
        print(f"   ⏭️  Skipped   : {result.get('skipped')} trades")
        print(f"   💰 Balance   : ${result.get('final_balance', 'N/A'):.2f}")
    else:
        print(f"\n   ❌ Import failed: {result.get('message')}")

    if result.get('errors'):
        print(f"\n   ⚠️  Errors on {len(result['errors'])} trade(s):")
        for err in result['errors']:
            print(f"      Trade #{err['index']}: {err['error']}")


def main():
    # Determine trades file path
    trades_file = sys.argv[1] if len(sys.argv) > 1 else 'trades.json'

    # Load trades JSON
    try:
        with open(trades_file, 'r') as f:
            trades = json.load(f)
        print(f"📂 Loaded {len(trades)} trade(s) from '{trades_file}'")
    except FileNotFoundError:
        print(f"❌ File not found: '{trades_file}'")
        print("   Save your parsed trades JSON as 'trades.json' in the same folder.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in '{trades_file}': {e}")
        sys.exit(1)

    # Run import with a persistent session (handles cookies automatically)
    with requests.Session() as session:
        if not login(session):
            sys.exit(1)
        import_trades(session, trades)


if __name__ == '__main__':
    main()

