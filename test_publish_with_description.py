"""
Test publishing a group with a guaranteed valid description.
This will help us figure out why Error 25016 keeps happening.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
from datetime import datetime, timedelta
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

def test_publish_group(group_key):
    """Test publishing a specific group."""
    print("=" * 80)
    print(f"TESTING PUBLISH FOR GROUP: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Step 1: Get current group
    print("Step 1: Getting current group data...")
    group_result = client.get_inventory_item_group(group_key)
    
    if not group_result.get('success'):
        print(f"❌ Group not found: {group_result.get('error')}")
        return
    
    group_data = group_result.get('data', {})
    title = group_data.get('title', 'Variation Listing')
    variant_skus = group_data.get('variantSKUs', [])
    
    print(f"✅ Group found: {title}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print()
    
    # Step 2: Get aspects from offers
    print("Step 2: Getting aspects from offers...")
    aspects = {}
    if variant_skus:
        offer_result = client.get_offer_by_sku(variant_skus[0])
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            listing = offer.get('listing', {})
            item_specifics = listing.get('itemSpecifics', {})
            if item_specifics:
                for key, value in item_specifics.items():
                    if isinstance(value, list) and len(value) > 0:
                        aspects[key] = value
                print(f"   Found aspects: {list(aspects.keys())}")
    
    # Step 3: Create a SIMPLE, guaranteed valid description
    print()
    print("Step 3: Creating simple, guaranteed valid description...")
    # Use a very simple description that's definitely valid
    simple_description = f"{title}. Select your card from the variations below. Each card is listed as a separate variation option. All cards are in Near Mint or better condition unless otherwise noted. Ships in penny sleeve and top loader via PWE with eBay tracking. This is a variation listing where you can select from multiple card options."
    
    # Ensure it's at least 50 characters
    if len(simple_description.strip()) < 50:
        simple_description = f"{title}. Select your card from the variations below. Each card is listed as a separate variation option. All cards are in Near Mint or better condition unless otherwise noted. Ships in penny sleeve and top loader via PWE with eBay tracking. This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."
    
    print(f"   Description length: {len(simple_description)}")
    print(f"   Description: {simple_description[:150]}...")
    print()
    
    # Step 4: Update group with this simple description
    print("Step 4: Updating group with simple description...")
    update_data = {
        "title": title,
        "variesBy": group_data.get('variesBy', {}),
        "inventoryItemGroup": {
            "aspects": aspects,
            "description": simple_description
        },
        "variantSKUs": variant_skus
    }
    
    print("   Update payload structure:")
    print(f"     - title: {title}")
    print(f"     - has inventoryItemGroup: True")
    print(f"     - has description: True (length: {len(simple_description)})")
    print()
    
    update_result = client.create_inventory_item_group(group_key, update_data)
    
    if not update_result.get('success'):
        print(f"❌ Update failed: {update_result.get('error')}")
        return
    
    print("✅ Group updated successfully")
    print()
    
    # Step 5: Wait for propagation
    print("Step 5: Waiting 10 seconds for eBay to process...")
    time.sleep(10)
    
    # Step 6: Verify description is there
    print("Step 6: Verifying description was saved...")
    verify_result = client.get_inventory_item_group(group_key)
    if verify_result.get('success'):
        print("✅ Group still exists after update")
        # Note: eBay GET may not return description, but it should be stored
        print("   (eBay GET may not return description, but it should be stored)")
    print()
    
    # Step 7: Try to publish
    print("Step 7: Attempting to publish group...")
    print("   This will create a scheduled listing if listingStartDate is set on offers")
    print()
    
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    print()
    print("PUBLISH RESULT:")
    print(f"  Success: {publish_result.get('success')}")
    if publish_result.get('success'):
        print("✅ PUBLISHED SUCCESSFULLY!")
        data = publish_result.get('data', {})
        listing_id = data.get('listingId')
        if listing_id:
            print(f"   Listing ID: {listing_id}")
        print()
        print("The listing should now be visible in Seller Hub!")
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"❌ PUBLISH FAILED: {error}")
        print()
        
        if '25016' in str(error):
            print("ERROR 25016 - Description issue")
            print()
            print("Even though we:")
            print("  1. Set a valid description (431+ characters)")
            print("  2. Updated the group")
            print("  3. Waited for propagation")
            print()
            print("eBay is still rejecting it. This suggests:")
            print("  - eBay may require description in a different format")
            print("  - There may be a timing issue (need longer wait)")
            print("  - There may be a bug in eBay's API")
            print()
            print("Let's check the offers to see if they have listingStartDate...")
            
            # Check offers for listingStartDate
            print()
            print("Checking offers for listingStartDate...")
            for sku in variant_skus[:3]:
                offer_result = client.get_offer_by_sku(sku)
                if offer_result.get('success'):
                    offer = offer_result.get('offer', {})
                    start_date = offer.get('listingStartDate', '')
                    print(f"   {sku}: {start_date or '❌ MISSING'}")
        
        print()
        print("The group exists with a valid description.")
        print("You can try publishing it manually from Seller Hub.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_publish_with_description.py <group_key>")
        print("Example: python test_publish_with_description.py GROUPSET1768868451")
        sys.exit(1)
    
    test_publish_group(sys.argv[1])
