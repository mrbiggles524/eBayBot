"""
Check what scopes the current token has.
"""
from config import Config
from ebay_api_client import eBayAPIClient

def check_token_scopes():
    """Check token scopes."""
    print("=" * 80)
    print("Checking Production Token Scopes")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Token found: {bool(config.ebay_token)}")
    print()
    
    # Try to get account privileges to see what scopes we have
    print("Checking token permissions...")
    try:
        response = client._make_request('GET', '/sell/account/v1/privilege')
        
        if response.status_code == 200:
            data = response.json()
            print("[OK] Token is valid and has access!")
            print()
            print("Account privileges:")
            print(json.dumps(data, indent=2))
            return True
        elif response.status_code == 403:
            print("[WARNING] Access denied (403)")
            print("This could mean:")
            print("  1. Keyset is still being activated (wait 10-30 minutes)")
            print("  2. Token doesn't have required scopes")
            print("  3. Keyset might still be disabled")
            print()
            print("Check Developer Console:")
            print("  - Go to: https://developer.ebay.com/my/keys")
            print("  - Check if Production keyset still says 'Non Compliant'")
            print("  - If it does, wait a bit longer for activation")
        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    return False

if __name__ == "__main__":
    import json
    check_token_scopes()
