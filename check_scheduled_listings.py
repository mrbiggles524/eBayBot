"""
Check if any listings appear in scheduled listings.
"""
import sys
from ebay_api_client import eBayAPIClient
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def check_scheduled_listings():
    """Check for scheduled listings via API."""
    print("=" * 80)
    print("CHECKING SCHEDULED LISTINGS")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get all offers and check for scheduled ones
    print("Step 1: Getting all inventory items...")
    items_result = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
    
    if items_result.status_code != 200:
        print(f"❌ Failed to get items: {items_result.status_code}")
        return
    
    items_data = items_result.json()
    inventory_items = items_data.get('inventoryItems', [])
    print(f"✅ Found {len(inventory_items)} inventory items")
    print()
    
    # Check offers for scheduled listings
    print("Step 2: Checking offers for scheduled listings...")
    scheduled_listings = []
    active_listings = []
    draft_listings = []
    
    for item in inventory_items:
        sku = item.get('sku', '')
        if 'CARD_SET' in sku:
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result.get('offer', {})
                listing_id = offer.get('listingId')
                start_date = offer.get('listingStartDate', '')
                group_key = offer.get('inventoryItemGroupKey', '')
                
                if listing_id:
                    if start_date:
                        try:
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                            if start_dt > now:
                                scheduled_listings.append({
                                    'sku': sku,
                                    'listing_id': listing_id,
                                    'start_date': start_date,
                                    'group_key': group_key,
                                    'hours_until': (start_dt - now).total_seconds() / 3600
                                })
                            else:
                                active_listings.append({
                                    'sku': sku,
                                    'listing_id': listing_id,
                                    'group_key': group_key
                                })
                        except:
                            active_listings.append({
                                'sku': sku,
                                'listing_id': listing_id,
                                'group_key': group_key
                            })
                    else:
                        active_listings.append({
                            'sku': sku,
                            'listing_id': listing_id,
                            'group_key': group_key
                        })
                else:
                    draft_listings.append({
                        'sku': sku,
                        'group_key': group_key
                    })
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Scheduled Listings: {len(scheduled_listings)}")
    if scheduled_listings:
        print("✅ Found scheduled listings:")
        for listing in scheduled_listings:
            print(f"   SKU: {listing['sku']}")
            print(f"   Listing ID: {listing['listing_id']}")
            print(f"   Group Key: {listing['group_key']}")
            print(f"   Will go live in: {listing['hours_until']:.1f} hours")
            print(f"   Start Date: {listing['start_date']}")
            print()
    else:
        print("❌ No scheduled listings found")
        print()
    
    print(f"Active Listings: {len(active_listings)}")
    if active_listings:
        for listing in active_listings[:5]:
            print(f"   SKU: {listing['sku']}, Listing ID: {listing['listing_id']}")
    
    print()
    print(f"Draft Listings: {len(draft_listings)}")
    if draft_listings:
        for listing in draft_listings[:5]:
            print(f"   SKU: {listing['sku']}, Group: {listing['group_key']}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if scheduled_listings:
        print("✅ Scheduled listings exist! They should appear in:")
        print("   https://www.ebay.com/sh/lst/scheduled")
    else:
        print("❌ No scheduled listings found")
        print("   This means either:")
        print("   1. No listings were created with listingStartDate")
        print("   2. Listings went active instead of scheduled")
        print("   3. Listings failed to publish")

if __name__ == "__main__":
    check_scheduled_listings()
