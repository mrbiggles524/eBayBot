"""
Comprehensive test to create a listing and verify where it appears.
This will test multiple approaches to figure out why listings aren't appearing.
"""
import sys
from ebay_api_client import eBayAPIClient
from ebay_listing import eBayListingManager
from config import Config
from datetime import datetime, timedelta
import time
import json

sys.stdout.reconfigure(encoding='utf-8')

def test_approach_1_draft():
    """Test 1: Create as draft (publish=False)"""
    print("=" * 80)
    print("TEST 1: CREATE AS DRAFT (publish=False)")
    print("=" * 80)
    print()
    
    manager = eBayListingManager()
    
    test_cards = [
        {
            'name': 'Test Card A',
            'number': 'TEST-1',
            'quantity': 2,
            'team': '',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        },
        {
            'name': 'Test Card B',
            'number': 'TEST-2',
            'quantity': 3,
            'team': '',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        }
    ]
    
    # Create with a guaranteed valid description
    valid_description = """Test Listing for Draft Verification

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
    
    print("Creating draft listing...")
    print(f"  publish: False")
    print(f"  schedule_draft: False")
    print(f"  Description length: {len(valid_description)}")
    print()
    
    result = manager.create_variation_listing(
        cards=test_cards,
        title="TEST DRAFT - Please Delete",
        description=valid_description,
        category_id="261328",
        price=1.50,
        quantity=1,
        condition="Near Mint",
        images=['https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'],
        publish=False,
        schedule_draft=False
    )
    
    print()
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Group Key: {result.get('group_key')}")
    print(f"  Status: {result.get('status')}")
    print(f"  Message: {result.get('message')}")
    
    if result.get('success') and result.get('group_key'):
        group_key = result.get('group_key')
        print()
        print("Verifying group and offers...")
        verify_group_and_offers(group_key, "DRAFT")
        return group_key
    
    return None

def test_approach_2_scheduled_draft():
    """Test 2: Create as scheduled draft (publish=True, schedule_draft=True)"""
    print()
    print("=" * 80)
    print("TEST 2: CREATE AS SCHEDULED DRAFT (publish=True, schedule_draft=True)")
    print("=" * 80)
    print()
    
    manager = eBayListingManager()
    
    test_cards = [
        {
            'name': 'Test Card C',
            'number': 'TEST-3',
            'quantity': 2,
            'team': '',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        },
        {
            'name': 'Test Card D',
            'number': 'TEST-4',
            'quantity': 3,
            'team': '',
            'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
        }
    ]
    
    valid_description = """Test Scheduled Draft Listing

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
    
    print("Creating scheduled draft listing...")
    print(f"  publish: True")
    print(f"  schedule_draft: True")
    print(f"  schedule_hours: 48")
    print(f"  Description length: {len(valid_description)}")
    print()
    
    result = manager.create_variation_listing(
        cards=test_cards,
        title="TEST SCHEDULED DRAFT - Please Delete",
        description=valid_description,
        category_id="261328",
        price=1.75,
        quantity=1,
        condition="Near Mint",
        images=['https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'],
        publish=True,
        schedule_draft=True,
        schedule_hours=48
    )
    
    print()
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Group Key: {result.get('group_key')}")
    print(f"  Status: {result.get('status')}")
    print(f"  Scheduled: {result.get('scheduled')}")
    print(f"  Listing ID: {result.get('listing_id')}")
    print(f"  Message: {result.get('message')}")
    
    if result.get('success') and result.get('group_key'):
        group_key = result.get('group_key')
        print()
        print("Verifying group and offers...")
        verify_group_and_offers(group_key, "SCHEDULED DRAFT")
        return group_key
    
    return None

