"""
Diagnose OAuth "unauthorized_client" error.
"""
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def diagnose():
    """Diagnose OAuth configuration issues."""
    config = Config()
    
    print("=" * 80)
    print("OAuth Configuration Diagnosis")
    print("=" * 80)
    print()
    
    print("Current Configuration:")
    print(f"  App ID (Client ID): {config.EBAY_APP_ID}")
    print(f"  Cert ID (Client Secret): {config.EBAY_CERT_ID[:20]}..." if config.EBAY_CERT_ID else "  Cert ID: NOT SET")
    print(f"  Environment: {config.EBAY_ENVIRONMENT}")
    print()
    
    # Check redirect URI
    redirect_uri = "https://webhookspy.com/44063bc75f7a4e4893da63668303edd3"
    print(f"Redirect URI being used: {redirect_uri}")
    print()
    
    print("=" * 80)
    print("Common Causes of 'unauthorized_client' Error")
    print("=" * 80)
    print()
    
    print("1. Redirect URI Mismatch")
    print("   - The redirect URI in your code must match EXACTLY what's in Developer Console")
    print("   - Check for:")
    print("     * Trailing slashes (https://example.com vs https://example.com/)")
    print("     * Protocol (http vs https)")
    print("     * Path differences (/callback vs no path)")
    print()
    
    print("2. App ID (Client ID) Mismatch")
    print(f"   - Your App ID: {config.EBAY_APP_ID}")
    print("   - Make sure this matches your Production App ID in Developer Console")
    print("   - Production App ID should contain 'PRD' (not 'SBX')")
    print()
    
    print("3. OAuth Not Enabled for Redirect URI")
    print("   - In Developer Console, find your redirect URL entry")
    print("   - Make sure 'OAuth Enabled' checkbox is CHECKED")
    print("   - If it's only checked for 'Auth'n'Auth', OAuth won't work")
    print()
    
    print("=" * 80)
    print("How to Fix")
    print("=" * 80)
    print()
    
    print("Step 1: Verify Redirect URI in Developer Console")
    print("   1. Go to: https://developer.ebay.com/my/keys")
    print("   2. Click 'Production' tab")
    print("   3. Click 'User Tokens'")
    print("   4. Scroll to 'Your eBay Sign-in Settings'")
    print("   5. Find your redirect URL entry")
    print("   6. Check 'Your auth accepted URL1' - it should be:")
    print(f"      {redirect_uri}")
    print("   7. Make sure 'OAuth Enabled' is CHECKED (not just 'Auth'n'Auth')")
    print()
    
    print("Step 2: Verify App ID")
    print("   1. In Developer Console, check your Production App ID")
    print("   2. It should be: YourName-BOT-PRD-xxxxxxxxxx")
    print(f"   3. Your config has: {config.EBAY_APP_ID}")
    print("   4. They must match exactly")
    print()
    
    print("Step 3: Try Again")
    print("   After verifying the above, run:")
    print("   python get_production_oauth_token.py")
    print()
    
    print("=" * 80)
    print("Alternative: Check Redirect URI Format")
    print("=" * 80)
    print()
    print("Your redirect URI in Developer Console might be:")
    print("  - https://webhookspy.com/44063bc75f7a4e4893da63668303edd3")
    print("  - https://webhookspy.com/44063bc75f7a4e4893da63668303edd3/")
    print("  - https://webhookspy.com/44063bc75f7a4e4893da63668303edd3/callback")
    print()
    print("The script uses the first one. If your Developer Console has a different")
    print("format, update the script to match EXACTLY.")
    print()

if __name__ == "__main__":
    diagnose()
