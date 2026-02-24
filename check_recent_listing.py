"""
Check the most recent listing attempt to see what happened.
"""
import sys
from ebay_api_client import eBayAPIClient
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

def check_recent_listings():
    """Check for recent listings created in the last hour."""
    print("=" * 80)
    print("CHECKING RECENT LISTINGS")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get all inventory items
    print("Step 1: Getting all inventory items...")
    items_result = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
    
    if items_result.status_code != 200:
        print(f"❌ Failed to get items: {items_result.status_code}")
        return
    
    items_data = items_result.json()
    inventory_items = items_data.get('inventoryItems', [])
    print(f"✅ Found {len(inventory_items)} inventory items")
    print()
    
    # Check recent SKUs (last hour)
    print("Step 2: Checking recent offers...")
    recent_skus = []
    for item in inventory_items[-10:]:  # Check last 10 items
        sku = item.get('sku', '')
        if 'CARD_SET' in sku:
            recent_skus.append(sku)
    
    print(f"Found {len(recent_skus)} recent card SKUs")
    print()
    
    # Check each SKU's offer
    scheduled_count = 0
    active_count = 0
    draft_count = 0
    
    for sku in recent_skus:
        print(f"Checking {sku}...")
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            offer_id = offer.get('offerId')
            listing_id = offer.get('listingId')
            start_date = offer.get('listingStartDate', '')
            group_key = offer.get('inventoryItemGroupKey', '')
            status = offer.get('status', 'UNKNOWN')
            
            print(f"  Offer ID: {offer_id}")
            print(f"  Listing ID: {listing_id or 'None (draft)'}")
            print(f"  Group Key: {group_key or 'None'}")
            print(f"  Status: {status}")
            print(f"  listingStartDate: {start_date or '❌ MISSING'}")
            
            if listing_id:
                if start_date:
                    # Check if start date is in future
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                        if start_dt > now:
                            print(f"  ✅ SCHEDULED (will go live in {(start_dt - now).total_seconds() / 3600:.1f} hours)")
                            scheduled_count += 1
                        else:
                            print(f"  ⚠️ ACTIVE (start date in past)")
                            active_count += 1
                    except:
                        print(f"  ⚠️ ACTIVE (could not parse date)")
                        active_count += 1
                else:
                    print(f"  ⚠️ ACTIVE (no start date)")
                    active_count += 1
            else:
                print(f"  ⚠️ DRAFT (no listing ID)")
                draft_count += 1
        else:
            print(f"  ❌ Could not get offer: {offer_result.get('error')}")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Scheduled: {scheduled_count}")
    print(f"Active: {active_count}")
    print(f"Draft: {draft_count}")
    print()
    
    if scheduled_count > 0:
        print("✅ Found scheduled listings! They should appear in Seller Hub > Scheduled Listings")
    elif active_count > 0:
        print("⚠️ Listings went ACTIVE instead of scheduled")
        print("   This means listingStartDate was not set or was in the past")
    elif draft_count > 0:
        print("⚠️ Listings are drafts (not published)")
        print("   Drafts may not appear in Seller Hub")

if __name__ == "__main__":
    check_recent_listings()
