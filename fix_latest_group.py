"""
Fix the latest group (GROUPSET1768801415) with description and try to publish.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import time
import re

sys.stdout.reconfigure(encoding='utf-8')

def strip_html(html_text):
    """Strip HTML tags from text, keeping only the text content."""
    if not html_text:
        return html_text
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_text)
    # Clean up multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def fix_and_publish_group(group_key: str):
    """Fix group description and try to publish."""
    print("=" * 80)
    print(f"FIXING GROUP: {group_key}")
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
    title = group_data.get('title', 'Variation Listing')
    variant_skus = group_data.get('variantSKUs', [])
    varies_by = group_data.get('variesBy', {})
    
    print(f"✅ Group retrieved")
    print(f"   Title: {title}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print()
    
    # Step 2: Build description (plain text, no HTML)
    print("Step 2: Building description...")
    description = f"""{title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve + top loader via PWE with eBay tracking."""
    
    print(f"   Description length: {len(description)}")
    print(f"   Description preview: {description[:100]}...")
    print()
    
    # Step 3: Get aspects (rebuild if needed)
    print("Step 3: Getting aspects...")
    aspects = {}
    if 'inventoryItemGroup' in group_data:
        aspects = group_data['inventoryItemGroup'].get('aspects', {})
    
    # If no aspects, try to build from offers
    if not aspects and variant_skus:
        print("   No aspects found - building from offers...")
        card_names = []
        card_numbers = []
        
        for sku in variant_skus[:3]:  # Check first 3
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result.get('offer', {})
                listing = offer.get('listing', {})
                offer_title = listing.get('title', '')
                
                # Try to extract info from title or SKU
                # SKU format: CARD_SET_NAME_NUMBER_X
                parts = sku.split('_')
                if len(parts) >= 4:
                    # Try to find card number
                    for part in parts:
                        if part.startswith('BD-') or (part.isdigit() and len(part) <= 3):
                            card_numbers.append(part)
                            break
        
        if card_names:
            aspects["Card Name"] = list(set(card_names))
        if card_numbers:
            aspects["Card Number"] = list(set(card_numbers))
    
    if not aspects:
        aspects = {}
        print("   ⚠️ Using empty aspects dict")
    else:
        print(f"   ✅ Built aspects: {list(aspects.keys())}")
    print()
    
    # Step 4: Update group with description in inventoryItemGroup
    print("Step 4: Updating group with description...")
    print("   CRITICAL: Description must be in inventoryItemGroup.description")
    
    update_data = {
        "title": title.strip()[:80],  # Ensure title is valid
        "variesBy": varies_by,
        "inventoryItemGroup": {
            "aspects": aspects,
            "description": description  # CRITICAL: Description in inventoryItemGroup
        },
        "variantSKUs": variant_skus
    }
    
    print(f"   Update payload structure:")
    print(f"     - title: {update_data['title']}")
    print(f"     - has inventoryItemGroup: True")
    print(f"     - inventoryItemGroup.aspects: {list(update_data['inventoryItemGroup']['aspects'].keys())}")
    print(f"     - inventoryItemGroup.description: {len(update_data['inventoryItemGroup']['description'])} chars")
    print()
    
    update_result = client.create_inventory_item_group(group_key, update_data)
    if update_result.get('success'):
        print(f"✅ Group updated successfully!")
        print(f"   Waiting 25 seconds for eBay to fully process and persist...")
        time.sleep(25)  # Long wait for persistence
    else:
        print(f"❌ Group update failed: {update_result.get('error')}")
        return
    print()
    
    # Step 5: Verify description was saved (eBay GET may not return it, but we'll check)
    print("Step 5: Verifying update...")
    verify_result = client.get_inventory_item_group(group_key)
    if verify_result.get('success'):
        verify_data = verify_result.get('data', {})
        print(f"   ✅ Group still exists")
        inv_group = verify_data.get('inventoryItemGroup', {})
        if inv_group:
            print(f"   ✅ inventoryItemGroup exists")
            if 'description' in inv_group:
                print(f"   ✅ Description found in GET response!")
            else:
                print(f"   ⚠️ Description not in GET response (normal - eBay may not return it)")
        else:
            print(f"   ⚠️ inventoryItemGroup not in GET response (normal)")
    print()
    
    # Step 6: Try to publish
    print("Step 6: Attempting to publish...")
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    if publish_result.get('success'):
        listing_id = publish_result.get('data', {}).get('listingId')
        print(f"✅ SUCCESS! Listing published!")
        print(f"   Listing ID: {listing_id}")
        base_url = "https://www.ebay.com" if config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
        print(f"   View: {base_url}/itm/{listing_id}")
        print(f"   Scheduled Listings: {base_url}/sh/lst/scheduled")
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"❌ Publish failed: {error}")
        if '25016' in str(error):
            print()
            print("Error 25016 still occurring. Possible causes:")
            print("  1. Description format issue (HTML vs plain text)")
            print("  2. eBay API timing/persistence issue")
            print("  3. Description needs to be in offers too")
            print()
            print("Next steps:")
            print("  1. Check Seller Hub manually: https://www.ebay.com/sh/lst/scheduled")
            print("  2. Try editing the listing in Seller Hub and adding description manually")
            print("  3. Then publish from Seller Hub")

if __name__ == "__main__":
    group_key = "GROUPSET1768801415"
    fix_and_publish_group(group_key)
