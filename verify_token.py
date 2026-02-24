"""
Quick script to verify current token format.
"""
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

config = Config()
token = config.ebay_token

print("=" * 80)
print("Current Token Status")
print("=" * 80)
print()
print(f"Token (first 50 chars): {token[:50]}...")
print()

if token.startswith('v^1.1#'):
    print("[WARNING] Token is Auth'n'Auth format (won't work with Inventory API)")
    print()
    print("You need an OAuth 2.0 token instead.")
    print()
    print("To get OAuth 2.0 token:")
    print("  1. Make sure redirect URL is updated with real webhookspy ID")
    print("  2. Go to User Tokens page")
    print("  3. Select 'OAuth (new security)'")
    print("  4. Click 'Sign in to Production for OAuth'")
    print("  5. Copy the new token (should NOT start with v^1.1#)")
    print("  6. Update: python update_token.py 'your_new_token'")
else:
    print("[OK] Token appears to be OAuth 2.0 format")
    print("Testing if it works...")
    print()
    # Quick test
    from ebay_api_client import eBayAPIClient
    client = eBayAPIClient()
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 1})
        if response.status_code == 200:
            print("[SUCCESS] Token works! Keyset is enabled!")
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {e}")
