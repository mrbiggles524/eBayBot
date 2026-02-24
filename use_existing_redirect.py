"""
Use an existing configured redirect URI from eBay Developer Console.
This allows you to use a redirect URI that's already set up with OAuth enabled.
"""
from ebay_oauth import eBayOAuth
from config import Config
import webbrowser

def main():
    print("=" * 80)
    print("Use Existing Redirect URI for OAuth")
    print("=" * 80)
    print()
    print("This script uses one of your existing redirect URIs from Developer Console.")
    print()
    print("First, let's check what redirect URIs you have configured:")
    print("1. Go to: https://developer.ebay.com/my/keys")
    print("2. Click 'User Tokens' for your Sandbox app")
    print("3. Scroll to 'Get a Token from eBay via Your Application'")
    print("4. Look at your redirect URL entries")
    print()
    print("Find one that has 'OAuth Enabled' checked.")
    print("Copy the 'Your auth accepted URL1' value from that entry.")
    print()
    print("=" * 80)
    print("Enter your configured redirect URI (or press Enter to use default):")
    print("=" * 80)
    print("Example: https://signin.ebay.com/ws/eBayISAPI.dll?ThirdPartyAuthSucessFailure&isAuthSuccessful=true")
    print()
    
    redirect_uri = input("Redirect URI: ").strip()
    
    if not redirect_uri:
        print("\nUsing default redirect URI from config...")
        oauth = eBayOAuth()
        redirect_uri = oauth.redirect_uri
    else:
        # Update config temporarily
        oauth = eBayOAuth()
        oauth.redirect_uri = redirect_uri
    
    print(f"\n✅ Using redirect URI: {redirect_uri}")
    print()
    print("Generating authorization URL...")
    
    # Get authorization URL
    auth_url = oauth.get_authorization_url()
    
    print("\n" + "=" * 80)
    print("Authorization URL:")
    print("=" * 80)
    print(auth_url)
    print("=" * 80)
    print()
    print("Steps:")
    print("1. Open this URL in your browser (or it will open automatically)")
    print("2. Sign in with: TESTUSER_manbot")
    print("3. Authorize the application")
    print("4. After redirect, copy the ENTIRE URL from address bar")
    print("5. Come back here and paste it")
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
    
    callback_url = input("\nRedirect URL: ").strip()
    
    if not callback_url:
        print("\nNo URL provided. Exiting.")
        return
    
    # Extract code from URL
    from urllib.parse import urlparse, parse_qs
    try:
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)
        auth_code = params.get('code', [None])[0]
        
        if not auth_code:
            # Try fragment
            if '#' in callback_url:
                fragment = callback_url.split('#')[1]
                fragment_params = parse_qs(fragment)
                auth_code = fragment_params.get('code', [None])[0]
        
        if not auth_code:
            print("\n❌ Could not find authorization code in URL.")
            print(f"   URL: {callback_url}")
            print("\n💡 The URL should contain '?code=...' or '#code=...'")
            print("\n   If the URL doesn't have a code, the redirect might be using")
            print("   a different flow. Try checking the page source or network tab.")
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
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
