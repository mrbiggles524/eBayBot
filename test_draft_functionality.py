"""Comprehensive test for draft and scheduled draft functionality."""
import sys
from ebay_listing import eBayListingManager
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

def test_regular_draft():
    """Test creating a regular draft (unpublished)."""
    print("\n" + "="*80)
    print("TEST 1: REGULAR DRAFT (publish=False)")
    print("="*80)
    
    manager = eBayListingManager()
    
    test_cards = [
        {'name': 'Test Draft 1', 'number': '1', 'quantity': 1, 'team': 'Test Team'},
        {'name': 'Test Draft 2', 'number': '2', 'quantity': 1, 'team': 'Test Team'}
    ]
    
    result = manager.create_variation_listing(
        cards=test_cards,
        title="TEST DRAFT - Please Delete",
        description="<p><strong>Test Draft</strong></p><p>This is a test draft listing.</p>",
        category_id="261328",
        price=1.00,
        quantity=1,
        condition="Near Mint",
        publish=False,  # DRAFT
        schedule_draft=False
    )
    
    print(f"\n✅ Success: {result.get('success')}")
    print(f"📦 Group Key: {result.get('group_key') or result.get('groupKey')}")
    print(f"📊 Status: {result.get('status', 'unknown')}")
    print(f"📝 Draft: {result.get('draft', False)}")
    print(f"📅 Published: {result.get('published', False)}")
    
    if result.get('success'):
        group_key = result.get('group_key') or result.get('groupKey')
        print(f"\n[VERIFY] Checking group: {group_key}")
        
        # Verify group exists
        group_result = manager.api_client.get_inventory_item_group(group_key)
        if group_result.get('success'):
            print("✅ Group exists!")
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            print(f"   Variant SKUs: {len(variant_skus)}")
            
            # Check offers
            for sku in variant_skus[:2]:
                offer_result = manager.api_client.get_offer_by_sku(sku)
                if offer_result.get('success'):
                    offer = offer_result.get('offer', {})
                    listing_id = offer.get('listingId')
                    status = offer.get('listing', {}).get('listingStatus', 'UNKNOWN')
                    print(f"   SKU {sku}: listingId={listing_id}, status={status}")
                    if listing_id:
                        print(f"      ⚠️ WARNING: Has listingId - this means it was published!")
                    else:
                        print(f"      ✅ No listingId - this is a draft")
        else:
            print(f"❌ Group not found: {group_result.get('error')}")
    
    return result

def test_scheduled_draft():
    """Test creating a scheduled draft."""
    print("\n" + "="*80)
    print("TEST 2: SCHEDULED DRAFT (schedule_draft=True, publish=True)")
    print("="*80)
    
    manager = eBayListingManager()
    
    test_cards = [
        {'name': 'Scheduled Test 1', 'number': '1', 'quantity': 1, 'team': 'Test Team'},
        {'name': 'Scheduled Test 2', 'number': '2', 'quantity': 1, 'team': 'Test Team'}
    ]
    
    schedule_hours = 24
    result = manager.create_variation_listing(
        cards=test_cards,
        title="TEST SCHEDULED - Please Delete",
        description="<p><strong>Test Scheduled</strong></p><p>This is a test scheduled listing.</p>",
        category_id="261328",
        price=1.00,
        quantity=1,
        condition="Near Mint",
        publish=True,  # Must publish for scheduled
        schedule_draft=True,  # Schedule it
        schedule_hours=schedule_hours
    )
    
    print(f"\n✅ Success: {result.get('success')}")
    print(f"📦 Group Key: {result.get('group_key') or result.get('groupKey')}")
    print(f"📊 Status: {result.get('status', 'unknown')}")
    print(f"📅 Scheduled: {result.get('scheduled', False)}")
    print(f"📅 Published: {result.get('published', False)}")
    print(f"⏰ Schedule Hours: {result.get('scheduleHours', schedule_hours)}")
    print(f"📅 Start Date: {result.get('listingStartDate', 'NOT SET')}")
    
    if result.get('success'):
        group_key = result.get('group_key') or result.get('groupKey')
        print(f"\n[VERIFY] Checking scheduled listing for group: {group_key}")
        
        # Verify group exists
        group_result = manager.api_client.get_inventory_item_group(group_key)
        if group_result.get('success'):
            print("✅ Group exists!")
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            print(f"   Variant SKUs: {len(variant_skus)}")
            
            # Check offers for listingStartDate
            scheduled_count = 0
            for sku in variant_skus[:2]:
                offer_result = manager.api_client.get_offer_by_sku(sku)
                if offer_result.get('success'):
                    offer = offer_result.get('offer', {})
                    start_date = offer.get('listingStartDate')
                    listing_id = offer.get('listingId')
                    status = offer.get('listing', {}).get('listingStatus', 'UNKNOWN')
                    
                    print(f"\n   SKU {sku}:")
                    print(f"      listingId: {listing_id}")
                    print(f"      Status: {status}")
                    print(f"      listingStartDate: {start_date if start_date else '❌ MISSING!'}")
                    
                    if start_date:
                        scheduled_count += 1
                        # Parse date
                        try:
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                            hours_until = (start_dt - now).total_seconds() / 3600
                            print(f"      ⏰ Will go live in: {hours_until:.1f} hours")
                            print(f"      ✅ Has listingStartDate - scheduled correctly!")
                        except Exception as e:
                            print(f"      ⚠️ Could not parse date: {e}")
                    else:
                        print(f"      ❌ MISSING listingStartDate - scheduled draft will NOT work!")
            
            if scheduled_count == len(variant_skus):
                print(f"\n✅ All {scheduled_count} offers have listingStartDate - scheduled draft should work!")
            else:
                print(f"\n⚠️ Only {scheduled_count}/{len(variant_skus)} offers have listingStartDate")
        else:
            print(f"❌ Group not found: {group_result.get('error')}")
    
    return result

if __name__ == "__main__":
    print("="*80)
    print("COMPREHENSIVE DRAFT & SCHEDULED DRAFT TEST")
    print("="*80)
    
    try:
        # Test 1: Regular draft
        draft_result = test_regular_draft()
        
        # Test 2: Scheduled draft
        scheduled_result = test_scheduled_draft()
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Regular Draft Test: {'✅ PASSED' if draft_result.get('success') else '❌ FAILED'}")
        print(f"Scheduled Draft Test: {'✅ PASSED' if scheduled_result.get('success') else '❌ FAILED'}")
        
        if scheduled_result.get('success'):
            has_start_date = scheduled_result.get('listingStartDate') is not None
            print(f"listingStartDate Set: {'✅ YES' if has_start_date else '❌ NO'}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
