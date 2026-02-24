"""
Extract OAuth authorization code from broken redirect URL and exchange for token.
Even if the redirect page is broken, the URL contains the code we need.
"""
from ebay_oauth import eBayOAuth
from urllib.parse import urlparse, parse_qs

def main():
    print("=" * 80)
    print("Extract Token from Broken Redirect")
    print("=" * 80)
    print()
    print("Even if the redirect page is broken, the URL contains the code we need!")
    print()
    print("Steps:")
    print("1. Go to: https://developer.ebay.com/my/keys")
    print("2. Click 'User Tokens' for your Sandbox app")
    print("3. Click 'Sign in to Sandbox for OAuth'")
    print("4. Sign in with: TESTUSER_manbot")
    print("5. After authorization, you'll be redirected to a broken page")
    print("6. COPY THE ENTIRE URL from your browser's address bar")
    print("   (Even if the page is broken, the URL has the code!)")
    print()
    print("=" * 80)
    print("Paste the redirect URL here (the broken page URL):")
    print("=" * 80)
    
    redirect_url = input("\nURL: ").strip()
    
    if not redirect_url:
        print("\nNo URL provided. Exiting.")
        return
    
    # Extract code from URL
    try:
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)
        auth_code = params.get('code', [None])[0]
        
        if not auth_code:
            # Try to find code in fragment (#code=...)
            if '#' in redirect_url:
                fragment = redirect_url.split('#')[1]
                fragment_params = parse_qs(fragment)
                auth_code = fragment_params.get('code', [None])[0]
        
        if not auth_code:
            print("\n❌ Could not find authorization code in URL.")
            print(f"   URL received: {redirect_url}")
            print("\n💡 The URL should contain '?code=...' or '#code=...'")
            print("   Make sure you copied the ENTIRE URL from the address bar.")
            return
        
        print(f"\n✅ Found authorization code: {auth_code[:30]}...")
        print("Exchanging for access token...")
        print()
        
        # Exchange code for token
        oauth = eBayOAuth()
        
        # Try to use the redirect URI from the URL if possible
        callback_redirect_uri = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if callback_redirect_uri and callback_redirect_uri != oauth.redirect_uri:
            print(f"⚠️  Redirect URI mismatch detected:")
            print(f"   URL used: {callback_redirect_uri}")
            print(f"   Config expects: {oauth.redirect_uri}")
            print(f"\n   Trying with the URL's redirect URI...")
            original_redirect_uri = oauth.redirect_uri
            oauth.redirect_uri = callback_redirect_uri
        
        result = oauth.exchange_code_for_token(auth_code)
        
        # Restore original redirect URI if we changed it
        if callback_redirect_uri and callback_redirect_uri != oauth.redirect_uri:
            oauth.redirect_uri = original_redirect_uri
        
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
            
            print("\n💡 Troubleshooting:")
            print("1. Authorization codes expire quickly (usually 10 minutes)")
            print("2. Try getting a new code by clicking 'Sign in to Sandbox for OAuth' again")
            print("3. Make sure you copy the ENTIRE URL immediately after redirect")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check the URL format and try again.")

if __name__ == "__main__":
    main()
