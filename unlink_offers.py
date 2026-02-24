"""
Unlink offers from a group by removing inventoryItemGroupKey.
Usage: python unlink_offers.py CARD_SET_GAGE_WOOD_BD_4_1 CARD_SET_ELI_WILLITS_BD_1_0
"""
import sys
from ebay_api_client import eBayAPIClient
import time

sys.stdout.reconfigure(encoding='utf-8')

def unlink_offers(skus):
    """Unlink offers from any group."""
    print("=" * 80)
    print("UNLINKING OFFERS FROM GROUPS")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    unlinked = 0
    for sku in skus:
        print(f"Processing {sku}...")
        offer_result = client.get_offer_by_sku(sku)
        
        if not offer_result.get('success'):
            print(f"   ⚠️ Could not get offer: {offer_result.get('error')}")
            continue
        
        offer = offer_result.get('offer', {})
        offer_id = offer.get('offerId')
        current_group = offer.get('inventoryItemGroupKey')
        
        if not offer_id:
            print(f"   ⚠️ No offer ID found")
            continue
        
        if current_group:
            print(f"   Found group: {current_group}")
            print(f"   Unlinking...")
            
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
            
            # DO NOT include inventoryItemGroupKey - this unlinks it
            update_result = client.update_offer(offer_id, offer_update)
            
            if update_result.get('success'):
                unlinked += 1
                print(f"   ✅ Unlinked from group")
            else:
                print(f"   ❌ Failed: {update_result.get('error')}")
        else:
            print(f"   ✅ Already unlinked (no group)")
            unlinked += 1
        
        print()
        time.sleep(1)  # Brief pause between updates
    
    print("=" * 80)
    print(f"SUMMARY: Unlinked {unlinked}/{len(skus)} offers")
    print("=" * 80)
    print()
    print("You can now try creating your listing again.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        skus = sys.argv[1:]
    else:
        # Default to the problematic SKUs from the error
        skus = ["CARD_SET_GAGE_WOOD_BD_4_1", "CARD_SET_ELI_WILLITS_BD_1_0"]
    
    unlink_offers(skus)
