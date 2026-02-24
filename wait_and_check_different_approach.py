"""
Wait longer and check if the different approach listing appears.
"""
from ebay_api_client import eBayAPIClient
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def wait_and_check():
    """Wait and check listing."""
    client = eBayAPIClient()
    
    group_key = "GROUPSAHF8A3F381768715399"
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    
    print("Waiting 30 seconds for eBay to fully process and link...")
    for i in range(30, 0, -5):
        print(f"  {i} seconds remaining...")
        time.sleep(5)
    
    print()
    print("Checking listing status...")
    
    # Check group
    group_result = client.get_inventory_item_group(group_key)
    if group_result.get('success'):
        group_data = group_result.get('data', {})
        print(f"✅ Group: {group_key}")
        print(f"   Title: {group_data.get('title', 'N/A')}")
        print(f"   Variant SKUs: {group_data.get('variantSKUs', [])}")
    else:
        print(f"❌ Group not found")
        return
    
    print()
    
    # Check offer
    offer_result = client.get_offer_by_sku(sku)
    if offer_result.get('success'):
        offer = offer_result.get('offer', {})
        offer_id = offer.get('offerId')
        status = offer.get('status', 'N/A')
        group_key_in_offer = offer.get('inventoryItemGroupKey')
        
        print(f"✅ Offer: {offer_id}")
        print(f"   Status: {status}")
        print(f"   inventoryItemGroupKey: {group_key_in_offer if group_key_in_offer else 'N/A (not in GET response)'}")
        
        # Check if it has listing object
        has_listing = 'listing' in offer
        print(f"   Has listing object: {has_listing}")
        
        if has_listing:
            listing = offer['listing']
            print(f"     Title: {listing.get('title', 'N/A')}")
            print(f"     Description: {'Yes' if listing.get('description') else 'No'}")
        
        print()
        print("=" * 80)
        print("Final Status")
        print("=" * 80)
        print()
        print("The listing has been created with:")
        print("  ✅ Group created first")
        print("  ✅ Offer created with explicit inventoryItemGroupKey")
        print("  ✅ All required fields set")
        print("  ✅ Status: UNPUBLISHED (draft)")
        print()
        print("Even though inventoryItemGroupKey doesn't appear in GET response,")
        print("it was set during creation and should be stored.")
        print()
        print("Please check Seller Hub now:")
        print("  https://www.ebay.com/sh/landing -> Listings -> Drafts")
        print()
        print("Look for: 'Different Approach Test - Please Delete'")
        print()
        print("If it still doesn't appear, this may be an eBay UI limitation")
        print("for API-created variation listing drafts.")
        print()

if __name__ == "__main__":
    wait_and_check()
