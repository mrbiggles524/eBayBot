"""
Get a new OAuth token with explicit scope selection.
This will guide you through getting a token with all required scopes.
"""
from ebay_oauth import eBayOAuth
from config import Config
import webbrowser

def main():
    print("=" * 80)
    print("Get OAuth Token with Required Scopes")
    print("=" * 80)
    print()
    print("The current token doesn't have Inventory API permissions.")
    print("We need to get a new OAuth token with explicit scopes.")
    print()
    
    config = Config()
    oauth = eBayOAuth()
    
    # Use the httpbin redirect URI that's already configured
    oauth.redirect_uri = "https://httpbin.org/anything"
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Redirect URI: {oauth.redirect_uri}")
    print()
    print("IMPORTANT: When you authorize, make sure to check ALL permission boxes!")
    print("Especially:")
    print("  - View and manage your inventory and offers")
    print("  - View and manage your account settings")
    print("  - View and manage your order fulfillments")
    print()
    
    # Generate OAuth URL with explicit scopes
    scopes = [
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
    ]
    
    auth_url = oauth.get_authorization_url(scopes=scopes)
    
    print("=" * 80)
    print("OAuth Authorization URL:")
    print("=" * 80)
    print(auth_url)
    print("=" * 80)
    print()
    print("Steps:")
    print("1. Open this URL (or it will open automatically)")
    print("2. Sign in with: TESTUSER_manbot")
    print("3. CHECK ALL PERMISSION BOXES (especially inventory management)")
    print("4. Authorize the application")
    print("5. You'll be redirected to httpbin.org")
    print("6. Copy the 'code' value from the JSON response")
    print()
    
    try:
        webbrowser.open(auth_url)
        print("[OK] Opened authorization URL in browser")
    except:
        print("[!] Could not open browser. Please copy the URL above.")
    
    print()
    print("=" * 80)
    print("After authorization, paste the authorization code here:")
    print("=" * 80)
    print("(Get it from httpbin.org JSON response, in the 'args' -> 'code' field)")
    print()
    
    auth_code = input("Authorization code: ").strip()
    
    if not auth_code:
        print("\nNo code provided. Exiting.")
        return
    
    print(f"\n[OK] Found authorization code: {auth_code[:30]}...")
    print("Exchanging for access token...")
    print()
    
    result = oauth.exchange_code_for_token(auth_code)
    
    if result.get('success'):
        print("\n[SUCCESS] Token saved!")
        print(f"Access token: {result.get('access_token', '')[:50]}...")
        print(f"Token type: {result.get('token_type', 'N/A')}")
        if 'scope' in result:
            print(f"Scopes: {result.get('scope', 'N/A')}")
        print("\n[OK] Testing token...")
        print()
        
        # Test the token
        import test_token
        test_token.main()
    else:
        print(f"\n[ERROR] Failed to get token")
        error = result.get('error', {})
        if isinstance(error, dict):
            print(f"Error ID: {error.get('error_id', 'N/A')}")
            print(f"Error Description: {error.get('error_description', 'N/A')}")
        else:
            print(f"Error: {error}")

if __name__ == "__main__":
    main()
