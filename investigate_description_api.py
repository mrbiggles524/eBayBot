"""
Investigate the API to understand why description validation fails.
Check how eBay stores and retrieves descriptions for variation listings.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def investigate():
    """Investigate description API behavior."""
    print("=" * 80)
    print("Investigating Description API Behavior")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Test group key from previous attempts
    test_group_key = "GROUPTESTSET1768712745"
    
    print("Step 1: Get group and check what eBay returns...")
    print(f"Group Key: {test_group_key}")
    print()
    
    group_result = client.get_inventory_item_group(test_group_key)
    
    if group_result.get('success'):
        group_data = group_result.get('data', {})
        print("[OK] Group retrieved")
        print()
        print("Group structure:")
        print(f"  Keys: {list(group_data.keys())}")
        print()
        
        # Check for inventoryItemGroup
        if 'inventoryItemGroup' in group_data:
            inv_group = group_data['inventoryItemGroup']
            print("  inventoryItemGroup found!")
            print(f"    Keys: {list(inv_group.keys())}")
            
            if 'description' in inv_group:
                desc = inv_group['description']
                print(f"    [OK] Description found: {len(desc)} chars")
                print(f"    Preview: {desc[:100]}...")
            else:
                print("    [WARNING] Description NOT in inventoryItemGroup")
        else:
            print("  [WARNING] inventoryItemGroup NOT in response!")
            print("  This is the problem - eBay GET doesn't return it")
        
        print()
        print("Full group data (JSON):")
        print(json.dumps(group_data, indent=2))
    else:
        print(f"[ERROR] Could not get group: {group_result.get('error')}")
    
    print()
    print("=" * 80)
    print("Step 2: Check offer description...")
    print("=" * 80)
    print()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    offer_result = client.get_offer_by_sku(sku)
    
    if offer_result.get('success'):
        offer = offer_result.get('offer', {})
        print("[OK] Offer retrieved")
        print()
        print("Offer structure:")
        print(f"  Keys: {list(offer.keys())}")
        print()
        
        if 'listing' in offer:
            listing = offer['listing']
            print("  listing found!")
            print(f"    Keys: {list(listing.keys())}")
            
            if 'description' in listing:
                desc = listing['description']
                print(f"    [OK] Description found: {len(desc)} chars")
                print(f"    Preview: {desc[:100]}...")
            else:
                print("    [WARNING] Description NOT in listing")
        else:
            print("  [WARNING] listing NOT in offer!")
        
        print()
        print("Full offer data (JSON):")
        print(json.dumps(offer, indent=2))
    else:
        print(f"[ERROR] Could not get offer: {offer_result.get('error')}")
    
    print()
    print("=" * 80)
    print("Analysis")
    print("=" * 80)
    print()
    print("For variation listings:")
    print("  1. Description should be in inventoryItemGroup.description")
    print("  2. eBay GET may not return inventoryItemGroup (known issue)")
    print("  3. But PUT with description should store it")
    print("  4. During publish, eBay validates description exists")
    print()
    print("Possible issues:")
    print("  - Description format/encoding")
    print("  - Description location (group vs offer)")
    print("  - API propagation delay")
    print("  - Production API bug with description persistence")
    print()

if __name__ == "__main__":
    investigate()
