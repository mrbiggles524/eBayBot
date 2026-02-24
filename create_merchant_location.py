"""
Create a merchant location in production.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def create_location():
    """Create a merchant location."""
    print("=" * 80)
    print("Create Merchant Location")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try to create a location
    print("Creating merchant location 'DEFAULT'...")
    print()
    print("Note: You may need to use your actual address from eBay Seller Hub.")
    print("For now, using a placeholder address that you can update later.")
    print()
    
    result = client.create_merchant_location(
        merchant_location_key="DEFAULT",
        name="Default Location",
        address={
            "addressLine1": "123 Main St",
            "city": "New York",
            "stateOrProvince": "NY",
            "postalCode": "10001",
            "country": "US"
        }
    )
    
    if result.get('success'):
        print("[SUCCESS] Merchant location created!")
        print()
        print("Location Key: DEFAULT")
        print()
        print("Your .env file should already have:")
        print("MERCHANT_LOCATION_KEY=DEFAULT")
        print()
        print("If not, add it to your .env file.")
        return True
    else:
        error = result.get('error', 'Unknown error')
        print(f"[ERROR] Failed to create location: {error}")
        print()
        print("Options:")
        print("1. Get your location key from eBay Seller Hub:")
        print("   - Go to: https://www.ebay.com/sh/landing")
        print("   - Navigate to: Account → Shipping Preferences")
        print("   - Find your location key")
        print("   - Add to .env: MERCHANT_LOCATION_KEY=your_key_here")
        print()
        print("2. Or try removing merchantLocationKey from listings")
        print("   (it may be optional in some cases)")
        return False

if __name__ == "__main__":
    create_location()
