"""
Test all authentication methods and endpoints to find what works.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import requests
import json

def test_with_bearer(token):
    """Test with Bearer token (OAuth 2.0 style)."""
    print("\n" + "=" * 80)
    print("Test 1: Bearer Token (OAuth 2.0 style)")
    print("=" * 80)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    try:
        response = requests.get(
            "https://api.sandbox.ebay.com/sell/account/v1/privilege",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("[SUCCESS] Bearer token works!")
            return True
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    return False

def test_without_bearer(token):
    """Test without Bearer prefix (Auth'n'Auth style)."""
    print("\n" + "=" * 80)
    print("Test 2: Direct Token (Auth'n'Auth style)")
    print("=" * 80)
    headers = {
        "X-EBAY-API-IAF-TOKEN": token,
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    try:
        response = requests.get(
            "https://api.sandbox.ebay.com/sell/account/v1/privilege",
            headers=headers
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("[SUCCESS] Direct token works!")
            return True
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    return False

def test_different_endpoints(token):
    """Test different API endpoints."""
    print("\n" + "=" * 80)
    print("Test 3: Different Endpoints")
    print("=" * 80)
    
    endpoints = [
        ("/sell/account/v1/privilege", "Account Privileges"),
        ("/sell/inventory/v1/inventory_item", "Inventory Items"),
        ("/sell/fulfillment/v1/order", "Orders"),
        ("/sell/account/v1/return_policy", "Return Policies"),
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
    }
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(
                f"https://api.sandbox.ebay.com{endpoint}",
                headers=headers,
                params={"limit": 1} if "inventory" in endpoint or "order" in endpoint else None
            )
            print(f"\n{name} ({endpoint}):")
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  [SUCCESS] {name} endpoint works!")
                data = response.json()
                print(f"  Response keys: {list(data.keys())[:5]}")
                return True
            elif response.status_code == 403:
                print(f"  [403] Insufficient permissions")
            else:
                print(f"  Response: {response.text[:150]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    return False

def test_oauth_token_info():
    """Check OAuth token information."""
    print("\n" + "=" * 80)
    print("Test 4: Check OAuth Token Info")
    print("=" * 80)
    
    try:
        import os
        if os.path.exists(".ebay_token.json"):
            with open(".ebay_token.json", "r") as f:
                token_data = json.load(f)
            print("Token data from .ebay_token.json:")
            print(f"  Token type: {token_data.get('token_type', 'N/A')}")
            print(f"  Expires in: {token_data.get('expires_in', 'N/A')} seconds")
            print(f"  Has refresh token: {'refresh_token' in token_data}")
            if 'scope' in token_data:
                print(f"  Scopes: {token_data.get('scope', 'N/A')}")
            else:
                print("  [WARNING] No scope information in token data")
    except Exception as e:
        print(f"Error reading token file: {e}")

def main():
    print("=" * 80)
    print("Testing All Authentication Methods")
    print("=" * 80)
    
    config = Config()
    token = config.ebay_token
    
    print(f"\nEnvironment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Token (first 50 chars): {token[:50]}...")
    print(f"Token format: {'v^1.1#' if token.startswith('v^1.1#') else 'Other'}")
    
    # Test 1: Bearer token
    if test_with_bearer(token):
        print("\n[SUCCESS] Bearer token method works!")
        return
    
    # Test 2: Direct token
    if test_without_bearer(token):
        print("\n[SUCCESS] Direct token method works!")
        return
    
    # Test 3: Different endpoints
    if test_different_endpoints(token):
        print("\n[SUCCESS] Found working endpoint!")
        return
    
    # Test 4: Check token info
    test_oauth_token_info()
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("\nAll tests returned 403 errors.")
    print("\nPossible solutions:")
    print("1. Sandbox account needs to be set up for Inventory API")
    print("2. Token needs to be regenerated with explicit scope selection")
    print("3. Account needs seller privileges enabled in sandbox")
    print("4. Try using the Trading API instead of Inventory API")

if __name__ == "__main__":
    main()
