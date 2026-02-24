"""
Comprehensive diagnostic script to find ALL listings and understand why they're not appearing in Seller Hub.
"""
import sys
import json
from datetime import datetime
from ebay_api_client import eBayAPIClient
from config import Config

sys.stdout.reconfigure(encoding='utf-8')

def diagnose_listings():
    """Comprehensive diagnosis of all listings."""
    print("=" * 80)
    print("COMPREHENSIVE LISTING DIAGNOSIS")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    env_name = config.EBAY_ENVIRONMENT.upper()
    api_url = config.ebay_api_url
    
    print(f"Environment: {env_name}")
    print(f"API URL: {api_url}")
    print()
    
    if env_name != 'PRODUCTION':
        print("⚠️ WARNING: Not using PRODUCTION!")
        print()
    else:
        print("✅ Using PRODUCTION environment")
        print()
    
    # Step 1: Get ALL offers
    print("=" * 80)
    print("STEP 1: Fetching ALL offers from API")
    print("=" * 80)
    print()
    
    all_offers = []
    offset = 0
    limit = 200
    max_pages = 20
    
    # Try to get offers - but this endpoint requires a SKU parameter
    # Instead, let's try to get inventory items first
    print("Note: /sell/inventory/v1/offer requires a SKU parameter.")
    print("Trying alternative approach: checking inventory items...")
    print()
    
    # Get inventory items instead
    try:
        print("Fetching inventory items...")
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 200})
        if response.status_code == 200:
            data = response.json()
            inventory_items = data.get('inventoryItems', [])
            print(f"  Found {len(inventory_items)} inventory items")
            
            # Now try to get offers for each SKU
            print()
            print("Fetching offers for each inventory item...")
            for item in inventory_items[:20]:  # Limit to first 20 to avoid too many requests
                sku = item.get('sku', '')
                if sku:
                    try:
                        offer_response = client._make_request('GET', '/sell/inventory/v1/offer', params={'sku': sku})
                        if offer_response.status_code == 200:
                            offer_data = offer_response.json()
                            offers_list = offer_data.get('offers', [])
                            all_offers.extend(offers_list)
                            if offers_list:
                                print(f"  SKU {sku}: Found {len(offers_list)} offer(s)")
                    except Exception as e:
                        print(f"  SKU {sku}: Error - {e}")
        else:
            print(f"  Error fetching inventory items: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print(f"Total offers found: {len(all_offers)}")
    print()
    
    # Step 2: Analyze offers
    print("=" * 80)
    print("STEP 2: Analyzing offers")
    print("=" * 80)
    print()
    
    groups_found = {}
    offers_by_status = {
        'UNPUBLISHED': [],
        'PUBLISHED': [],
        'UNKNOWN': []
    }
    
    for offer in all_offers:
        offer_id = offer.get('offerId', '')
        sku = offer.get('sku', '')
        listing_id = offer.get('listingId', '')
        status = offer.get('status', 'UNKNOWN')
        listing = offer.get('listing', {})
        listing_status = listing.get('listingStatus', 'UNKNOWN')
        group_key = offer.get('inventoryItemGroupKey', '')
        start_date = offer.get('listingStartDate', '') or listing.get('listingStartDate', '')
        title = listing.get('title', offer.get('title', 'No title'))
        
        # Track groups
        if group_key:
            if group_key not in groups_found:
                groups_found[group_key] = {
                    'offers': [],
                    'has_listing_id': False,
                    'has_start_date': False,
                    'statuses': set()
                }
            groups_found[group_key]['offers'].append({
                'sku': sku,
                'offer_id': offer_id,
                'listing_id': listing_id,
                'status': listing_status or status,
                'start_date': start_date,
                'title': title
            })
            if listing_id:
                groups_found[group_key]['has_listing_id'] = True
            if start_date:
                groups_found[group_key]['has_start_date'] = True
            groups_found[group_key]['statuses'].add(listing_status or status)
        
        # Categorize by status
        final_status = listing_status or status
        if final_status == 'UNPUBLISHED' or not listing_id:
            offers_by_status['UNPUBLISHED'].append(offer)
        elif listing_id:
            offers_by_status['PUBLISHED'].append(offer)
        else:
            offers_by_status['UNKNOWN'].append(offer)
    
    # Step 3: Report findings
    print("=" * 80)
    print("STEP 3: FINDINGS")
    print("=" * 80)
    print()
    
    print(f"Total Offers: {len(all_offers)}")
    print(f"  - Unpublished (drafts): {len(offers_by_status['UNPUBLISHED'])}")
    print(f"  - Published (active/scheduled): {len(offers_by_status['PUBLISHED'])}")
    print(f"  - Unknown status: {len(offers_by_status['UNKNOWN'])}")
    print()
    
    print(f"Variation Groups Found: {len(groups_found)}")
    print()
    
    if groups_found:
        print("Group Details:")
        print("-" * 80)
        for group_key, group_info in groups_found.items():
            print(f"\nGroup: {group_key}")
            print(f"  Offers in group: {len(group_info['offers'])}")
            print(f"  Has listing ID (published): {group_info['has_listing_id']}")
            print(f"  Has start date (scheduled): {group_info['has_start_date']}")
            print(f"  Statuses: {', '.join(group_info['statuses']) if group_info['statuses'] else 'None'}")
            
            for offer in group_info['offers']:
                print(f"    - SKU: {offer['sku']}")
                print(f"      Offer ID: {offer['offer_id']}")
                print(f"      Listing ID: {offer['listing_id'] or 'NONE (unpublished)'}")
                print(f"      Status: {offer['status']}")
                print(f"      Start Date: {offer['start_date'] or 'MISSING'}")
                
                # Determine where it should appear
                if offer['start_date']:
                    print(f"      → Should appear in: Scheduled Listings")
                elif offer['listing_id']:
                    print(f"      → Should appear in: Active Listings")
                else:
                    print(f"      → Should appear in: Drafts (may not be visible)")
    else:
        print("⚠️ NO VARIATION GROUPS FOUND!")
        print("This means either:")
        print("  1. No listings have been created successfully")
        print("  2. Listings were created but offers aren't linked to groups")
        print("  3. Listings are in a different account/environment")
    
    print()
    print("=" * 80)
    print("STEP 4: Checking specific test groups")
    print("=" * 80)
    print()
    
    # Check for recent test groups
    test_groups = [
        "GROUPSET1768799945",
        "GROUPSET1768799557",
        "GROUPSET1768799124",
        "GROUPSET1768797951"
    ]
    
    for test_group in test_groups:
        print(f"Checking group: {test_group}")
        group_result = client.get_inventory_item_group(test_group)
        if group_result.get('success'):
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            print(f"  ✅ Group exists!")
            print(f"  Variant SKUs: {len(variant_skus)}")
            for sku in variant_skus[:5]:
                print(f"    - {sku}")
            
            # Check offers for these SKUs
            for sku in variant_skus[:3]:
                offer_result = client.get_offer_by_sku(sku)
                if offer_result.get('success'):
                    offer = offer_result.get('offer', {})
                    listing_id = offer.get('listingId', '')
                    status = offer.get('status', '')
                    start_date = offer.get('listingStartDate', '')
                    print(f"    SKU {sku}:")
                    print(f"      Listing ID: {listing_id or 'NONE'}")
                    print(f"      Status: {status}")
                    print(f"      Start Date: {start_date or 'NONE'}")
        else:
            print(f"  ❌ Group not found: {group_result.get('error', 'Unknown error')}")
        print()
    
    # Step 5: Recommendations
    print("=" * 80)
    print("STEP 5: RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    if len(all_offers) == 0:
        print("❌ NO OFFERS FOUND AT ALL")
        print("This suggests:")
        print("  1. Wrong environment (check .env file)")
        print("  2. Wrong account/token")
        print("  3. No listings have been created")
    elif len(groups_found) == 0:
        print("⚠️ OFFERS EXIST BUT NO GROUPS")
        print("This suggests:")
        print("  1. Offers were created but group creation failed")
        print("  2. Offers aren't linked to groups")
        print("  3. Error 25016 or 25703 prevented group creation")
    else:
        print("✅ Groups found! Check the details above.")
        print("If they're not in Seller Hub, possible reasons:")
        print("  1. Error 25016 prevented publishing (description issue)")
        print("  2. Listings are unpublished (drafts) - may not appear in Seller Hub")
        print("  3. Need to wait a few minutes for eBay to sync")
    
    print()
    base_url = "https://www.ebay.com" if env_name == 'PRODUCTION' else "https://sandbox.ebay.com"
    print("Seller Hub Links:")
    print(f"  Scheduled: {base_url}/sh/lst/scheduled")
    print(f"  Active: {base_url}/sh/lst/active")
    print(f"  Drafts: {base_url}/sh/lst/drafts")
    print(f"  Unsold: {base_url}/sh/lst/unsold")
    print()

if __name__ == "__main__":
    diagnose_listings()