def verify_group_and_offers(group_key, test_type):
    """Verify group and offers, check where they appear."""
    print()
    print(f"VERIFYING {test_type} LISTING: {group_key}")
    print("-" * 80)
    
    client = eBayAPIClient()
    
    # Get group
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print(f"❌ Group not found: {group_result.get('error')}")
        return
    
    group_data = group_result.get('data', {})
    variant_skus = group_data.get('variantSKUs', [])
    print(f"✅ Group found")
    print(f"   Title: {group_data.get('title', 'N/A')}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print()
    
    # Check each offer
    print("Checking offers:")
    scheduled_count = 0
    active_count = 0
    draft_count = 0
    offers_with_listing_id = 0
    offers_with_start_date = 0
    
    for sku in variant_skus:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            offer_id = offer.get('offerId')
            listing_id = offer.get('listingId')
            start_date = offer.get('listingStartDate', '')
            status = offer.get('status', 'UNKNOWN')
            group_key_in_offer = offer.get('inventoryItemGroupKey', '')
            
            print(f"   SKU: {sku}")
            print(f"      Offer ID: {offer_id}")
            print(f"      Listing ID: {listing_id or 'None'}")
            print(f"      Status: {status}")
            print(f"      Group Key: {group_key_in_offer}")
            print(f"      listingStartDate: {start_date or 'None'}")
            
            if listing_id:
                offers_with_listing_id += 1
                if start_date:
                    offers_with_start_date += 1
                    try:
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                        if start_dt > now:
                            scheduled_count += 1
                            print(f"      ✅ SCHEDULED (goes live in {(start_dt - now).total_seconds() / 3600:.1f} hours)")
                        else:
                            active_count += 1
                            print(f"      ⚠️ ACTIVE (start date in past)")
                    except:
                        active_count += 1
                        print(f"      ⚠️ ACTIVE (could not parse date)")
                else:
                    active_count += 1
                    print(f"      ⚠️ ACTIVE (no start date)")
            else:
                draft_count += 1
                print(f"      ⚠️ DRAFT (no listing ID)")
        else:
            print(f"   ❌ Could not get offer: {offer_result.get('error')}")
        print()
    
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total Offers: {len(variant_skus)}")
    print(f"  - With Listing ID: {offers_with_listing_id}")
    print(f"  - With Start Date: {offers_with_start_date}")
    print(f"  - Scheduled: {scheduled_count}")
    print(f"  - Active: {active_count}")
    print(f"  - Draft: {draft_count}")
    print()
    
    if scheduled_count > 0:
        print("✅ SCHEDULED LISTINGS FOUND!")
        print("   Should appear in: https://www.ebay.com/sh/lst/scheduled")
    elif active_count > 0:
        print("⚠️ LISTINGS WENT ACTIVE")
        print("   Should appear in: https://www.ebay.com/sh/account/listings?status=ACTIVE")
    elif draft_count > 0:
        print("⚠️ LISTINGS ARE DRAFTS")
        print("   May appear in:")
        print("   - https://www.ebay.com/sh/account/listings?status=UNSOLD")
        print("   - https://www.ebay.com/sh/account/listings?status=ACTIVE")
        print("   - Or may not be visible (eBay API limitation)")
    else:
        print("❌ NO LISTINGS FOUND")
    
    print()
    print("WHERE TO CHECK:")
    print("  1. Scheduled: https://www.ebay.com/sh/lst/scheduled")
    print("  2. Active: https://www.ebay.com/sh/account/listings?status=ACTIVE")
    print("  3. Unsold: https://www.ebay.com/sh/account/listings?status=UNSOLD")
    print("  4. Drafts: https://www.ebay.com/sh/account/listings?status=DRAFT")
    print()
    print(f"Group Key: {group_key}")
    print("Search for this group key in Seller Hub to find the listing.")

def main():
    """Run comprehensive tests."""
    print("=" * 80)
    print("COMPREHENSIVE LISTING CREATION TEST")
    print("=" * 80)
    print()
    print("This script will test multiple approaches to create listings")
    print("and verify where they appear in Seller Hub.")
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"API URL: {config.ebay_api_url}")
    print()
    
    # Test 1: Draft
    group_key_1 = test_approach_1_draft()
    
    # Wait a bit
    print()
    print("Waiting 10 seconds before next test...")
    time.sleep(10)
    
    # Test 2: Scheduled Draft
    group_key_2 = test_approach_2_scheduled_draft()
    
    print()
    print("=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print()
    print("Group Keys Created:")
    if group_key_1:
        print(f"  Test 1 (Draft): {group_key_1}")
    if group_key_2:
        print(f"  Test 2 (Scheduled): {group_key_2}")
    print()
    print("Next Steps:")
    print("1. Wait 2-3 minutes for eBay to process")
    print("2. Check Seller Hub at the URLs shown above")
    print("3. Search for the group keys to find the listings")
    print("4. Report back what you find (or don't find)")

if __name__ == "__main__":
    main()
