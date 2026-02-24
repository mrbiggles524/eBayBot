"""
Exchange the new authorization code for an access token.
"""
from ebay_oauth import eBayOAuth
from config import Config

def main():
    print("=" * 80)
    print("Exchange Authorization Code for Access Token")
    print("=" * 80)
    print()
    
    # The code from httpbin.org
    auth_code = "v^1.1#i^1#p^3#r^1#f^0#I^3#t^Ul41XzA6OEE1MTI2QkVCNEVGRjA0MjE0NzVDREVENDgwODkwMDFfMV8xI0VeMTI4NA=="
    redirect_uri = "https://httpbin.org/anything"
    
    print(f"Authorization code: {auth_code[:50]}...")
    print(f"Redirect URI: {redirect_uri}")
    print()
    print("Exchanging for access token...")
    print()
    
    oauth = eBayOAuth()
    oauth.redirect_uri = redirect_uri
    
    result = oauth.exchange_code_for_token(auth_code)
    
    if result.get('success'):
        print("\n[SUCCESS] Token saved!")
        print(f"Access token: {result.get('access_token', '')[:50]}...")
        print(f"Token type: {result.get('token_type', 'N/A')}")
        print(f"Expires in: {result.get('expires_in', 'N/A')} seconds")
        if result.get('refresh_token'):
            print(f"Refresh token: {result.get('refresh_token', '')[:50]}...")
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
        
        message = result.get('message', '')
        if message:
            print(f"\n{message}")

if __name__ == "__main__":
    main()
