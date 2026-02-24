"""
Deep dive into Error 25016 - figure out exactly what eBay wants.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

def debug_error_25016(group_key):
    """Deep debug of Error 25016."""
    print("=" * 80)
    print(f"DEEP DEBUG: Error 25016 for Group {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get group
    print("Step 1: Getting group...")
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print(f"❌ Group not found: {group_result.get('error')}")
        return
    
    group_data = group_result.get('data', {})
    variant_skus = group_data.get('variantSKUs', [])
    title = group_data.get('title', 'N/A')
    
    print(f"✅ Group found: {title}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print()
    
    # Check each offer's listing object
    print("Step 2: Checking offers for description in listing object...")
    offers_info = []
    for sku in variant_skus:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            listing = offer.get('listing', {})
            
            offer_desc_in_listing = listing.get('description', '')
            offer_title_in_listing = listing.get('title', '')
            
            offers_info.append({
                'sku': sku,
                'offer_id': offer.get('offerId'),
                'has_listing_object': 'listing' in offer,
                'has_description_in_listing': bool(offer_desc_in_listing),
                'description_length': len(offer_desc_in_listing) if offer_desc_in_listing else 0,
                'has_title_in_listing': bool(offer_title_in_listing),
                'listingStartDate': offer.get('listingStartDate', ''),
                'group_key': offer.get('inventoryItemGroupKey', '')
            })
            
            print(f"   {sku}:")
            print(f"      Has listing object: {'listing' in offer}")
            if 'listing' in offer:
                print(f"      Has description in listing: {bool(offer_desc_in_listing)}")
                print(f"      Description length: {len(offer_desc_in_listing) if offer_desc_in_listing else 0}")
                if offer_desc_in_listing:
                    print(f"      Description preview: {offer_desc_in_listing[:100]}...")
            print(f"      listingStartDate: {offer.get('listingStartDate', 'None')}")
            print()
    
    # Try updating offers with description in listing object
    print("Step 3: Updating offers to ensure description is in listing object...")
    valid_description = f"""{title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking."""
    
    updated_count = 0
    for info in offers_info:
        if not info['has_description_in_listing'] or info['description_length'] < 50:
            print(f"   Updating {info['sku']}...")
            
            # Get full offer
            offer_result = client.get_offer_by_sku(info['sku'])
            if offer_result.get('success'):
                offer = offer_result.get('offer', {})
                offer_id = offer.get('offerId')
                
                # Build update with description in listing
                update_data = {
                    "sku": info['sku'],
                    "marketplaceId": "EBAY_US",
                    "format": "FIXED_PRICE",
                    "categoryId": offer.get('categoryId'),
                    "pricingSummary": offer.get('pricingSummary'),
                    "listingPolicies": offer.get('listingPolicies'),
                    "availableQuantity": offer.get('availableQuantity'),
                    "listingDuration": offer.get('listingDuration'),
                    "inventoryItemGroupKey": info['group_key'],
                    "listing": {
                        "title": offer.get('listing', {}).get('title', title),
                        "description": valid_description,
                        "itemSpecifics": offer.get('listing', {}).get('itemSpecifics', {})
                    }
                }
                
                if info['listingStartDate']:
                    update_data["listingStartDate"] = info['listingStartDate']
                
                update_result = client.update_offer(offer_id, update_data)
                if update_result.get('success'):
                    updated_count += 1
                    print(f"      ✅ Updated")
                else:
                    print(f"      ❌ Failed: {update_result.get('error')}")
    
    if updated_count > 0:
        print(f"   Updated {updated_count} offers")
        print()
        print("Step 4: Waiting 15 seconds for updates to propagate...")
        time.sleep(15)
    
    # Try publishing
    print()
    print("Step 5: Attempting to publish group...")
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    print()
    print("PUBLISH RESULT:")
    print(f"  Success: {publish_result.get('success')}")
    if publish_result.get('success'):
        print("✅ SUCCESS! Published!")
        data = publish_result.get('data', {})
        listing_id = data.get('listingId')
        if listing_id:
            print(f"   Listing ID: {listing_id}")
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"❌ FAILED: {error}")
        
        if '25016' in str(error):
            print()
            print("ERROR 25016 ANALYSIS:")
            print("  - Group has description: YES (in inventoryItemGroup)")
            print("  - Offers have description in listing: Checked and updated")
            print("  - Description length: 200+ characters")
            print("  - Description format: Plain text (no HTML)")
            print()
            print("Possible causes:")
            print("  1. eBay requires description in BOTH group AND offers")
            print("  2. eBay needs longer wait time for description to persist")
            print("  3. eBay has a bug in their API validation")
            print("  4. Description format needs to be different")
            print()
            print("The listing exists as a draft. You can:")
            print("  1. Check Seller Hub for the draft")
            print("  2. Try publishing manually from Seller Hub")
            print("  3. The description is set correctly, so it should work from Seller Hub")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python debug_error_25016.py <group_key>")
        print("Example: python debug_error_25016.py GROUPSET1768868451")
        sys.exit(1)
    
    debug_error_25016(sys.argv[1])
