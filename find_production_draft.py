"""
Find the draft listing we just created in production.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def find_draft():
    """Find the draft listing."""
    print("=" * 80)
    print("Finding Production Draft Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Search for inventory items
    print("Searching for inventory items...")
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 50})
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('inventoryItems', [])
            
            print(f"[OK] Found {len(items)} inventory item(s)")
            print()
            
            # Look for test items
            test_items = [item for item in items if 'TEST' in item.get('sku', '').upper()]
            
            if test_items:
                print("Test items found:")
                print()
                for item in test_items:
                    sku = item.get('sku', 'N/A')
                    print(f"  SKU: {sku}")
                    
                    # Try to get offer for this SKU
                    try:
                        offer_response = client._make_request('GET', f'/sell/inventory/v1/offer?sku={sku}')
                        if offer_response.status_code == 200:
                            offer_data = offer_response.json()
                            offers = offer_data.get('offers', [])
                            if offers:
                                offer = offers[0]
                                offer_id = offer.get('offerId', 'N/A')
                                listing_status = offer.get('listing', {}).get('listingStatus', 'N/A')
                                title = offer.get('listing', {}).get('title', 'N/A')
                                
                                print(f"    Offer ID: {offer_id}")
                                print(f"    Title: {title}")
                                print(f"    Status: {listingStatus}")
                                print()
                    except Exception as e:
                        print(f"    [ERROR] Could not get offer: {e}")
                        print()
            else:
                print("[INFO] No test items found in inventory")
                print()
            
            # Show all items
            if items:
                print("All inventory items:")
                print()
                for item in items[:10]:  # Show first 10
                    sku = item.get('sku', 'N/A')
                    print(f"  - {sku}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
                print()
        else:
            print(f"[ERROR] Failed to get inventory items: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        print()
    
    # Search for inventory item groups
    print("Searching for inventory item groups...")
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item_group', params={'limit': 50})
        
        if response.status_code == 200:
            data = response.json()
            groups = data.get('inventoryItemGroups', [])
            
            print(f"[OK] Found {len(groups)} inventory item group(s)")
            print()
            
            # Look for test groups
            test_groups = [g for g in groups if 'TEST' in g.get('inventoryItemGroupKey', '').upper()]
            
            if test_groups:
                print("Test groups found:")
                print()
                for group in test_groups:
                    group_key = group.get('inventoryItemGroupKey', 'N/A')
                    title = group.get('title', 'N/A')
                    variant_skus = group.get('variantSKUs', [])
                    
                    print(f"  Group Key: {group_key}")
                    print(f"  Title: {title}")
                    print(f"  Variant SKUs: {', '.join(variant_skus)}")
                    print()
            else:
                print("[INFO] No test groups found")
                print()
            
            # Show all groups
            if groups:
                print("All inventory item groups:")
                print()
                for group in groups[:10]:  # Show first 10
                    group_key = group.get('inventoryItemGroupKey', 'N/A')
                    title = group.get('title', 'N/A')
                    print(f"  - {group_key}: {title}")
                if len(groups) > 10:
                    print(f"  ... and {len(groups) - 10} more")
                print()
        else:
            print(f"[ERROR] Failed to get groups: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        print()
    
    print("=" * 80)
    print("Tips")
    print("=" * 80)
    print()
    print("If you don't see the draft in Seller Hub:")
    print("  1. Try refreshing the page")
    print("  2. Check if there's a search filter applied")
    print("  3. Look for 'Test Listing - Please Delete' in the title")
    print("  4. The draft might take a few minutes to appear")
    print()
    print("You can also search by SKU in Seller Hub:")
    print("  - Look for SKU: CARD_TEST_SET_TEST_CARD_1_0")
    print()

if __name__ == "__main__":
    find_draft()
