"""Debug script to check token status."""
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Force reload .env
load_dotenv(override=True)

print("=" * 70)
print("Token Debug")
print("=" * 70)
print()

# Check .env file directly
env_file = ".env"
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    print("From .env file:")
    for line in env_content.split('\n'):
        if 'TOKEN' in line.upper() or 'OAUTH' in line.upper() or 'ENVIRONMENT' in line.upper():
            if '=' in line:
                key, value = line.split('=', 1)
                if len(value) > 50:
                    print(f"  {key}={value[:50]}...")
                else:
                    print(f"  {line}")
    print()

# Check environment variables
print("From environment variables (os.getenv):")
print(f"  USE_OAUTH: {os.getenv('USE_OAUTH', 'NOT SET')}")
print(f"  EBAY_ENVIRONMENT: {os.getenv('EBAY_ENVIRONMENT', 'NOT SET')}")
prod_token = os.getenv('EBAY_PRODUCTION_TOKEN', '')
print(f"  EBAY_PRODUCTION_TOKEN: {'Set (' + str(len(prod_token)) + ' chars)' if prod_token else 'NOT SET'}")
if prod_token:
    print(f"    Preview: {prod_token[:50]}...")
print()

# Check Config class
print("From Config class:")
from config import Config
config = Config()
print(f"  USE_OAUTH: {config.USE_OAUTH}")
print(f"  EBAY_ENVIRONMENT: {config.EBAY_ENVIRONMENT}")
print(f"  EBAY_PRODUCTION_TOKEN length: {len(config.EBAY_PRODUCTION_TOKEN) if config.EBAY_PRODUCTION_TOKEN else 0}")
token = config.ebay_token
print(f"  config.ebay_token: {'Set (' + str(len(token)) + ' chars)' if token else 'NOT SET'}")
if token:
    print(f"    Preview: {token[:50]}...")
    print(f"    First 100 chars: {token[:100]}")
print()

# Test API call
print("Testing API call...")
try:
    import requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    url = "https://api.ebay.com/sell/account/v1/payment_policy"
    response = requests.get(url, headers=headers, params={'marketplace_id': 'EBAY_US'}, timeout=10)
    print(f"  Status Code: {response.status_code}")
    if response.status_code == 200:
        print("  SUCCESS! Token is valid.")
    elif response.status_code == 401:
        print("  FAILED: 401 Unauthorized")
        try:
            error_data = response.json()
            print(f"  Error: {error_data}")
        except:
            print(f"  Response: {response.text[:500]}")
    else:
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
