"""Simple script to refresh eBay OAuth token."""
from ebay_oauth import eBayOAuth
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("eBay Token Refresh")
print("=" * 70)
print()

oauth = eBayOAuth()

# Check if token exists
token_data = oauth.load_token()
if not token_data:
    print("❌ No saved token found!")
    print()
    print("You need to login first:")
    print("  python ebay_bot.py --login")
    print()
    sys.exit(1)

if 'refresh_token' not in token_data:
    print("❌ No refresh token found in saved token!")
    print()
    print("You need to login again to get a new refresh token:")
    print("  python ebay_bot.py --login")
    print()
    sys.exit(1)

print("✓ Found saved token")
print(f"  Refresh token: {token_data.get('refresh_token', 'N/A')[:30]}...")
print()

print("Refreshing token...")
result = oauth.refresh_token()

if result.get('success'):
    print("✅ Token refreshed successfully!")
    print()
    print("Your policies should now load in the UI.")
    print("Refresh the page and try again.")
else:
    print("❌ Token refresh failed!")
    print(f"Error: {result.get('error')}")
    print()
    print("You may need to login again:")
    print("  python ebay_bot.py --login")
