"""Simple OAuth login without importing ebay_listing."""
from ebay_oauth import eBayOAuth
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("eBay OAuth Login")
print("=" * 70)
print()

oauth = eBayOAuth()

print("Starting OAuth login...")
print("This will open a browser window.")
print()

result = oauth.login()

if result.get('success'):
    print()
    print("✅ Login successful!")
    print("Your token has been saved.")
    print()
    print("Now restart the app and policies should load.")
else:
    print()
    print("❌ Login failed!")
    print(f"Error: {result.get('error')}")
    print()
    print("Please check:")
    print("  1. Your .env file has correct EBAY_APP_ID and EBAY_CERT_ID")
    print("  2. Your redirect URI matches in eBay Developer Portal")
    print("  3. You complete the authorization in the browser")
