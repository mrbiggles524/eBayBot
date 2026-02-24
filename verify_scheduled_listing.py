"""
Verify that a scheduled listing appears in scheduled listings.
Takes a group key as argument.
"""
import sys
from ebay_api_client import eBayAPIClient
from datetime import datetime
import time

sys.stdout.reconfigure(encoding='utf-8')

def verify_scheduled_listing(group_key):
    """Verify a scheduled listing by group key."""
    print("=" * 80)
    print(f"VERIFYING SCHEDULED LISTING: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get the group
    print("Step 1: Getting group details...")
    group_result = client.get_inventory_item_group(group_key)
    
    if not group_result.get('success'):
        print(f"❌ Group not found: {group_result.get('error')}")
        return
    
    group_data = group_result.get('data', {})
    variant_skus = group_data.get('variantSKUs', [])
    print(f"✅ Group found with {len(variant_skus)} variant SKUs")
    print()
    
    # Check each offer
    print("Step 2: Checking offers for scheduled status...")
    scheduled_count = 0
    active_count = 0
    draft_count = 0
    
    for sku in variant_skus:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            listing_id = offer.get('listingId')
            start_date = offer.get('listingStartDate', '')
            status = offer.get('status', 'UNKNOWN')
            
            print(f"   SKU: {sku}")
            print(f"      Listing ID: {listing_id or 'None (draft)'}")
            print(f"      Status: {status}")
            print(f"      listingStartDate: {start_date or '❌ MISSING'}")
            
            if listing_id:
                if start_date:
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                        hours_until = (start_dt - now).total_seconds() / 3600
                        
                        if start_dt > now:
                            print(f"      ✅ SCHEDULED (will go live in {hours_until:.1f} hours)")
                            scheduled_count += 1
                        else:
                            print(f"      ⚠️ ACTIVE (start date in past)")
                            active_count += 1
                    except Exception as e:
                        print(f"      ⚠️ ACTIVE (could not parse date: {e})")
                        active_count += 1
                else:
                    print(f"      ⚠️ ACTIVE (no start date)")
                    active_count += 1
            else:
                print(f"      ⚠️ DRAFT (no listing ID)")
                draft_count += 1
        else:
            print(f"      ❌ Could not get offer: {offer_result.get('error')}")
        print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print(f"Scheduled: {scheduled_count}/{len(variant_skus)}")
    print(f"Active: {active_count}/{len(variant_skus)}")
    print(f"Draft: {draft_count}/{len(variant_skus)}")
    print()
    
    if scheduled_count == len(variant_skus):
        print("✅ SUCCESS! All offers are scheduled")
        print()
        print("The listing should appear in:")
        print("   https://www.ebay.com/sh/lst/scheduled")
        print()
        print("NOTE: It may take 1-2 minutes for eBay to process and show it in Seller Hub")
    elif active_count > 0:
        print("⚠️ WARNING: Some offers went ACTIVE instead of scheduled")
        print("   This means listingStartDate was not set or was in the past")
    elif draft_count > 0:
        print("⚠️ WARNING: Offers are still drafts (not published)")
        print("   The listing may have failed to publish")
    else:
        print("❌ No scheduled listings found")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_scheduled_listing.py <group_key>")
        print("Example: python verify_scheduled_listing.py GROUPSET1768849629")
        sys.exit(1)
    
    group_key = sys.argv[1]
    verify_scheduled_listing(group_key)
