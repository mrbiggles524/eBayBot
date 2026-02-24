"""
Diagnose persistent 403 errors after keyset exemption approval.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def diagnose_403():
    """Diagnose why we're getting 403 errors."""
    print("=" * 80)
    print("Diagnosing 403 Error (8+ Hours After Exemption)")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Token present: {bool(config.ebay_token)}")
    print(f"Use OAuth: {config.USE_OAUTH}")
    print()
    
    # Test 1: Try different endpoints
    print("Test 1: Try Account API (Privilege endpoint)...")
    try:
        response = client._make_request('GET', '/sell/account/v1/privilege')
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [OK] Account API works!")
        elif response.status_code == 403:
            error_data = response.json() if response.text else {}
            print(f"  [403] Error: {json.dumps(error_data, indent=2)}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    
    # Test 2: Try Inventory API
    print("Test 2: Try Inventory API (inventory_item endpoint)...")
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 1})
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [OK] Inventory API works!")
        elif response.status_code == 403:
            error_data = response.json() if response.text else {}
            print(f"  [403] Error: {json.dumps(error_data, indent=2)}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    
    # Test 3: Check if it's a scope issue
    print("Test 3: Try a simpler endpoint (if available)...")
    try:
        # Try to get user info or something basic
        response = client._make_request('GET', '/sell/account/v1/return_policy')
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [OK] Basic API works!")
        elif response.status_code == 403:
            print("  [403] Still getting access denied")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    print("=" * 80)
    print("Diagnosis Summary")
    print("=" * 80)
    print()
    print("After 8 hours, persistent 403 errors suggest:")
    print()
    print("1. Keyset might not be fully enabled despite exemption approval")
    print("   - Check Developer Console: https://developer.ebay.com/my/keys")
    print("   - Verify exemption is still active")
    print("   - Look for any warning messages")
    print()
    print("2. Token might not have required scopes")
    print("   - Try getting a new token from User Tokens page")
    print("   - Make sure you select all scopes when generating")
    print()
    print("3. There might be additional requirements")
    print("   - Check if there are any pending actions in Developer Console")
    print("   - Verify your eBay seller account is in good standing")
    print()
    print("4. Contact eBay Developer Support")
    print("   - This is unusual after 8 hours")
    print("   - Provide App ID: YourName-BOT-PRD-xxxxxxxxxx")
    print("   - Explain: 'Exemption approved 8+ hours ago but still getting 403'")
    print()
    print("RECOMMENDED: Contact eBay Developer Support")
    print("  - Go to: https://developer.ebay.com/")
    print("  - Look for 'Support' or 'Contact Us'")
    print("  - Explain the situation")
    print()

if __name__ == "__main__":
    diagnose_403()
