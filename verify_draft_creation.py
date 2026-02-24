"""Quick verification script for draft and scheduled draft creation."""
import sys
from ebay_listing import eBayListingManager
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

def verify_draft_workflow():
    """Test and verify draft creation workflow."""
    print("=" * 80)
    print("DRAFT & SCHEDULED DRAFT VERIFICATION")
    print("=" * 80)
    
    manager = eBayListingManager()
    
    # Test with minimal data
    test_cards = [
        {
            'name': 'Verify Player',
            'number': '1',
            'quantity': 1,
            'team': 'Test Team'
        }
    ]
    
    print("\n[TEST 1] Regular Draft (publish=False)")
    print("-" * 80)
    result1 = manager.create_variation_listing(
        cards=test_cards,
        title="VERIFY DRAFT TEST",
        description="<p><strong>Verify Draft Test</strong></p><p>Testing draft creation.</p>",
        category_id="261328",
        price=1.00,
        quantity=1,
        condition="Near Mint",
        publish=False,  # Draft
        schedule_draft=False
    )
    
    print(f"Success: {result1.get('success')}")
    print(f"Group Key: {result1.get('group_key')}")
    print(f"Status: {result1.get('status', 'unknown')}")
    print(f"Draft: {result1.get('draft', False)}")
    
    if result1.get('success'):
        group_key = result1.get('group_key')
        # Verify group exists
        group_check = manager.api_client.get_inventory_item_group(group_key)
        if group_check.get('success'):
            print("✅ Group exists and verified")
            # Check offers
            group_data = group_check.get('data', {})
            skus = group_data.get('variantSKUs', [])
            print(f"   Variant SKUs: {len(skus)}")
            for sku in skus:
                offer_check = manager.api_client.get_offer_by_sku(sku)
                if offer_check.get('success'):
                    offer = offer_check.get('offer', {})
                    listing_id = offer.get('listingId')
                    listing_status = offer.get('listing', {}).get('listingStatus', 'UNKNOWN')
                    print(f"   SKU {sku}: Status={listing_status}, ListingID={listing_id or 'None (draft)'}")
        else:
            print(f"❌ Group verification failed: {group_check.get('error')}")
    
    print("\n[TEST 2] Scheduled Draft (schedule_draft=True, publish=True)")
    print("-" * 80)
    result2 = manager.create_variation_listing(
        cards=test_cards,
        title="VERIFY SCHEDULED TEST",
        description="<p><strong>Verify Scheduled Test</strong></p><p>Testing scheduled draft creation.</p>",
        category_id="261328",
        price=1.00,
        quantity=1,
        condition="Near Mint",
        publish=True,  # Must publish for scheduled
        schedule_draft=True,  # Schedule it
        schedule_hours=24
    )
    
    print(f"Success: {result2.get('success')}")
    print(f"Group Key: {result2.get('group_key')}")
    print(f"Status: {result2.get('status', 'unknown')}")
    print(f"Scheduled: {result2.get('scheduled', False)}")
    
    if result2.get('success'):
        group_key = result2.get('group_key')
        # Verify group exists
        group_check = manager.api_client.get_inventory_item_group(group_key)
        if group_check.get('success'):
            print("✅ Group exists and verified")
            # Check offers for listingStartDate
            group_data = group_check.get('data', {})
            skus = group_data.get('variantSKUs', [])
            print(f"   Variant SKUs: {len(skus)}")
            for sku in skus:
                offer_check = manager.api_client.get_offer_by_sku(sku)
                if offer_check.get('success'):
                    offer = offer_check.get('offer', {})
                    listing_id = offer.get('listingId')
                    start_date = offer.get('listingStartDate')
                    listing_status = offer.get('listing', {}).get('listingStatus', 'UNKNOWN')
                    print(f"   SKU {sku}:")
                    print(f"      Status: {listing_status}")
                    print(f"      ListingID: {listing_id or 'None'}")
                    print(f"      StartDate: {start_date or 'MISSING!'}")
                    if start_date:
                        try:
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                            hours = (start_dt - now).total_seconds() / 3600
                            print(f"      Will go live in: {hours:.1f} hours")
                        except:
                            pass
                    else:
                        print(f"      ⚠️ WARNING: listingStartDate is MISSING!")
        else:
            print(f"❌ Group verification failed: {group_check.get('error')}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Regular Draft: {'✅ PASSED' if result1.get('success') else '❌ FAILED'}")
    print(f"Scheduled Draft: {'✅ PASSED' if result2.get('success') else '❌ FAILED'}")
    
    if result2.get('success'):
        # Check if listingStartDate was set
        group_key = result2.get('group_key')
        group_check = manager.api_client.get_inventory_item_group(group_key)
        if group_check.get('success'):
            skus = group_check.get('data', {}).get('variantSKUs', [])
            has_start_date = False
            for sku in skus:
                offer_check = manager.api_client.get_offer_by_sku(sku)
                if offer_check.get('success'):
                    if offer_check.get('offer', {}).get('listingStartDate'):
                        has_start_date = True
                        break
            if has_start_date:
                print("✅ listingStartDate verified in offers")
            else:
                print("❌ listingStartDate NOT found in offers - scheduled draft may not work!")

if __name__ == "__main__":
    try:
        verify_draft_workflow()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
