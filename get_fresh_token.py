"""
Get a fresh OAuth token after opting into seller programs.
This ensures the token has all the required scopes.
"""
from ebay_oauth import eBayOAuth
from config import Config
import json

def main():
    print("=" * 80)
    print("Get Fresh OAuth Token (After Seller Opt-In)")
    print("=" * 80)
    print()
    
    config = Config()
    oauth = eBayOAuth()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    print("Since you've opted into SELLING_POLICY_MANAGEMENT, you need a NEW token")
    print("that was obtained AFTER the opt-in. The old token doesn't have the right scopes.")
    print()
    print("=" * 80)
    print("Step 1: Generate OAuth Authorization URL")
    print("=" * 80)
    print()
    
    # Generate URL with explicit scopes
    scopes = [
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
    ]
    
    auth_url = oauth.get_authorization_url(scopes=scopes)
    
    print("Open this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("=" * 80)
    print("Step 2: Authorize and Get Code")
    print("=" * 80)
    print()
    print("After authorizing, you'll be redirected to httpbin.org")
    print("Copy the FULL redirect URL (including the 'code' parameter)")
    print()
    print("Example:")
    print("https://httpbin.org/anything?code=v^1.1#i^1#...&expires_in=299")
    print()
    
    redirect_url = input("Paste the redirect URL here: ").strip()
    
    if not redirect_url:
        print("[ERROR] No URL provided!")
        return
    
    print()
    print("=" * 80)
    print("Step 3: Exchange Code for Token")
    print("=" * 80)
    print()
    
    # Extract code from URL
    from urllib.parse import urlparse, parse_qs
    
    try:
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        
        if not code:
            print("[ERROR] Could not extract code from URL!")
            print(f"URL: {redirect_url[:200]}")
            return
        
        print(f"[OK] Extracted code: {code[:50]}...")
        print()
        
        # Exchange for token
        result = oauth.exchange_code_for_token(code)
        
        if result.get('success'):
            print("[OK] Token obtained successfully!")
            print()
            print("Token saved to .ebay_token.json")
            print()
            print("=" * 80)
            print("Step 4: Verify Token")
            print("=" * 80)
            print()
            
            # Test the token
            from ebay_api_client import eBayAPIClient
            client = eBayAPIClient()
            
            # Check privileges
            print("Checking seller privileges...")
            priv_response = client._make_request('GET', '/sell/account/v1/privilege')
            if priv_response.status_code == 200:
                privileges = priv_response.json()
                seller_reg = privileges.get('sellerRegistrationCompleted', False)
                print(f"Seller Registration: {seller_reg}")
            
            print()
            print("Testing Inventory API access...")
            inv_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 1})
            
            if inv_response.status_code == 200:
                print("[OK] Inventory API accessible! Token has sell.inventory scope!")
                print("[OK] You should be able to create listings now!")
            elif inv_response.status_code == 403:
                print("[ERROR] Still getting 403 - token might not have scopes yet")
                print("Wait a few minutes and try again, or contact eBay support")
            else:
                print(f"[INFO] Status {inv_response.status_code}: {inv_response.text[:200]}")
                
        else:
            print(f"[ERROR] Failed to get token: {result.get('error')}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
