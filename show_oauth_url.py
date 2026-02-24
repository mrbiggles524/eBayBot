"""
Show the correct OAuth 2.0 authorization URL.
This URL will redirect with a code parameter after authorization.
"""
from ebay_oauth import eBayOAuth
from config import Config
import webbrowser

def main():
    print("=" * 80)
    print("eBay OAuth 2.0 Authorization URL")
    print("=" * 80)
    print()
    
    config = Config()
    oauth = eBayOAuth()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"App ID: {config.EBAY_APP_ID}")
    print()
    
    # The issue: eBay requires HTTPS redirect URIs for OAuth 2.0
    # The redirect URI you showed is for Auth'n'Auth, not OAuth 2.0
    # We need to use a redirect URI that's registered for OAuth 2.0
    
    # Try using one of the configured redirect URIs
    # Based on what you showed, you have redirect URIs configured
    # But they might be set for Auth'n'Auth, not OAuth 2.0
    
    print("[!] IMPORTANT: The redirect URL you showed is for Auth'n'Auth.")
    print("   OAuth 2.0 requires a redirect URI that's registered for OAuth.")
    print()
    print("Let's generate the OAuth 2.0 URL with a proper redirect URI.")
    print()
    
    # Use eBay's default OAuth redirect (but this might not work if not registered)
    # Actually, we should use one of the user's configured redirect URIs
    # But we need to know which one has OAuth enabled
    
    # For now, let's try with the redirect URI from config
    redirect_uri = oauth.redirect_uri
    
    print(f"Using redirect URI: {redirect_uri}")
    print()
    print("[!] If this doesn't work, you need to:")
    print("   1. Go to Developer Console -> User Tokens")
    print("   2. Find/create a redirect URL entry with 'OAuth Enabled' checked")
    print("   3. Set 'Your auth accepted URL1' to an HTTPS URL")
    print("   4. Use that URL as the redirect_uri")
    print()
    
    # Generate OAuth URL
    auth_url = oauth.get_authorization_url()
    
    print("=" * 80)
    print("OAuth 2.0 Authorization URL:")
    print("=" * 80)
    print(auth_url)
    print("=" * 80)
    print()
    print("Steps:")
    print("1. Open this URL in your browser")
    print("2. Sign in with: TESTUSER_manbot")
    print("3. Authorize the application")
    print("4. After redirect, the URL should have ?code=... in it")
    print("5. Copy that ENTIRE URL and run: python extract_token_from_url.py")
    print()
    
    # Try to open browser
    try:
        webbrowser.open(auth_url)
        print("[OK] Opened authorization URL in browser")
    except:
        print("[!] Could not open browser. Please copy the URL above.")
    
    print()
    print("[TIP] If the redirect URL doesn't have ?code=..., it means:")
    print("   - The redirect URI isn't registered for OAuth 2.0")
    print("   - You need to create a new redirect URL entry with OAuth enabled")
    print("   - Or use ngrok to create an HTTPS tunnel")

if __name__ == "__main__":
    main()
