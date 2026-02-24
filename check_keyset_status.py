"""
Check if eBay Production Keyset is enabled.
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
from ebay_api_client import eBayAPIClient
from config import Config
import json

def check_keyset_status():
    """Check if production keyset is enabled by making a test API call."""
    print("=" * 80)
    print("Checking eBay Production Keyset Status")
    print("=" * 80)
    print()
    
    config = Config()
    
    # Check current environment
    current_env = config.EBAY_ENVIRONMENT.lower()
    print(f"Current Environment: {current_env.upper()}")
    print(f"API URL: {config.ebay_api_url}")
    print()
    
    if current_env != 'production':
        print("[WARNING] Not in production environment!")
        print("To check production keyset, you need to be in production mode.")
        print()
        print("To switch to production:")
        print("  1. Run: python switch_to_production.py")
        print("  2. Then run this script again")
        print()
        return
    
    # Check if we have a token
    if not config.ebay_token:
        print("[ERROR] No production token found!")
        print("You need to:")
        print("  1. Set up OAuth (run: python -m streamlit run start.py, go to Step 2)")
        print("  2. Or set EBAY_PRODUCTION_TOKEN in .env")
        print()
        return
    
    print("Token found: Yes")
    print()
    print("Making test API call to check keyset status...")
    print()
    
    # Try to make a simple API call
    # We'll try to get account privileges or inventory items
    client = eBayAPIClient()
    
    # Test 1: Try to get inventory items (simple call)
    print("Test 1: Checking Inventory API access...")
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 1})
        
        if response.status_code == 200:
            print("[OK] Keyset appears to be ENABLED!")
            print("   - API call succeeded")
            print("   - You can use production environment")
            print()
            return True
        elif response.status_code == 401:
            error_text = response.text.lower()
            if 'invalid_client' in error_text or 'client authentication failed' in error_text:
                print("[WARNING] Client authentication failed!")
                print("   - This often means your PRODUCTION keyset is DISABLED")
                print("   - Or your production credentials are incorrect")
                print("   - Check eBay Developer Console for keyset status")
                print()
            else:
                print("[ERROR] Authentication failed")
                print("   - This might be a token issue")
                print("   - Or keyset might be disabled")
                print("   - Check your OAuth token and keyset status")
                print()
        elif response.status_code == 403:
            print("[ERROR] Access forbidden")
            print("   - This could indicate keyset is disabled")
            print("   - Or insufficient permissions")
            print()
        else:
            print(f"[INFO] Got status code: {response.status_code}")
            error_text = response.text[:500]
            print(f"Response: {error_text}")
            print()
            
            # Check for specific keyset-related errors
            if 'disabled' in error_text.lower() or 'keyset' in error_text.lower():
                print("[WARNING] Keyset might be DISABLED!")
                print()
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Exception occurred: {error_msg}")
        print()
        
        if 'disabled' in error_msg.lower() or 'keyset' in error_msg.lower():
            print("[WARNING] Keyset appears to be DISABLED!")
            print()
    
    # Test 2: Try Account API
    print("Test 2: Checking Account API access...")
    try:
        response = client._make_request('GET', '/sell/account/v1/privilege')
        
        if response.status_code == 200:
            print("[OK] Keyset appears to be ENABLED!")
            print("   - Account API call succeeded")
            print("   - You can use production environment")
            print()
            return True
        else:
            error_text = response.text[:500]
            print(f"Status: {response.status_code}")
            print(f"Response: {error_text}")
            print()
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Exception: {error_msg}")
        print()
    
    # If we get here, keyset might be disabled
    print("=" * 80)
    print("[WARNING] Keyset Status: UNKNOWN or DISABLED")
    print("=" * 80)
    print()
    print("What this means:")
    print("  - Your production keyset might be disabled")
    print("  - eBay requires you to set up notifications before enabling production")
    print()
    print("How to Enable Production Keyset:")
    print()
    print("Option 1: Set Up Notifications (Recommended)")
    print("  1. Go to https://developer.ebay.com/")
    print("  2. Navigate to: Application Keys -> Your Production App")
    print("  3. Click 'Alerts & Notifications' or 'Notifications'")
    print("  4. Find 'Marketplace Account Deletion' section")
    print("  5. Choose one:")
    print("     - Email notification: Enter your email")
    print("     - Webhook endpoint: Enter an HTTPS URL")
    print("  6. Click 'Save'")
    print("  7. Your keyset should be enabled automatically")
    print()
    print("Option 2: Apply for Exemption")
    print("  1. Look for 'Apply for an exemption' link in Developer Console")
    print("  2. Fill out the exemption request form")
    print("  3. Wait for eBay's approval")
    print()
    print("Verify Keyset is Enabled:")
    print("  1. Go to https://developer.ebay.com/")
    print("  2. Navigate to: Application Keys")
    print("  3. Check your Production keyset")
    print("  4. It should NOT say 'Your Keyset is currently disabled'")
    print("  5. You should see your App ID, Dev ID, and Cert ID")
    print()
    print("For now, you can:")
    print("  - Use Sandbox environment (keyset is already enabled)")
    print("  - Test all functionality in sandbox")
    print("  - Switch to production after keyset is enabled")
    print()
    
    return False

if __name__ == "__main__":
    try:
        check_keyset_status()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
