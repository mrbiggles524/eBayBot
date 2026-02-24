"""
Fix a group's description and try to publish it.
This will help us understand why Error 25016 keeps happening.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import time

sys.stdout.reconfigure(encoding='utf-8')

def fix_and_publish_group(group_key: str):
    """Fix group description and try to publish."""
    print("=" * 80)
    print(f"FIXING AND PUBLISHING GROUP: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    config = Config()
    
    # Step 1: Get group
    print("Step 1: Getting group data...")
    result = client.get_inventory_item_group(group_key)
    
    if not result.get('success'):
        print(f"❌ Failed to get group: {result.get('error')}")
        return
    
    group_data = result.get('data', {})
    title = group_data.get('title', '')
    
    # If title is empty, use a default
    if not title or not title.strip():
        title = "Variation Listing"
        print(f"   ⚠️ Title was empty, using default: {title}")
    
    variant_skus = group_data.get('variantSKUs', [])
    varies_by = group_data.get('variesBy', {})
    
    print(f"✅ Group retrieved")
    print(f"   Title: {title}")
    print(f"   Title length: {len(title)}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print()
    
    # Step 2: Build description
    print("Step 2: Building description...")
    description = f"""{title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve + top loader via PWE with eBay tracking."""
    
    print(f"   Description length: {len(description)}")
    print()
    
    # Step 3: Get aspects from group (if available) OR build them from offers
    print("Step 3: Getting aspects...")
    aspects = {}
    if 'inventoryItemGroup' in group_data:
        aspects = group_data['inventoryItemGroup'].get('aspects', {})
        print(f"   Found aspects in group: {list(aspects.keys())}")
    
    # If no aspects, try to build them from offers
    if not aspects and variant_skus:
        print("   No aspects in group - building from offers...")
        card_names = []
        card_numbers = []
        
        for sku in variant_skus:
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result.get('offer', {})
                listing = offer.get('listing', {})
                title = listing.get('title', '')
                
                # Try to extract card name from title (format: "Name #Number - Set")
                # Or from SKU pattern
                if title:
                    # Title might be "Eli Willits #BD-1 - Base Cards..."
                    parts = title.split('#')
                    if len(parts) > 1:
                        name_part = parts[0].strip()
                        number_part = parts[1].split('-')[0].strip() if '-' in parts[1] else parts[1].split()[0].strip()
                        if name_part:
                            card_names.append(name_part)
                        if number_part:
                            card_numbers.append(number_part)
        
        # Build aspects
        if card_names:
            aspects["Card Name"] = list(set(card_names))
        if card_numbers:
            aspects["Card Number"] = list(set(card_numbers))
        
        print(f"   Built aspects: {list(aspects.keys())}")
        if not aspects:
            print("   ⚠️ Could not build aspects - will use empty dict")
    print()
    
    # Step 4: Update group with description
    print("Step 4: Updating group with description...")
    
    # Ensure title is valid
    if not title or not title.strip():
        title = "Variation Listing"
    
    update_data = {
        "title": title.strip()[:80],  # Ensure title is valid
        "variesBy": varies_by,
        "inventoryItemGroup": {
            "aspects": aspects,  # Keep existing aspects
            "description": description
        },
        "variantSKUs": variant_skus
    }
    
    print(f"   Update payload keys: {list(update_data.keys())}")
    print(f"   Title in payload: {update_data['title']} (length: {len(update_data['title'])})")
    print(f"   inventoryItemGroup keys: {list(update_data['inventoryItemGroup'].keys())}")
    print(f"   Description in payload: {'description' in update_data['inventoryItemGroup']}")
    print()
    
    update_result = client.create_inventory_item_group(group_key, update_data)
    if update_result.get('success'):
        print(f"✅ Group updated successfully!")
        print(f"   Waiting 15 seconds for eBay to fully process and persist the description...")
        time.sleep(15)  # Longer wait for description to persist
    else:
        print(f"❌ Group update failed: {update_result.get('error')}")
        return
    print()
    
    # Verify description was saved by getting the group again
    print("Step 4b: Verifying description was saved...")
    verify_result = client.get_inventory_item_group(group_key)
    if verify_result.get('success'):
        verify_data = verify_result.get('data', {})
        # Note: eBay GET may not return description even if it's there
        print(f"   ✅ Group still exists")
        print(f"   ⚠️ Note: eBay GET may not return description even if it's stored")
    print()
    
    # Step 5: Try to publish
    print("Step 5: Attempting to publish...")
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    if publish_result.get('success'):
        listing_id = publish_result.get('data', {}).get('listingId')
        print(f"✅ SUCCESS! Listing published!")
        print(f"   Listing ID: {listing_id}")
        base_url = "https://www.ebay.com" if config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
        print(f"   View: {base_url}/itm/{listing_id}")
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"❌ Publish failed: {error}")
        if '25016' in str(error):
            print()
            print("Error 25016 still occurring. This suggests:")
            print("  1. Description update didn't persist")
            print("  2. eBay API has a timing issue")
            print("  3. Description format is still invalid")
            print()
            print("Try waiting a few minutes and running this script again.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        group_key = sys.argv[1]
    else:
        group_key = "GROUPSET1768800934"  # Default to latest
    
    fix_and_publish_group(group_key)
