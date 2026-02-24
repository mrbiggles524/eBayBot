"""
Extract authorization code from webhookspy redirect URL.
"""
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_code():
    """Extract code from redirect URL."""
    print("=" * 80)
    print("Extract Authorization Code from Redirect URL")
    print("=" * 80)
    print()
    print("In webhookspy, click 'View in Inspector' to see the full request.")
    print("Copy the FULL URL from the browser address bar or from webhookspy.")
    print()
    print("The URL should look like:")
    print("  https://webhookspy.com/44063bc75f7a4e4893da63668303edd3?code=ABC123...")
    print()
    print("=" * 80)
    redirect_url = input("Paste the FULL redirect URL here: ").strip()
    
    if not redirect_url:
        print("[ERROR] No URL provided")
        return None
    
    # Extract code from URL
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' not in query_params:
            print("[ERROR] No 'code' parameter found in URL")
            print()
            print("The URL should contain '?code=...'")
            print(f"You provided: {redirect_url[:100]}...")
            print()
            print("Make sure you copy the FULL URL from:")
            print("  1. Browser address bar after redirect, OR")
            print("  2. Webhookspy Inspector (click 'View in Inspector')")
            return None
        
        auth_code = query_params['code'][0]
        print()
        print("=" * 80)
        print("[SUCCESS] Authorization Code Extracted!")
        print("=" * 80)
        print()
        print(f"Code: {auth_code}")
        print()
        print("=" * 80)
        print("Next: Exchange Code for Token")
        print("=" * 80)
        print()
        print("Now run:")
        print("  python get_production_oauth_token.py")
        print()
        print("When prompted, paste this URL:")
        print(f"  {redirect_url}")
        print()
        print("OR, if you want to exchange it now, the code is:")
        print(f"  {auth_code}")
        print()
        
        return auth_code
        
    except Exception as e:
        print(f"[ERROR] Failed to parse URL: {e}")
        return None

if __name__ == "__main__":
    extract_code()
