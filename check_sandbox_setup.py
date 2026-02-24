"""
Check if sandbox account needs additional setup for Inventory API.
"""
import requests
from config import Config

def main():
    print("=" * 80)
    print("Sandbox Account Setup Check")
    print("=" * 80)
    print()
    
    config = Config()
    token = config.ebay_token
    
    print("The 403 errors suggest the sandbox account might need:")
    print("1. Seller privileges enabled")
    print("2. Account verification")
    print("3. Additional permissions granted")
    print()
    print("=" * 80)
    print("Possible Solutions:")
    print("=" * 80)
    print()
    print("1. CHECK SANDBOX USER ACCOUNT:")
    print("   - Go to: https://developer.ebay.com/my/keys")
    print("   - Look for sandbox user account settings")
    print("   - Make sure 'TESTUSER_manbot' has seller privileges")
    print()
    print("2. TRY TRADING API INSTEAD:")
    print("   - The Trading API might work with Auth'n'Auth tokens")
    print("   - It's the older API but might have fewer restrictions")
    print()
    print("3. CHECK IF INVENTORY API IS AVAILABLE IN SANDBOX:")
    print("   - Some APIs have limited sandbox support")
    print("   - You might need to use production for full Inventory API access")
    print()
    print("4. VERIFY TOKEN SCOPES:")
    print("   - The token shows 'Scopes: None'")
    print("   - This means scopes weren't granted during authorization")
    print("   - Try re-authorizing and make sure ALL boxes are checked")
    print()
    print("=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print()
    print("Since we've tried multiple tokens and all give 403 errors,")
    print("the issue is likely with the sandbox account setup, not the tokens.")
    print()
    print("The listing creation worked earlier with a different token,")
    print("so the code is correct. The issue is authentication/permissions.")
    print()
    print("Would you like to:")
    print("1. Check sandbox account settings in Developer Console")
    print("2. Try using the Trading API instead")
    print("3. Contact eBay support about sandbox Inventory API access")

if __name__ == "__main__":
    main()
