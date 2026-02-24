"""
Clean up a specific group by unlinking offers and deleting it.
Usage: python cleanup_group.py GROUPSET1768801675
"""
import sys
from ebay_api_client import eBayAPIClient
import time

sys.stdout.reconfigure(encoding='utf-8')

def cleanup_group(group_key: str):
    """Clean up a group by unlinking offers and deleting it."""
    print("=" * 80)
    print(f"CLEANING UP GROUP: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Step 1: Get group info
    print("Step 1: Getting group information...")
    group_result = client.get_inventory_item_group(group_key)
    
    if not group_result.get('success'):
        print(f"❌ Group not found: {group_result.get('error')}")
        print("   Group may already be deleted.")
        return
    
    group_data = group_result.get('data', {})
    title = group_data.get('title', 'N/A')
    variant_skus = group_data.get('variantSKUs', [])
    
    print(f"✅ Group found")
    print(f"   Title: {title}")
    print(f"   SKUs: {variant_skus}")
    print()
    
    # Step 2: Unlink offers
    print("Step 2: Unlinking offers from group...")
    offers_unlinked = 0
    for sku in variant_skus:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success') and offer_result.get('offer'):
            offer = offer_result['offer']
            offer_id = offer.get('offerId')
            current_group = offer.get('inventoryItemGroupKey')
            
            if current_group == group_key:
                print(f"   Unlinking {sku}...")
                # Update offer to remove inventoryItemGroupKey
                offer_update = {
                    "sku": sku,
                    "marketplaceId": "EBAY_US",
                    "format": "FIXED_PRICE",
                    "categoryId": offer.get('categoryId', '261328'),
                    "pricingSummary": offer.get('pricingSummary', {}),
                    "listingPolicies": offer.get('listingPolicies', {}),
                    "availableQuantity": offer.get('availableQuantity', 1),
                    "listingDuration": offer.get('listingDuration', 'GTC')
                }
                
                if 'listing' in offer:
                    offer_update['listing'] = offer['listing']
                
                update_result = client.update_offer(offer_id, offer_update)
                if update_result.get('success'):
                    offers_unlinked += 1
                    print(f"   ✅ Unlinked {sku}")
                else:
                    print(f"   ❌ Failed to unlink {sku}: {update_result.get('error')}")
            else:
                print(f"   ⚠️ {sku} not linked to this group (linked to: {current_group})")
        else:
            print(f"   ⚠️ Could not get offer for {sku}")
    
    print(f"   Unlinked {offers_unlinked}/{len(variant_skus)} offers")
    print()
    
    # Step 3: Wait for propagation
    if offers_unlinked > 0:
        print("Step 3: Waiting 5 seconds for unlinking to propagate...")
        time.sleep(5)
        print()
    
    # Step 4: Delete group
    print("Step 4: Deleting group...")
    delete_result = client.delete_inventory_item_group(group_key)
    
    if delete_result.get('success'):
        print(f"✅ Group deleted successfully!")
        print()
        print("You can now try creating your listing again.")
    else:
        error = delete_result.get('error', 'Unknown error')
        print(f"❌ Failed to delete group: {error}")
        print()
        print("The group may be published or scheduled. You need to:")
        print("1. Go to Scheduled Listings: https://www.ebay.com/sh/lst/scheduled")
        print("2. Or Active Listings: https://www.ebay.com/sh/lst/active")
        print(f"3. Find and end/delete the listing (group: {group_key})")
        print("4. Wait 1-2 minutes for eBay to process")
        print("5. Then run this script again or try creating your listing")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        group_key = sys.argv[1]
    else:
        group_key = "GROUPSET1768801675"  # Default to the problematic group
    
    cleanup_group(group_key)
