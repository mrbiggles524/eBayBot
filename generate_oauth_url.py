"""
Generate the correct OAuth 2.0 authorization URL for eBay.
This creates the proper OAuth URL that will redirect with a code parameter.
"""
from ebay_oauth import eBayOAuth
from config import Config
import webbrowser
import urllib.parse

def main():
    print("=" * 80)
    print("Generate eBay OAuth 2.0 Authorization URL")
    print("=" * 80)
    print()
    print("The URL you showed is for Auth'n'Auth, not OAuth 2.0.")
    print("We need to generate a proper OAuth 2.0 URL that will redirect with a code.")
    print()
    
    config = Config()
    oauth = eBayOAuth()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"App ID: {config.EBAY_APP_ID}")
    print()
    
    # For OAuth 2.0, we need an HTTPS redirect URI
    # Let's try using one of eBay's default OAuth redirect URIs
    print("For OAuth 2.0, we need an HTTPS redirect URI.")
    print("Since you don't have a custom HTTPS redirect URI set up,")
    print("we'll use eBay's default OAuth redirect page.")
    print()
    print("=" * 80)
    print("Enter a redirect URI (or press Enter for default):")
    print("=" * 80)
    print("Default: https://signin.ebay.com/ws/eBayISAPI.dll?ThirdPartyAuthSucessFailure")
    print("(This is eBay's default OAuth redirect page)")
    print()
    
    redirect_uri = input("Redirect URI (Enter for default): ").strip()
    
    if not redirect_uri:
        # Use eBay's default OAuth redirect
        redirect_uri = "https://signin.ebay.com/ws/eBayISAPI.dll?ThirdPartyAuthSucessFailure"
    
    oauth.redirect_uri = redirect_uri
    
    print(f"\n✅ Using redirect URI: {redirect_uri}")
    print()
    print("Generating OAuth 2.0 authorization URL...")
    print()
    
    # Generate the OAuth 2.0 URL
    auth_url = oauth.get_authorization_url()
    
    print("=" * 80)
    print("OAuth 2.0 Authorization URL:")
    print("=" * 80)
    print(auth_url)
    print("=" * 80)
    print()
    print("⚠️  IMPORTANT: This URL uses OAuth 2.0 (not Auth'n'Auth)")
    print("   After authorization, it should redirect with ?code=... in the URL")
    print()
    print("Steps:")
    print("1. Open this URL in your browser")
    print("2. Sign in with: TESTUSER_manbot")
    print("3. Authorize the application")
    print("4. After redirect, check the URL - it should have ?code=...")
    print("5. Copy the ENTIRE redirect URL")
    print()
    
    # Try to open browser
    try:
        webbrowser.open(auth_url)
        print("✅ Opened authorization URL in browser")
    except:
        print("⚠️  Could not open browser. Please copy the URL above.")
    
    print()
    print("=" * 80)
    print("After authorization, paste the redirect URL here:")
    print("=" * 80)
    print("(The URL should contain ?code=... or #code=...)")
    print()
    
    callback_url = input("Redirect URL: ").strip()
    
    if not callback_url:
        print("\nNo URL provided.")
        print("\n💡 If the redirect URL doesn't have a code, it means:")
        print("   1. The redirect URI isn't registered for OAuth 2.0")
        print("   2. eBay is using Auth'n'Auth flow instead")
        print("   3. You need to register an HTTPS redirect URI in Developer Console")
        return
    
    # Check if URL has code
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    auth_code = params.get('code', [None])[0]
    
    if not auth_code and '#' in callback_url:
        fragment = callback_url.split('#')[1]
        fragment_params = parse_qs(fragment)
        auth_code = fragment_params.get('code', [None])[0]
    
    if not auth_code:
        print(f"\n❌ No authorization code found in URL: {callback_url}")
        print("\n💡 This means the redirect is using Auth'n'Auth, not OAuth 2.0.")
        print("\n   To fix this, you need to:")
        print("   1. Go to Developer Console → User Tokens")
        print("   2. Create a NEW redirect URL entry")
        print("   3. Set 'Your auth accepted URL1' to an HTTPS URL")
        print("   4. Make sure 'OAuth Enabled' is CHECKED")
        print("   5. Use that redirect URI in the authorization URL")
        print("\n   OR use ngrok to create an HTTPS tunnel to localhost")
        return
    
    print(f"\n✅ Found authorization code: {auth_code[:30]}...")
    print("Exchanging for access token...")
    print()
    
    # Make sure we use the same redirect URI
    oauth.redirect_uri = redirect_uri
    result = oauth.exchange_code_for_token(auth_code)
    
    if result.get('success'):
        print("\n🎉 SUCCESS! Token saved!")
        print(f"Access token: {result.get('access_token', '')[:50]}...")
        print("\n✅ You can now use the bot!")
        print("   Run: python check_listings.py")
    else:
        print(f"\n❌ Failed to get token")
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
