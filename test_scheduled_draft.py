"""
Test creating a scheduled draft to see what happens.
"""
import sys
from ebay_listing import eBayListingManager
from config import Config
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Force reload .env
load_dotenv(override=True)
config = Config()

print("=" * 80)
print("TESTING SCHEDULED DRAFT CREATION")
print("=" * 80)
print()
print(f"Environment: {config.EBAY_ENVIRONMENT}")
print(f"API URL: {config.ebay_api_url}")
print()

# Test data
test_cards = [
    {
        'name': 'Test Card 1',
        'number': 'BD-1',
        'quantity': 2,
        'team': '',
        'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
    },
    {
        'name': 'Test Card 2',
        'number': 'BD-2',
        'quantity': 2,
        'team': '',
        'image_url': 'https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'
    }
]

listing_manager = eBayListingManager()

print("Creating scheduled draft...")
print("  schedule_draft: True")
print("  publish: True (required for scheduled)")
print("  schedule_hours: 24")
print()

result = listing_manager.create_variation_listing(
    cards=test_cards,
    title="Test Scheduled Draft - Please Delete",
    description="<p><strong>Test Scheduled Draft</strong></p><p>This is a test. Please delete.</p>",
    category_id="261328",
    price=2.0,
    quantity=1,
    condition="Near Mint",
    images=['https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp'],
    publish=True,
    schedule_draft=True,
    schedule_hours=24
)

print()
print("=" * 80)
print("RESULT")
print("=" * 80)
print(f"Success: {result.get('success')}")
print(f"Error: {result.get('error')}")
print(f"Group Key: {result.get('group_key')}")
print(f"Listing ID: {result.get('listing_id')}")
print(f"Status: {result.get('status')}")
print(f"Scheduled: {result.get('scheduled')}")
print(f"Message: {result.get('message')}")
print()

if result.get('success'):
    group_key = result.get('group_key')
    if group_key:
        print("Verifying group and offers...")
        from ebay_api_client import eBayAPIClient
        client = eBayAPIClient()
        
        # Check group
        group_result = client.get_inventory_item_group(group_key)
        if group_result.get('success'):
            print(f"✅ Group exists: {group_key}")
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            print(f"   Variant SKUs: {len(variant_skus)}")
            
            # Check offers
            for sku in variant_skus:
                offer_result = client.get_offer_by_sku(sku)
                if offer_result.get('success'):
                    offer = offer_result.get('offer', {})
                    listing_id = offer.get('listingId')
                    start_date = offer.get('listingStartDate', '')
                    print(f"   {sku}:")
                    print(f"      Listing ID: {listing_id or 'None'}")
                    print(f"      listingStartDate: {start_date or '❌ MISSING'}")
        else:
            print(f"❌ Group not found: {group_result.get('error')}")
else:
    print(f"❌ Creation failed: {result.get('error')}")
