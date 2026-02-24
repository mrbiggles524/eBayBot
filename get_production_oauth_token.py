"""
Get Production OAuth 2.0 token using the actual OAuth redirect flow.
This bypasses the manual token generation which gives Auth'n'Auth tokens.
"""
import requests
import base64
import webbrowser
import urllib.parse
from config import Config
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_oauth_token():
    """Get OAuth 2.0 token using redirect flow."""
    config = Config()
    
    # PRODUCTION App ID and Cert ID - use from config (.env) or set here for standalone use
    production_app_id = config.EBAY_APP_ID or os.environ.get("EBAY_APP_ID", "YOUR_APP_ID")
    production_cert_id = config.EBAY_CERT_ID or os.environ.get("EBAY_CERT_ID", "YOUR_CERT_ID")
    
    # Your redirect URL from Developer Console
    redirect_uri = "https://webhookspy.com/44063bc75f7a4e4893da63668303edd3"
    
    # OAuth scopes needed for Inventory API
    scopes = [
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
    ]
    
    # Step 1: Generate authorization URL
    auth_url = "https://auth.ebay.com/oauth2/authorize"
    params = {
        "client_id": production_app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes)
    }
    
    auth_url_full = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    print("=" * 80)
    print("Get Production OAuth 2.0 Token")
    print("=" * 80)
    print()
    print("Step 1: Authorize the application")
    print()
    print("Visit this URL in your browser:")
    print()
    print(auth_url_full)
    print()
    print("After authorizing, eBay will redirect you to:")
    print(f"  {redirect_uri}")
    print()
    print("The redirect URL will contain a 'code' parameter.")
    print("Copy the ENTIRE redirect URL (including the code) and paste it below.")
    print()
    
    # Open browser
    try:
        webbrowser.open(auth_url_full)
        print("[OK] Browser opened. Please authorize the application...")
    except:
        print("[INFO] Could not open browser automatically.")
        print("       Please copy and paste the URL above into your browser.")
    
    print()
    print("=" * 80)
    redirect_url = input("Paste the redirect URL here (with the code parameter): ").strip()
    
    if not redirect_url:
        print("[ERROR] No redirect URL provided")
        return None
    
    # Extract code from redirect URL
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' not in query_params:
            print("[ERROR] No 'code' parameter found in redirect URL")
            print(f"       URL: {redirect_url[:200]}...")
            return None
        
        auth_code = query_params['code'][0]
        print(f"[OK] Authorization code extracted: {auth_code[:20]}...")
    except Exception as e:
        print(f"[ERROR] Failed to parse redirect URL: {e}")
        return None
    
    # Step 2: Exchange code for token
    print()
    print("Step 2: Exchanging authorization code for access token...")
    
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    
    # Create Basic Auth header (using Production credentials)
    credentials = f"{production_app_id}:{production_cert_id}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=30)
        
        if response.status_code != 200:
            print(f"[ERROR] Token exchange failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            print("[ERROR] No access token in response")
            print(f"Response: {token_data}")
            return None
        
        print()
        print("=" * 80)
        print("[SUCCESS] OAuth 2.0 Token Received!")
        print("=" * 80)
        print()
        print(f"Token (first 50 chars): {access_token[:50]}...")
        print()
        
        # Check if it's OAuth 2.0 (should NOT start with v^1.1#)
        if access_token.startswith('v^1.1#'):
            print("[WARNING] Token still appears to be Auth'n'Auth format!")
            print("          This shouldn't happen with OAuth flow.")
        else:
            print("[OK] Token appears to be OAuth 2.0 format!")
        
        print()
        print("Token details:")
        print(f"  Type: {token_data.get('token_type', 'N/A')}")
        print(f"  Expires in: {token_data.get('expires_in', 'N/A')} seconds")
        print(f"  Scopes: {token_data.get('scope', 'N/A')}")
        print()
        print("=" * 80)
        print("Next Steps:")
        print("=" * 80)
        print()
        print("1. Update your token:")
        print(f'   python update_token.py "{access_token}"')
        print()
        print("2. Test the token:")
        print("   python check_keyset_status.py")
        print()
        
        return access_token
        
    except Exception as e:
        print(f"[ERROR] Failed to exchange code for token: {e}")
        return None

if __name__ == "__main__":
    token = get_oauth_token()
    if token:
        print()
        print("=" * 80)
        print("Copy this command to update your token:")
        print("=" * 80)
        print()
        print(f'python update_token.py "{token}"')
        print()
