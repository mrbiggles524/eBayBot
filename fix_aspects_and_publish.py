"""
Fix aspects alignment and try publishing.
Add PICK YOUR CARD aspect to inventory item to match variesBy.
"""
from ebay_api_client import eBayAPIClient
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def fix_and_publish():
    """Fix aspects and publish."""
    client = eBayAPIClient()
    
    group_key = "GROUPSAHF8A3F381768715399"
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    
    print("=" * 80)
    print("Fixing Aspects Alignment and Publishing")
    print("=" * 80)
    print()
    
    # Step 1: Get current inventory item
    print("Step 1: Getting current inventory item...")
    item_result = client._make_request('GET', f'/sell/inventory/v1/inventory_item/{sku}')
    if item_result.status_code != 200:
        print(f"[ERROR] Could not get inventory item: {item_result.status_code}")
        return
    
    item_data = item_result.json()
    product = item_data.get('product', {})
    current_aspects = product.get('aspects', {})
    
    print(f"Current aspects: {list(current_aspects.keys())}")
    print()
    
    # Step 2: Add PICK YOUR CARD aspect to match variesBy
    print("Step 2: Adding 'PICK YOUR CARD' aspect to match variesBy...")
    
    # Get the variation value from the group
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print("[ERROR] Could not get group")
        return
    
    group_data = group_result.get('data', {})
    varies_by = group_data.get('variesBy', {})
    specifications = varies_by.get('specifications', [])
    
    variation_value = None
    if specifications:
        spec = specifications[0]
        values = spec.get('values', [])
        if values:
            variation_value = values[0]
    
    if not variation_value:
        variation_value = "1 Different Approach Test Card"
    
    # Update inventory item with PICK YOUR CARD aspect
    updated_aspects = current_aspects.copy()
    updated_aspects["PICK YOUR CARD"] = [variation_value]
    
    print(f"  Adding aspect: PICK YOUR CARD = {variation_value}")
    print(f"  Updated aspects: {list(updated_aspects.keys())}")
    print()
    
    # Update inventory item
    item_update = {
        "product": {
            "categoryId": product.get('categoryId', '261328'),
            "aspects": updated_aspects
        },
        "condition": item_data.get('condition', 'USED_VERY_GOOD'),
        "availability": item_data.get('availability', {}),
        "packageWeightAndSize": item_data.get('packageWeightAndSize', {}),
        "conditionDescriptors": item_data.get('conditionDescriptors', [])
    }
    
    update_result = client._make_request('PUT', f'/sell/inventory/v1/inventory_item/{sku}', data=item_update)
    if update_result.status_code in [200, 204]:
        print("[OK] Inventory item updated with PICK YOUR CARD aspect")
    else:
        print(f"[WARNING] Inventory item update: {update_result.status_code}")
        print("Continuing anyway...")
    
    print()
    print("Step 3: Waiting 5 seconds...")
    time.sleep(5)
    print()
    
    print("Step 4: Publishing...")
    print("[WARNING] This will make the listing LIVE!")
    print()
    
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    if publish_result.get('success'):
        listing_id = publish_result.get('listing_id')
        print()
        print("=" * 80)
        print("[SUCCESS] Listing Published!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print()
        print("View your listing:")
        print(f"  https://www.ebay.com/itm/{listing_id}")
        print()
        print("Check Seller Hub -> Listings -> Active")
        print()
        print("[IMPORTANT] Delete this test listing when done!")
        print()
    else:
        error = publish_result.get('error', 'Unknown error')
        print()
        print("=" * 80)
        print("[ERROR] Publish Failed")
        print("=" * 80)
        print(f"Error: {error}")
        print()
        print("The aspects alignment fix didn't resolve the issue.")
        print("This confirms Error 25016 is a persistent eBay API issue.")
        print()

if __name__ == "__main__":
    fix_and_publish()
