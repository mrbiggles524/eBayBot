"""
Direct method to get OAuth token from eBay Developer Console.
This bypasses the redirect URI requirement by using eBay's direct sign-in.
"""
from config import Config

def main():
    print("=" * 80)
    print("Get eBay OAuth Token - Direct Method")
    print("=" * 80)
    print()
    print("This method uses eBay's Developer Console directly - no redirect URI needed!")
    print()
    print("Steps:")
    print("1. Open: https://developer.ebay.com/my/keys")
    print("2. Make sure you're in SANDBOX mode")
    print("3. Click 'User Tokens' for your Sandbox app")
    print("4. Click 'Sign in to Sandbox for OAuth' button")
    print("5. Sign in with: TESTUSER_manbot")
    print("6. After authorization, you'll see a token on the page")
    print("7. Copy the ENTIRE token (it's long, starts with something like 'v^1.1#...')")
    print()
    print("=" * 80)
    print("Paste your token here (or press Enter to skip):")
    print("=" * 80)
    
    token = input("\nToken: ").strip()
    
    if not token:
        print("\nNo token provided. You can add it manually to .env later.")
        print("Set: EBAY_SANDBOX_TOKEN=your_token_here")
        return
    
    # Update .env
    try:
        with open(".env", "r") as f:
            content = f.read()
        
        # Update or add EBAY_SANDBOX_TOKEN
        if "EBAY_SANDBOX_TOKEN=" in content:
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if line.startswith("EBAY_SANDBOX_TOKEN="):
                    new_lines.append(f"EBAY_SANDBOX_TOKEN={token}")
                else:
                    new_lines.append(line)
            content = "\n".join(new_lines)
        else:
            content += f"\nEBAY_SANDBOX_TOKEN={token}\n"
        
        with open(".env", "w") as f:
            f.write(content)
        
        print("\n✅ Token saved to .env file!")
        print("\nNext steps:")
        print("1. Set USE_OAUTH=false in .env (if not already set)")
        print("2. Test with: python check_listings.py")
        
    except Exception as e:
        print(f"\n❌ Error saving token: {e}")
        print(f"\nPlease manually add to .env:")
        print(f"EBAY_SANDBOX_TOKEN={token}")

if __name__ == "__main__":
    main()
