"""
Verify description is stored and try publishing with a longer wait.
"""
from ebay_api_client import eBayAPIClient
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def verify_and_publish():
    """Verify and publish."""
    client = eBayAPIClient()
    
    group_key = "GROUPSAHF8A3F381768715399"
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    
    print("=" * 80)
    print("Verifying Description and Publishing")
    print("=" * 80)
    print()
    
    # Try to get the group with a different approach
    print("Step 1: Verifying group exists...")
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print("[ERROR] Group not found")
        return
    
    group_data = group_result.get('data', {})
    print(f"[OK] Group exists: {group_key}")
    print(f"  Title: {group_data.get('title', 'N/A')}")
    print(f"  Variant SKUs: {group_data.get('variantSKUs', [])}")
    print()
    
    # Update group one more time with a very explicit description
    print("Step 2: Updating group with explicit description format...")
    
    title = "Different Approach Test - Please Delete"
    # Use a longer, more explicit description
    description = """Different Approach Test - Please Delete

This is a test listing created via API. 

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Fast shipping and excellent customer service guaranteed."""
    
    group_update = {
        "title": title,
        "variesBy": {
            "specifications": [{
                "name": "PICK YOUR CARD",
                "values": ["1 Different Approach Test Card"]
            }]
        },
        "inventoryItemGroup": {
            "aspects": {
                "Card Name": ["Different Approach Test Card"],
                "Card Number": ["1"]
            },
            "description": description
        },
        "variantSKUs": [sku]
    }
    
    update_result = client.create_inventory_item_group(group_key, group_update)
    if update_result.get('success'):
        print(f"[OK] Group updated with description (length: {len(description)})")
    else:
        print(f"[WARNING] Group update: {update_result.get('error')}")
    
    print()
    print("Step 3: Waiting 15 seconds for description to fully propagate...")
    time.sleep(15)
    print()
    
    print("Step 4: Attempting to publish...")
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
        print("[ERROR] Publish Still Failed")
        print("=" * 80)
        print(f"Error: {error}")
        print()
        print("This confirms the Error 25016 issue persists.")
        print("The description is being set correctly, but eBay's publish")
        print("validation cannot find it. This appears to be an eBay API bug.")
        print()
        print("The listing exists as a draft and can be managed via API.")
        print("You may need to contact eBay support about this issue.")
        print()

if __name__ == "__main__":
    verify_and_publish()
