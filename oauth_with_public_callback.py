"""
Use a public OAuth callback service to receive the OAuth redirect.
This bypasses the need for ngrok or a custom HTTPS domain.
"""
from ebay_oauth import eBayOAuth
from config import Config
import webbrowser
import time

def main():
    print("=" * 80)
    print("eBay OAuth 2.0 with Public Callback Service")
    print("=" * 80)
    print()
    print("Since eBay requires HTTPS redirect URIs, we'll use a public")
    print("OAuth callback service to receive the authorization code.")
    print()
    
    config = Config()
    oauth = eBayOAuth()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"App ID: {config.EBAY_APP_ID}")
    print()
    
    # Use a public OAuth callback service
    # Option 1: httpbin.org (simple, shows the full request)
    # Option 2: oauth.pstmn.io (Postman's OAuth callback service)
    
    print("We'll use httpbin.org to receive the OAuth redirect.")
    print("This is a public service that shows you the full redirect URL.")
    print()
    
    # Use httpbin.org - it will show us the full redirect with all parameters
    redirect_uri = "https://httpbin.org/anything"
    
    print(f"Using redirect URI: {redirect_uri}")
    print()
    print("[!] IMPORTANT: You need to register this redirect URI in Developer Console:")
    print("   1. Go to: https://developer.ebay.com/my/keys")
    print("   2. Click 'User Tokens' for your Sandbox app")
    print("   3. Click '+ Add eBay Redirect URL'")
    print("   4. Set 'Your auth accepted URL1' to: https://httpbin.org/anything")
    print("   5. Make sure 'OAuth Enabled' is CHECKED")
    print("   6. Save")
    print()
    
    input("Press Enter after you've registered the redirect URI in Developer Console...")
    
    oauth.redirect_uri = redirect_uri
    
    # Generate OAuth URL
    auth_url = oauth.get_authorization_url()
    
    print()
    print("=" * 80)
    print("OAuth 2.0 Authorization URL:")
    print("=" * 80)
    print(auth_url)
    print("=" * 80)
    print()
    print("Steps:")
    print("1. Open this URL in your browser (or it will open automatically)")
    print("2. Sign in with: TESTUSER_manbot")
    print("3. Authorize the application")
    print("4. You'll be redirected to httpbin.org")
    print("5. On the httpbin page, look for the 'args' section")
    print("6. Find the 'code' parameter in the JSON response")
    print("7. Copy that code value")
    print()
    
    # Try to open browser
    try:
        webbrowser.open(auth_url)
        print("[OK] Opened authorization URL in browser")
    except:
        print("[!] Could not open browser. Please copy the URL above.")
    
    print()
    print("=" * 80)
    print("After authorization, you'll see a JSON page on httpbin.org")
    print("Look for the 'code' parameter in the 'args' section")
    print("=" * 80)
    print()
    
    auth_code = input("Paste the authorization code here: ").strip()
    
    if not auth_code:
        print("\nNo code provided.")
        print("\nThe code should be in the httpbin.org response, in the 'args' section.")
        print("It looks like: 'code': 'ABC123XYZ...'")
        return
    
    print(f"\n[OK] Found authorization code: {auth_code[:30]}...")
    print("Exchanging for access token...")
    print()
    
    # Make sure we use the same redirect URI
    oauth.redirect_uri = redirect_uri
    result = oauth.exchange_code_for_token(auth_code)
    
    if result.get('success'):
        print("\n[SUCCESS] Token saved!")
        print(f"Access token: {result.get('access_token', '')[:50]}...")
        print("\n[OK] You can now use the bot!")
        print("   Run: python check_listings.py")
    else:
        print(f"\n[ERROR] Failed to get token")
        error = result.get('error', {})
        if isinstance(error, dict):
            print(f"Error ID: {error.get('error_id', 'N/A')}")
            print(f"Error Description: {error.get('error_description', 'N/A')}")
        else:
            print(f"Error: {error}")
        
        message = result.get('message', '')
        if message:
            print(f"\n{message}")

if __name__ == "__main__":
    main()
