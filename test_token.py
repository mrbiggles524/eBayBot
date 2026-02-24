"""Quick script to test if token is working."""
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()

config = Config()

print("=" * 70)
print("Token Test")
print("=" * 70)
print()

print(f"USE_OAUTH: {config.USE_OAUTH}")
print(f"EBAY_ENVIRONMENT: {config.EBAY_ENVIRONMENT}")
print()

if config.USE_OAUTH:
    print("OAuth Mode:")
    refresh_token = os.getenv('EBAY_REFRESH_TOKEN', '')
    print(f"  EBAY_REFRESH_TOKEN: {'Set' if refresh_token else 'NOT SET'}")
    if refresh_token:
        print(f"  Token preview: {refresh_token[:50]}...")
    
    # Check OAuth token file
    if os.path.exists('.ebay_token.json'):
        import json
        with open('.ebay_token.json', 'r') as f:
            oauth_data = json.load(f)
            print(f"  .ebay_token.json exists")
            print(f"  Has access_token: {'access_token' in oauth_data}")
            if 'expires_at' in oauth_data:
                import time
                expires_in = oauth_data['expires_at'] - time.time()
                print(f"  Expires in: {int(expires_in/60)} minutes")
    else:
        print("  .ebay_token.json does NOT exist")
else:
    print("User Token Mode:")
    print(f"  EBAY_PRODUCTION_TOKEN: {'Set' if config.EBAY_PRODUCTION_TOKEN else 'NOT SET'}")
    if config.EBAY_PRODUCTION_TOKEN:
        print(f"  Token preview: {config.EBAY_PRODUCTION_TOKEN[:50]}...")

print()
print("Current token (from config.ebay_token):")
token = config.ebay_token
if token:
    print(f"  Token: {token[:50]}...")
    print(f"  Length: {len(token)} characters")
else:
    print("  ❌ NO TOKEN AVAILABLE!")

print()
print("Testing API call...")
try:
    from ebay_api_client import eBayAPIClient
    client = eBayAPIClient()
    print(f"  API Client initialized")
    print(f"  Token in client: {client.token[:50] if client.token else 'NONE'}...")
    
    # Try a simple API call
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        print("  ✅ Token is VALID! API call succeeded.")
    elif resp.status_code == 401:
        print("  ❌ Token is EXPIRED or INVALID (401 Unauthorized)")
        print(f"  Response: {resp.text[:200]}")
    else:
        print(f"  ⚠️  API returned status {resp.status_code}")
        print(f"  Response: {resp.text[:200]}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
