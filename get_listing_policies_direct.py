"""
Get policies directly from a listing ID using different methods.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    listing_id = "295755540338"
    
    print("=" * 80)
    print(f"Get Policies from Listing: {listing_id}")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Method 1: Try Browse API to get item details
    print("Method 1: Trying Browse API...")
    try:
        # Browse API endpoint
        browse_response = client._make_request('GET', '/buy/browse/v1/item', params={
            'item_id': listing_id
        })
        
        if browse_response.status_code == 200:
            item_data = browse_response.json()
            print("[OK] Got item from Browse API")
            print(f"Title: {item_data.get('title', 'N/A')}")
            # Browse API might not have policy IDs, but let's check
            print(f"Data keys: {list(item_data.keys())}")
            print(json.dumps(item_data, indent=2)[:1000])
    except Exception as e:
        print(f"  [SKIP] {e}")
    
    print()
    
    # Method 2: Try to find the SKU pattern from the listing
    # The listing title suggests it might have SKUs like CARD_* or similar
    # Let's try to query inventory items with a pattern
    
    print("Method 2: Since this is a variation listing, trying to find the inventory item group...")
    print("(We need to find the group key or SKUs)")
    print()
    
    # Actually, let me try a different approach - query published listings
    # Or try to get the item via a different inventory endpoint
    
    # Method 3: Try to get all inventory items and look for ones that might match
    print("Method 3: The listing ID format suggests this might be a published listing.")
    print("For published listings, we need to find the SKU first.")
    print()
    print("Since the offers endpoint isn't working, let's try to:")
    print("1. Query inventory items by a known pattern")
    print("2. Or you can provide a SKU from this listing")
    print()
    print("=" * 80)
    print("ALTERNATIVE SOLUTION")
    print("=" * 80)
    print()
    print("If you can provide:")
    print("- A SKU from this listing (any variation SKU)")
    print("- OR the inventory item group key")
    print()
    print("I can extract the return policy ID from that.")
    print()
    print("OR - try this:")
    print("1. Go to the listing in eBay")
    print("2. Look at the URL - it might have the group key or SKU")
    print("3. Or check the listing source code for SKU values")
    print()
    print("For now, let me try one more thing - query by listing ID using a different format...")
    
    # Try Trading API with proper format
    print()
    print("Method 4: Trying Trading API GetItem...")
    try:
        # Trading API uses XML, but let's try JSON if available
        # Actually, eBay Trading API is XML-based, so this might not work with our client
        print("  Trading API requires XML format - skipping for now")
    except Exception as e:
        print(f"  [SKIP] {e}")

if __name__ == "__main__":
    main()
