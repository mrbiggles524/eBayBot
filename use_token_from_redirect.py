"""
Use the token from the OAuth redirect directly.
eBay seems to be returning the token in the code parameter.
"""
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

def use_token():
    """Extract and use token from redirect."""
    print("=" * 80)
    print("Extract Token from OAuth Redirect")
    print("=" * 80)
    print()
    print("eBay redirected you with a token in the 'code' parameter.")
    print("This appears to be an Auth'n'Auth token, not an OAuth code.")
    print()
    print("The redirect URL shows:")
    print("  code=v^1.1#i^1#I^3#p^3#r^1#f^0#t^...")
    print()
    print("Let's extract it and test it.")
    print()
    print("=" * 80)
    
    # The token from the redirect
    redirect_url = "https://webhookspy.com/44063bc75f7a4e4893da63668303edd3?code=v%5E1.1%23i%5E1%23I%5E3%23p%5E3%23r%5E1%23f%5E0%23t%5EUl41XzM6RDNCNDUwMTVCRDFERjZBQkJBQTJBNTRFMDcwODU1NjBfMF8xI0VeMjYw&expires_in=299"
    
    # Or get from user
    print("Paste the redirect URL (or press Enter to use the one from webhookspy):")
    user_input = input().strip()
    if user_input:
        redirect_url = user_input
    
    # Extract code/token
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' not in query_params:
            print("[ERROR] No 'code' parameter found")
            return None
        
        token = query_params['code'][0]
        expires_in = query_params.get('expires_in', [''])[0]
        
        print()
        print("=" * 80)
        print("Token Extracted")
        print("=" * 80)
        print()
        print(f"Token: {token[:50]}...")
        print(f"Expires in: {expires_in} seconds" if expires_in else "Expires in: Unknown")
        print()
        
        # Check token format
        if token.startswith('v^1.1#'):
            print("[WARNING] Token is Auth'n'Auth format (v^1.1#...)")
            print("          This is unusual for OAuth flow.")
            print("          But let's test it anyway.")
        else:
            print("[OK] Token appears to be OAuth 2.0 format")
        
        print()
        print("=" * 80)
        print("Next Steps")
        print("=" * 80)
        print()
        print("1. Update your token:")
        print(f'   python update_token.py "{token}"')
        print()
        print("2. Test the token:")
        print("   python check_keyset_status.py")
        print()
        print("3. If it works, great! If not, we may need to try a different approach.")
        print()
        
        return token
        
    except Exception as e:
        print(f"[ERROR] Failed to extract token: {e}")
        return None

if __name__ == "__main__":
    token = use_token()
    if token:
        print()
        print("=" * 80)
        print("Copy this command to update your token:")
        print("=" * 80)
        print()
        print(f'python update_token.py "{token}"')
        print()
