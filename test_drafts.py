"""Test draft and scheduled draft creation."""
import sys
import os
from ebay_listing import eBayListingManager
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

def test_draft_creation():
    """Test creating a draft listing (unpublished)."""
    print("=" * 80)
    print("TEST 1: Creating DRAFT listing (unpublished)")
    print("=" * 80)
    
    manager = eBayListingManager()
    
    # Create a simple test listing with 2 cards
    test_cards = [
        {
            'name': 'Test Player 1',
            'number': '1',
            'quantity': 1,
            'team': 'Test Team',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        },
        {
            'name': 'Test Player 2',
            'number': '2',
            'quantity': 1,
            'team': 'Test Team',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        }
    ]
    
    result = manager.create_variation_listing(
        cards=test_cards,
        title="TEST DRAFT - Delete Me",
        description="<p><strong>Test Draft Listing</strong></p><p>This is a test draft. Please delete.</p>",
        category_id="261328",
        price=1.00,
        quantity=1,
        condition="Near Mint",
        images=None,
        publish=False,  # DRAFT - don't publish
        schedule_draft=False,
        schedule_hours=24
    )
    
    print(f"\nResult: {result.get('success')}")
    print(f"Group Key: {result.get('group_key') or result.get('groupKey')}")
    print(f"Cards Created: {result.get('cardsCreated', 0)}")
    print(f"Status: {result.get('status', 'unknown')}")
    
    if result.get('success'):
        group_key = result.get('group_key') or result.get('groupKey')
        if group_key:
            # Verify the group exists
            print(f"\n[VERIFY] Checking group: {group_key}")
            group_result = manager.api_client.get_inventory_item_group(group_key)
            if group_result.get('success'):
                print("✅ Group verified!")
                group_data = group_result.get('data', {})
                variant_skus = group_data.get('variantSKUs', [])
                print(f"   Variant SKUs: {len(variant_skus)}")
                
                # Check offers
                for sku in variant_skus[:3]:  # Check first 3
                    offer_result = manager.api_client.get_offer_by_sku(sku)
                    if offer_result.get('success'):
                        offer_data = offer_result.get('data', {})
                        offer_status = offer_data.get('listing', {}).get('listingStatus', 'UNKNOWN')
                        print(f"   SKU {sku}: Status = {offer_status}")
            else:
                print(f"❌ Group verification failed: {group_result.get('error')}")
    
    return result

def test_scheduled_draft():
    """Test creating a scheduled draft listing."""
    print("\n" + "=" * 80)
    print("TEST 2: Creating SCHEDULED DRAFT listing (published with future start date)")
    print("=" * 80)
    
    manager = eBayListingManager()
    
    # Create a simple test listing with 2 cards
    test_cards = [
        {
            'name': 'Scheduled Test Player 1',
            'number': '1',
            'quantity': 1,
            'team': 'Test Team',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        },
        {
            'name': 'Scheduled Test Player 2',
            'number': '2',
            'quantity': 1,
            'team': 'Test Team',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        }
    ]
    
    schedule_hours = 24
    result = manager.create_variation_listing(
        cards=test_cards,
        title="TEST SCHEDULED - Delete Me",
        description="<p><strong>Test Scheduled Listing</strong></p><p>This is a test scheduled listing. Please delete.</p>",
        category_id="261328",
        price=1.00,
        quantity=1,
        condition="Near Mint",
        images=None,
        publish=True,  # Must publish for scheduled
        schedule_draft=True,  # Schedule it
        schedule_hours=schedule_hours
    )
    
    print(f"\nResult: {result.get('success')}")
    print(f"Group Key: {result.get('group_key') or result.get('groupKey')}")
    print(f"Cards Created: {result.get('cardsCreated', 0)}")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Scheduled: {result.get('scheduled', False)}")
    
    if result.get('success'):
        group_key = result.get('group_key') or result.get('groupKey')
        if group_key:
            # Verify the group exists
            print(f"\n[VERIFY] Checking group: {group_key}")
            group_result = manager.api_client.get_inventory_item_group(group_key)
            if group_result.get('success'):
                print("✅ Group verified!")
                group_data = group_result.get('data', {})
                variant_skus = group_data.get('variantSKUs', [])
                print(f"   Variant SKUs: {len(variant_skus)}")
                
                # Check offers and their listingStartDate
                for sku in variant_skus[:3]:  # Check first 3
                    offer_result = manager.api_client.get_offer_by_sku(sku)
                    if offer_result.get('success'):
                        offer_data = offer_result.get('data', {})
                        offer_status = offer_data.get('listing', {}).get('listingStatus', 'UNKNOWN')
                        start_date = offer_data.get('listingStartDate')
                        print(f"   SKU {sku}:")
                        print(f"      Status = {offer_status}")
                        print(f"      Start Date = {start_date}")
                        
                        if start_date:
                            # Parse and show when it will go live
                            try:
                                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                                now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                                hours_until = (start_dt - now).total_seconds() / 3600
                                print(f"      Will go live in: {hours_until:.1f} hours")
                            except:
                                pass
            else:
                print(f"❌ Group verification failed: {group_result.get('error')}")
    
    return result

if __name__ == "__main__":
    print("Testing Draft and Scheduled Draft Creation")
    print("=" * 80)
    
    try:
        # Test 1: Regular draft
        draft_result = test_draft_creation()
        
        # Test 2: Scheduled draft
        scheduled_result = test_scheduled_draft()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Draft Test: {'✅ PASSED' if draft_result.get('success') else '❌ FAILED'}")
        print(f"Scheduled Draft Test: {'✅ PASSED' if scheduled_result.get('success') else '❌ FAILED'}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
