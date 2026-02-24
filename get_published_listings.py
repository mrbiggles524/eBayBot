"""
Get published listings (active listings) from sandbox.
This helps you find listing IDs to view your listings.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Get Published Listings from Sandbox")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try to get inventory item groups (variation listings)
    print("Checking inventory item groups (variation listings)...")
    print()
    
    try:
        # Get inventory item groups
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item_group', params={'limit': 50})
        
        if response.status_code == 200:
            data = response.json()
            groups = data.get('inventoryItemGroups', [])
            
            if groups:
                print(f"[OK] Found {len(groups)} inventory item group(s):")
                print()
                for i, group in enumerate(groups, 1):
                    group_key = group.get('inventoryItemGroupKey', 'N/A')
                    title = group.get('title', 'N/A')
                    variant_skus = group.get('variantSKUs', [])
                    
                    print(f"{i}. Group Key: {group_key}")
                    print(f"   Title: {title}")
                    print(f"   Variants: {len(variant_skus)} SKU(s)")
                    print()
            else:
                print("[INFO] No inventory item groups found")
        else:
            print(f"[WARNING] Status {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Could not get inventory item groups: {e}")
    
    print()
    print("=" * 80)
    print("Important: Sandbox Seller Hub Limitation")
    print("=" * 80)
    print()
    print("The sandbox seller hub UI (sandbox.ebay.com/selling) doesn't work well")
    print("and often redirects to production. This is a known eBay limitation.")
    print()
    print("To view your listings:")
    print()
    print("1. If you have a LISTING_ID from when you created the listing:")
    print("   https://sandbox.ebay.com/itm/{LISTING_ID}")
    print()
    print("2. Check the Streamlit UI output - it should show the listing_id")
    print("   when a listing is successfully published")
    print()
    print("3. The listing might be created as a DRAFT")
    print("   - Drafts don't have listing IDs yet")
    print("   - They need to be published first")
    print("   - Check if 'publish_immediately' was checked when creating")
    print()
    print("4. To publish a draft listing, you can:")
    print("   - Use the API to publish it")
    print("   - Or create a new listing with 'publish_immediately' checked")
    print()

if __name__ == "__main__":
    main()
