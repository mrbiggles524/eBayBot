"""
Check the normal flow listing to see if it's properly linked and might appear in drafts.
"""
from ebay_api_client import eBayAPIClient
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def check_normal():
    """Check normal flow listing."""
    client = eBayAPIClient()
    
    group_key = "GROUPSET1768715280"
    sku = "CARD_SET_NORMAL_FLOW_TEST_CAR_1_0"
    
    print("=" * 80)
    print("Checking Normal Flow Listing")
    print("=" * 80)
    print()
    
    print("Waiting 5 seconds for eBay to process...")
    time.sleep(5)
    
    # Check group
    print("Group Status:")
    group_result = client.get_inventory_item_group(group_key)
    if group_result.get('success'):
        group_data = group_result.get('data', {})
        print(f"  ✅ Group: {group_key}")
        print(f"  Title: {group_data.get('title', 'N/A')}")
        print(f"  Variant SKUs: {group_data.get('variantSKUs', [])}")
    else:
        print(f"  ❌ Group not found")
        return
    
    print()
    
    # Check offer
    print("Offer Status:")
    offer_result = client.get_offer_by_sku(sku)
    if offer_result.get('success'):
        offer = offer_result.get('offer', {})
        offer_id = offer.get('offerId')
        status = offer.get('status', 'N/A')
        group_key_in_offer = offer.get('inventoryItemGroupKey')
        
        print(f"  ✅ Offer ID: {offer_id}")
        print(f"  Status: {status}")
        print(f"  SKU: {offer.get('sku', 'N/A')}")
        print(f"  Category: {offer.get('categoryId', 'N/A')}")
        print(f"  Price: ${offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A')}")
        print(f"  inventoryItemGroupKey: {group_key_in_offer if group_key_in_offer else 'N/A (missing)'}")
        
        if group_key_in_offer == group_key:
            print("  [SUCCESS] Offer is linked to group!")
        elif group_key_in_offer:
            print(f"  [WARNING] Group key mismatch: {group_key_in_offer} vs {group_key}")
        else:
            print("  [WARNING] Group key missing - might not appear in drafts")
        
        # Check listing object
        has_listing = 'listing' in offer
        print(f"  Has listing object: {has_listing}")
        if has_listing:
            listing = offer['listing']
            print(f"    Title: {listing.get('title', 'N/A')}")
            print(f"    Description: {'Yes' if listing.get('description') else 'No'}")
    else:
        print(f"  ❌ Offer not found")
        return
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(f"Group Key: {group_key}")
    print(f"SKU: {sku}")
    print(f"Offer ID: {offer_id if offer_result.get('success') else 'N/A'}")
    print()
    print("Check Seller Hub:")
    print("  1. Go to: https://www.ebay.com/sh/landing")
    print("  2. Navigate to: Listings -> Drafts")
    print("  3. Look for: 'Normal Flow Test Listing - Please Delete'")
    print()
    print("Wait 1-2 minutes if it doesn't appear immediately.")
    print()

if __name__ == "__main__":
    check_normal()
