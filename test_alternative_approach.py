"""
Test alternative approach: Create offers with listingStartDate, then create group, then publish.
This might work better than creating group first.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
from datetime import datetime, timedelta
import time
import json

sys.stdout.reconfigure(encoding='utf-8')

def test_alternative_approach():
    """Test creating offers first with listingStartDate, then group."""
    print("=" * 80)
    print("TESTING ALTERNATIVE APPROACH")
    print("=" * 80)
    print("Strategy: Create offers with listingStartDate FIRST, then group, then publish")
    print()
    
    client = eBayAPIClient()
    config = Config()
    
    # Test data
    test_cards = [
        {'name': 'Test Card E', 'number': 'TEST-5', 'price': 1.50, 'quantity': 2},
        {'name': 'Test Card F', 'number': 'TEST-6', 'price': 1.75, 'quantity': 3}
    ]
    
    # Calculate listingStartDate (48 hours from now)
    start_time = datetime.utcnow() + timedelta(hours=48)
    listing_start_date = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    print(f"Listing Start Date: {listing_start_date}")
    print(f"Will go live in: 48 hours")
    print()
    
    # Simple valid description
    valid_description = """Test Alternative Approach Listing

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options."""
    
    print(f"Description length: {len(valid_description)}")
    print()
    
    # Step 1: Create inventory items
    print("Step 1: Creating inventory items...")
    created_skus = []
    for card in test_cards:
        sku = f"CARD_SET_TEST_{card['name'].upper().replace(' ', '_')}_{card['number']}_0"
        created_skus.append(sku)
        
        item_data = {
            "sku": sku,
            "product": {
                "title": f"Test {card['name']}",
                "aspects": {
                    "Card Name": [card['name']]
                },
                "imageUrls": ["https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"]
            },
            "condition": "NEW_OTHER",
            "packageWeightAndSize": {
                "weight": {
                    "value": 1,
                    "unit": "OUNCE"
                },
                "dimensions": {
                    "length": 6,
                    "width": 4,
                    "height": 1,
                    "unit": "INCH"
                }
            }
        }
        
        result = client.create_or_replace_inventory_item(sku, item_data)
        if result.get('success'):
            print(f"  ✅ Created item: {sku}")
        else:
            print(f"  ❌ Failed: {result.get('error')}")
    
    print()
    time.sleep(2)
    
    # Step 2: Create offers WITH listingStartDate
    print("Step 2: Creating offers with listingStartDate...")
    offer_ids = []
    for i, card in enumerate(test_cards):
        sku = created_skus[i]
        
        offer_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "availableQuantity": card['quantity'],
            "pricingSummary": {
                "price": {
                    "value": str(card['price']),
                    "currency": "USD"
                }
            },
            "categoryId": "261328",
            "listingPolicies": {
                "fulfillmentPolicyId": "229316003019",
                "paymentPolicyId": "53240392019",
                "returnPolicyId": "243552423019"
            },
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc",
            "listingDuration": "GTC",
            "listing": {
                "title": f"Test {card['name']}",
                "description": valid_description,
                "itemSpecifics": {
                    "Card Name": [card['name']]
                }
            },
            "listingStartDate": listing_start_date  # CRITICAL: Set start date on offer
        }
        
        result = client.create_or_update_offer(offer_data)
        if result.get('success'):
            offer_id = result.get('data', {}).get('offerId')
            offer_ids.append((sku, offer_id))
            print(f"  ✅ Created offer: {sku} (ID: {offer_id})")
            print(f"     listingStartDate: {listing_start_date}")
        else:
            print(f"  ❌ Failed: {result.get('error')}")
    
    print()
    time.sleep(5)
    
    # Step 3: Create group
    print("Step 3: Creating inventory item group...")
    group_key = f"GROUPTEST{int(time.time())}"
    
    group_data = {
        "title": "TEST ALTERNATIVE APPROACH - Please Delete",
        "variesBy": {
            "specifications": [{
                "name": "PICK YOUR CARD",
                "values": [f"{card['number']} {card['name']}" for card in test_cards]
            }]
        },
        "inventoryItemGroup": {
            "aspects": {
                "Card Name": [card['name'] for card in test_cards]
            },
            "description": valid_description
        },
        "variantSKUs": created_skus
    }
    
    result = client.create_inventory_item_group(group_key, group_data)
    if result.get('success'):
        print(f"  ✅ Created group: {group_key}")
    else:
        print(f"  ❌ Failed: {result.get('error')}")
        return
    
    print()
    time.sleep(10)
    
    # Step 4: Link offers to group
    print("Step 4: Linking offers to group...")
    for sku, offer_id in offer_ids:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            current_group = offer.get('inventoryItemGroupKey')
            
            if current_group != group_key:
                update_data = {
                    "sku": sku,
                    "marketplaceId": "EBAY_US",
                    "format": "FIXED_PRICE",
                    "inventoryItemGroupKey": group_key,
                    "categoryId": offer.get('categoryId'),
                    "pricingSummary": offer.get('pricingSummary'),
                    "listingPolicies": offer.get('listingPolicies'),
                    "availableQuantity": offer.get('availableQuantity'),
                    "listingDuration": offer.get('listingDuration'),
                    "listingStartDate": listing_start_date  # Keep start date
                }
                
                if 'listing' in offer:
                    update_data['listing'] = offer['listing']
                
                update_result = client.update_offer(offer_id, update_data)
                if update_result.get('success'):
                    print(f"  ✅ Linked {sku} to group")
                else:
                    print(f"  ❌ Failed to link {sku}: {update_result.get('error')}")
            else:
                print(f"  ✅ {sku} already linked")
    
    print()
    time.sleep(5)
    
    # Step 5: Verify offers have listingStartDate
    print("Step 5: Verifying offers have listingStartDate...")
    all_have_start_date = True
    for sku, offer_id in offer_ids:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            start_date = offer.get('listingStartDate', '')
            if start_date:
                print(f"  ✅ {sku}: {start_date}")
            else:
                print(f"  ❌ {sku}: MISSING listingStartDate!")
                all_have_start_date = False
    
    if not all_have_start_date:
        print()
        print("⚠️ WARNING: Not all offers have listingStartDate!")
        print("This will cause the listing to go live immediately instead of scheduled.")
        return
    
    print()
    print("Step 6: Publishing group...")
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    print()
    print("PUBLISH RESULT:")
    print(f"  Success: {publish_result.get('success')}")
    if publish_result.get('success'):
        print("✅ PUBLISHED SUCCESSFULLY!")
        data = publish_result.get('data', {})
        listing_id = data.get('listingId')
        if listing_id:
            print(f"   Listing ID: {listing_id}")
        print()
        print("The listing should now be scheduled and visible in Seller Hub!")
        print("Check: https://www.ebay.com/sh/lst/scheduled")
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"❌ PUBLISH FAILED: {error}")
        print()
        print("Group Key:", group_key)
        print("You can try publishing it manually from Seller Hub.")

if __name__ == "__main__":
    test_alternative_approach()
