"""
Simple script to get OAuth token via command line.
This bypasses the redirect issues by showing you the URL directly.
"""
from ebay_oauth import eBayOAuth
from config import Config

def main():
    print("=" * 80)
    print("eBay OAuth Token Generator")
    print("=" * 80)
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"API URL: {config.ebay_api_url}")
    print()
    
    oauth = eBayOAuth()
    
    # Get authorization URL
    auth_url = oauth.get_authorization_url()
    
    print("Step 1: Open this URL in your browser:")
    print("-" * 80)
    print(auth_url)
    print("-" * 80)
    print()
    print("Step 2: Sign in and authorize the application")
    print("Step 3: After authorization, you'll be redirected to a URL like:")
    print("   http://localhost:8080/callback?code=...")
    print()
    print("Step 4: Copy the ENTIRE redirect URL (the full URL with ?code=...)")
    print()
    
    # Try to open browser automatically
    import webbrowser
    try:
        webbrowser.open(auth_url)
        print("✅ Opened authorization URL in your browser")
    except:
        print("⚠️  Could not open browser automatically. Please copy the URL above.")
    
    print()
    print("=" * 80)
    print("After you get redirected, paste the FULL redirect URL here:")
    print("=" * 80)
    
    redirect_url = input("\nPaste the redirect URL here: ").strip()
    
    if not redirect_url:
        print("No URL provided. Exiting.")
        return
    
    # Extract code and redirect URI from URL
    from urllib.parse import urlparse, parse_qs, urlunparse
    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)
    auth_code = params.get('code', [None])[0]
    
    if not auth_code:
        print("❌ Could not find authorization code in URL.")
        print(f"   URL received: {redirect_url}")
        print("\n💡 The URL should contain ?code=... or &code=...")
        return
    
    # Extract the base redirect URI from the callback URL (everything before ?)
    callback_redirect_uri = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    print(f"\n✅ Found authorization code: {auth_code[:20]}...")
    print(f"Callback redirect URI: {callback_redirect_uri}")
    print(f"Configured redirect URI: {oauth.redirect_uri}")
    
    # Use the redirect URI from the callback if it's different
    if callback_redirect_uri != oauth.redirect_uri:
        print(f"\n⚠️  Warning: Redirect URI mismatch!")
        print(f"   Callback used: {callback_redirect_uri}")
        print(f"   Config expects: {oauth.redirect_uri}")
        print(f"\n   Using the callback redirect URI for token exchange...")
        # Temporarily override redirect URI
        original_redirect_uri = oauth.redirect_uri
        oauth.redirect_uri = callback_redirect_uri
    
    print("Exchanging for access token...")
    print()
    
    # Exchange code for token
    result = oauth.exchange_code_for_token(auth_code)
    
    # Restore original redirect URI if we changed it
    if callback_redirect_uri != oauth.redirect_uri:
        oauth.redirect_uri = original_redirect_uri
    
    if result.get('success'):
        print("\n🎉 SUCCESS! Token saved!")
        print(f"Access token: {result.get('access_token', '')[:50]}...")
        print("\nYou can now use the bot!")
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
        print("1. Make sure the redirect URI is registered in eBay Developer Console:")
        print(f"   Go to: https://developer.ebay.com/my/keys")
        print(f"   Find your Sandbox app and add this redirect URI:")
        print(f"   {oauth.redirect_uri}")
        print("2. The redirect URI must match EXACTLY (including http vs https)")
        print("3. Authorization codes expire quickly - try getting a new one")

if __name__ == "__main__":
    main()
