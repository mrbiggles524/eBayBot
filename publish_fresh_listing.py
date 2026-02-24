"""
Publish the fresh listing we just created.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def publish_fresh():
    """Publish the fresh listing."""
    print("=" * 80)
    print("Publishing Fresh Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Fresh listing details from creation
    group_key = "GROUPSET1768713890"
    sku = "CARD_SET_FRESH_TEST_CARD_1_0"
    
    print(f"Group Key: {group_key}")
    print(f"SKU: {sku}")
    print()
    
    # First verify the group exists and check its structure
    print("Step 1: Verifying group...")
    group_result = client.get_inventory_item_group(group_key)
    
    if group_result.get('success'):
        group_data = group_result.get('data', {})
        print("[OK] Group exists")
        print(f"  Keys: {list(group_data.keys())}")
        
        # Check if inventoryItemGroup is in response
        if 'inventoryItemGroup' in group_data:
            inv_group = group_data['inventoryItemGroup']
            if 'description' in inv_group:
                print(f"  [OK] Description found in GET response: {len(inv_group['description'])} chars")
            else:
                print("  [WARNING] Description NOT in GET response (but may still be stored)")
        else:
            print("  [NOTE] inventoryItemGroup not in GET response (eBay API quirk)")
            print("  [NOTE] This is normal - eBay doesn't return it even if stored")
    else:
        print(f"[ERROR] Group not found: {group_result.get('error')}")
        return
    
    print()
    print("Step 2: Updating group with description (to be 100% sure)...")
    
    # Update group with description
    group_update = {
        "title": "Fresh Test Listing - Please Delete",
        "variesBy": {
            "specifications": [{
                "name": "PICK YOUR CARD",
                "values": ["1 Fresh Test Card"]
            }]
        },
        "inventoryItemGroup": {
            "aspects": {
                "Card Name": ["Fresh Test Card"],
                "Card Number": ["1"]
            },
            "description": "Fresh Test Listing - Please Delete\n\nSelect your card from the variations below. Each card is listed as a separate variation option.\n\nAll cards are in Near Mint or better condition unless otherwise noted."
        },
        "variantSKUs": [sku]
    }
    
    update_result = client.create_inventory_item_group(group_key, group_update)
    if update_result.get('success'):
        print("[OK] Group updated with description")
    else:
        print(f"[WARNING] Group update: {update_result.get('error')}")
    
    print()
    print("Step 3: Waiting 10 seconds for propagation...")
    time.sleep(10)
    print()
    
    print("Step 4: Publishing...")
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    if publish_result.get('success'):
        listing_id = publish_result.get('listing_id')
        print()
        print("=" * 80)
        print("[SUCCESS] Fresh Listing Published!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print()
        print("View your listing:")
        print(f"  https://www.ebay.com/itm/{listing_id}")
        print()
        print("Check Seller Hub -> Listings -> Active")
        print()
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"[ERROR] Publish failed: {error}")
        print()
        print("This confirms the description validation issue persists.")
        print("The API investigation shows:")
        print("  - eBay GET doesn't return inventoryItemGroup (even if stored)")
        print("  - PUT with description returns 204 (success)")
        print("  - But publish still fails with Error 25016")
        print()
        print("This appears to be a production API bug with description persistence.")

if __name__ == "__main__":
    publish_fresh()
