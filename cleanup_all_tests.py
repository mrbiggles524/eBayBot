"""
Clean up ALL test listings from eBay.
"""
from ebay_api_client import eBayAPIClient
import sys

sys.stdout.reconfigure(encoding='utf-8')

def cleanup():
    client = eBayAPIClient()
    
    print("=" * 80)
    print("Cleaning Up All Test Listings")
    print("=" * 80)
    print()
    
    # All known test groups and SKUs
    test_items = [
        # Old test listings
        ("GROUPSAHF8A3F381768715399", "CARD_DIFF_APPROACH_TEST_1_0"),
        ("GROUPSET1768715280", "CARD_SET_NORMAL_FLOW_TEST_CAR_1_0"),
        ("GROUPSET1768714571", "CARD_SET_FINAL_TEST_CARD_1_0"),
        # New working test listings
        ("GROUP_2374DF41", "TEST_CARD_2374DF41"),
        ("VARGROUP_8A2C1450", "VAR_8A2C1450_1"),
        # Single item tests (no group)
        (None, "SINGLE_TEST_63502346"),
        (None, "CARD_TEST_26ABABC0"),
        (None, "CARD_COMPLETE_1CE9D83D"),
    ]
    
    deleted_groups = []
    deleted_offers = []
    deleted_items = []
    
    # First, delete groups (which should handle their offers)
    print("Step 1: Deleting inventory item groups...")
    for group_key, sku in test_items:
        if group_key:
            print(f"  Deleting group: {group_key}")
            
            # Get group to find all SKUs
            group_result = client.get_inventory_item_group(group_key)
            if group_result.get('success'):
                variant_skus = group_result.get('data', {}).get('variantSKUs', [])
                
                # Delete offers first
                for variant_sku in variant_skus:
                    offer_result = client.get_offer_by_sku(variant_sku)
                    if offer_result.get('success'):
                        offer = offer_result['offer']
                        offer_id = offer.get('offerId')
                        if offer_id:
                            resp = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
                            if resp.status_code in [200, 204]:
                                deleted_offers.append(offer_id)
                                print(f"    [OK] Deleted offer: {offer_id}")
                
                # Delete group
                result = client.delete_inventory_item_group(group_key)
                if result.get('success'):
                    deleted_groups.append(group_key)
                    print(f"    [OK] Deleted group: {group_key}")
                else:
                    print(f"    [SKIP] Group not found or already deleted")
            else:
                print(f"    [SKIP] Group not found: {group_key}")
    
    print()
    print("Step 2: Deleting standalone offers and inventory items...")
    
    # Delete any remaining offers and items
    all_skus = set()
    for group_key, sku in test_items:
        all_skus.add(sku)
    
    # Add variation SKUs
    all_skus.add("VAR_8A2C1450_1")
    all_skus.add("VAR_8A2C1450_2")
    all_skus.add("VAR_8A2C1450_3")
    
    for sku in all_skus:
        # Try to delete offer
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result['offer']
            offer_id = offer.get('offerId')
            if offer_id and offer_id not in deleted_offers:
                resp = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
                if resp.status_code in [200, 204]:
                    deleted_offers.append(offer_id)
                    print(f"  [OK] Deleted offer for {sku}: {offer_id}")
        
        # Try to delete inventory item
        resp = client._make_request('DELETE', f'/sell/inventory/v1/inventory_item/{sku}')
        if resp.status_code in [200, 204]:
            deleted_items.append(sku)
            print(f"  [OK] Deleted inventory item: {sku}")
        else:
            print(f"  [SKIP] Item not found: {sku}")
    
    print()
    print("=" * 80)
    print("Cleanup Summary")
    print("=" * 80)
    print(f"  Groups deleted: {len(deleted_groups)}")
    print(f"  Offers deleted: {len(deleted_offers)}")
    print(f"  Items deleted: {len(deleted_items)}")
    print()
    print("[NOTE] The published listings (297945076691, 297945079830) need to be")
    print("       deleted manually from eBay Seller Hub -> Listings -> Active")
    print()
    print("Go to: https://www.ebay.com/sh/lst/active")
    print("Find the test listings and click 'End listing'")
    print()

if __name__ == "__main__":
    cleanup()
