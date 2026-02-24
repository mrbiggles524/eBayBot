"""
Test different token formats to see which works.
"""
import requests
from config import Config

def test_token_formats():
    """Test different ways to use the token."""
    config = Config()
    token = config.ebay_token
    
    print("=" * 80)
    print("Testing Token Formats")
    print("=" * 80)
    print()
    print(f"Token (first 50 chars): {token[:50]}...")
    token_type = "Auth'n'Auth" if token.startswith('v^1.1#') else "OAuth 2.0"
    print(f"Token format: {token_type}")
    print()
    
    base_url = config.ebay_api_url
    endpoint = "/sell/inventory/v1/inventory_item"
    url = f"{base_url}{endpoint}"
    
    # Test 1: Bearer token (OAuth 2.0)
    print("Test 1: Bearer Token (OAuth 2.0 format)")
    headers1 = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    try:
        response = requests.get(url, headers=headers1, params={'limit': 1})
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [SUCCESS] Bearer token works!")
            return True
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    
    # Test 2: X-EBAY-API-IAF-TOKEN (Auth'n'Auth format)
    print("Test 2: X-EBAY-API-IAF-TOKEN (Auth'n'Auth format)")
    headers2 = {
        "X-EBAY-API-IAF-TOKEN": token,
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    try:
        response = requests.get(url, headers=headers2, params={'limit': 1})
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [SUCCESS] IAF token works!")
            return True
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    
    # Test 3: Try without Bearer prefix
    print("Test 3: Direct token (no Bearer prefix)")
    headers3 = {
        "Authorization": token,
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    try:
        response = requests.get(url, headers=headers3, params={'limit': 1})
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  [SUCCESS] Direct token works!")
            return True
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("All token formats failed.")
    print()
    print("The token you have appears to be an Auth'n'Auth token.")
    print("The Inventory API requires OAuth 2.0 tokens.")
    print()
    print("You need to get an OAuth 2.0 token, not an Auth'n'Auth token.")
    print()
    print("To get OAuth 2.0 token:")
    print("  1. Go to: https://developer.ebay.com/my/keys")
    print("  2. Click 'User Tokens' for Production")
    print("  3. Make sure you're using 'OAuth (new security)' not 'Auth'n'Auth'")
    print("  4. Click 'Sign in to Production'")
    print("  5. Get the OAuth 2.0 token")
    print()
    
    return False

if __name__ == "__main__":
    test_token_formats()
