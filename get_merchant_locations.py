"""
Get merchant locations from eBay account.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def get_locations():
    """Get merchant locations."""
    print("=" * 80)
    print("Getting Merchant Locations")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get merchant locations
    print("Fetching merchant locations...")
    result = client.get_merchant_locations()
    
    if result.get('locations') is not None:
        locations = result.get('locations', [])
        
        if not locations:
            print()
            print("[WARNING] No merchant locations found!")
            print()
            print("You need to create a merchant location in eBay Seller Hub:")
            print("1. Go to: https://www.ebay.com/sh/landing")
            print("2. Navigate to: Account → Shipping Preferences")
            print("3. Create a shipping location")
            print("4. Copy the location key and add it to your .env file:")
            print("   MERCHANT_LOCATION_KEY=your_location_key_here")
            print()
            return None
        
        print()
        print(f"[OK] Found {len(locations)} merchant location(s):")
        print()
        
        for i, location in enumerate(locations, 1):
            location_key = location.get('merchantLocationKey', 'N/A')
            name = location.get('name', 'N/A')
            address = location.get('location', {}).get('address', {})
            address_str = f"{address.get('addressLine1', '')}, {address.get('city', '')}, {address.get('stateOrProvince', '')} {address.get('postalCode', '')}"
            
            print(f"Location {i}:")
            print(f"  Key: {location_key}")
            print(f"  Name: {name}")
            print(f"  Address: {address_str}")
            print()
        
        # Suggest first location
        primary_location = locations[0]
        primary_key = primary_location.get('merchantLocationKey')
        
        if primary_key:
            print("=" * 80)
            print("Recommended: Use First Location")
            print("=" * 80)
            print()
            print(f"To use the first location, add this to your .env file:")
            print()
            print(f"MERCHANT_LOCATION_KEY={primary_key}")
            print()
            print("Or update it with:")
            print(f'python -c "import os; from pathlib import Path; env = Path(\'.env\'); content = env.read_text() if env.exists() else \'\'; lines = [l for l in content.splitlines() if not l.strip().startswith(\'MERCHANT_LOCATION_KEY=\')]; lines.append(f\'MERCHANT_LOCATION_KEY={primary_key}\'); env.write_text(\'\\n\'.join(lines))"')
            print()
        
        return locations
    else:
        error = result.get('error', 'Unknown error')
        if error:
            print(f"[ERROR] Failed to get merchant locations: {error}")
        else:
            print("[ERROR] Failed to get merchant locations: Unknown error")
        print()
        print("This might mean:")
        print("  1. Your token doesn't have the right permissions")
        print("  2. Merchant locations API is not available")
        print("  3. You need to create a location in eBay Seller Hub first")
        print()
        return None

if __name__ == "__main__":
    get_locations()
