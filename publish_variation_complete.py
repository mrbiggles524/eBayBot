"""
Publish a VARIATION listing with all required fields.
Key learnings applied:
- Description at ROOT level of group
- Card Condition required
- Image URL required
- Use custom variation aspect (not predefined ones like Card Name)
"""
from ebay_api_client import eBayAPIClient
import sys
import time
import json
import uuid

sys.stdout.reconfigure(encoding='utf-8')

def create_and_publish_variation():
    """Create and publish a variation listing."""
    client = eBayAPIClient()
    
    print("=" * 80)
    print("Creating VARIATION Listing with All Required Fields")
    print("=" * 80)
    print()
    
    unique_id = str(uuid.uuid4())[:8].upper()
    group_key = f"VARGROUP_{unique_id}"
    
    # Create 3 card variations
    cards = [
        {"name": "LeBron James", "number": "1", "sku": f"VAR_{unique_id}_1"},
        {"name": "Stephen Curry", "number": "2", "sku": f"VAR_{unique_id}_2"},
        {"name": "Kevin Durant", "number": "3", "sku": f"VAR_{unique_id}_3"},
    ]
    
    print(f"Group Key: {group_key}")
    print(f"Cards: {len(cards)}")
    for card in cards:
        print(f"  - {card['number']} {card['name']} (SKU: {card['sku']})")
    print()
    
    # Step 1: Create inventory items for each card
    print("Step 1: Creating inventory items...")
    
    created_skus = []
    variation_values = []
    
    for card in cards:
        sku = card['sku']
        card_name = card['name']
        card_number = card['number']
        variation_value = f"{card_number} {card_name}"
        variation_values.append(variation_value)
        
        item_data = {
            "sku": sku,
            "product": {
                "title": f"{card_name} #{card_number} - Test Card",
                "description": f"<p>{card_name} #{card_number} trading card.</p><p>Test listing - please delete.</p>",
                "aspects": {
                    "Card Name": [card_name],
                    "Card Number": [card_number],
                    "Sport": ["Basketball"],
                    "Card Manufacturer": ["Topps"],
                    "Season": ["2024-25"],
                    "Features": ["Base"],
                    "Type": ["Sports Trading Card"],
                    "Language": ["English"],
                    "Original/Licensed Reprint": ["Original"],
                    # Add the variation aspect to the item
                    "Pick Your Card": [variation_value]
                },
                "imageUrls": [
                    "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"
                ]
            },
            "condition": "USED_VERY_GOOD",
            "conditionDescriptors": [
                {
                    "name": "40001",
                    "values": ["400010"]
                }
            ],
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": 1
                }
            },
            "packageWeightAndSize": {
                "dimensions": {"width": 4.0, "length": 6.0, "height": 1.0, "unit": "INCH"},
                "weight": {"value": 0.19, "unit": "POUND"}
            }
        }
        
        item_result = client.create_inventory_item(sku, item_data)
        if item_result.get('success'):
            created_skus.append(sku)
            print(f"  [OK] Created: {sku}")
        else:
            print(f"  [ERROR] Failed: {sku} - {item_result.get('error')}")
    
    if len(created_skus) < 2:
        print("[ERROR] Need at least 2 items for variation listing")
        return
    print()
    
    # Step 2: Create inventory item group with description at ROOT
    print("Step 2: Creating inventory item group...")
    print("[KEY] Description at ROOT level, custom variation aspect 'Pick Your Card'")
    print()
    
    group_data = {
        "title": "Test Variation Listing - Please Delete",
        "description": """<p><strong>Test Variation Listing - Please Delete</strong></p>
<p>This is a test variation listing created via the eBay Inventory API.</p>
<p>Select your card from the variations below. Each card is listed as a separate variation option.</p>
<p>All cards are in Near Mint or better condition unless otherwise noted.</p>
<p>Fast shipping and excellent customer service guaranteed!</p>""",
        "variantSKUs": created_skus,
        "variesBy": {
            "specifications": [
                {
                    "name": "Pick Your Card",
                    "values": variation_values
                }
            ]
        },
        "aspects": {
            "Sport": ["Basketball"],
            "Card Manufacturer": ["Topps"],
            "Season": ["2024-25"],
            "Type": ["Sports Trading Card"]
        },
        "imageUrls": [
            "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"
        ]
    }
    
    response = client._make_request(
        'PUT', 
        f'/sell/inventory/v1/inventory_item_group/{group_key}',
        data=group_data
    )
    
    if response.status_code in [200, 201, 204]:
        print(f"[OK] Group created (status: {response.status_code})")
    else:
        print(f"[ERROR] Group creation failed: {response.status_code}")
        print(response.text)
        return
    print()
    
    # Step 3: Get policies
    print("Step 3: Getting policies...")
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    payment_policy_id = resp.json().get('paymentPolicies', [{}])[0].get('paymentPolicyId') if resp.status_code == 200 else None
    
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    fulfillment_policies = resp.json().get('fulfillmentPolicies', []) if resp.status_code == 200 else []
    fulfillment_policy_id = None
    for policy in fulfillment_policies:
        if policy.get('shippingServices'):
            fulfillment_policy_id = policy.get('fulfillmentPolicyId')
            break
    if not fulfillment_policy_id and fulfillment_policies:
        fulfillment_policy_id = fulfillment_policies[0].get('fulfillmentPolicyId')
    
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    return_policy_id = resp.json().get('returnPolicies', [{}])[0].get('returnPolicyId') if resp.status_code == 200 else None
    
    print(f"  Payment: {payment_policy_id}")
    print(f"  Fulfillment: {fulfillment_policy_id}")
    print(f"  Return: {return_policy_id}")
    print()
    
    # Step 4: Create offers for each SKU
    print("Step 4: Creating offers...")
    
    offer_ids = []
    for sku in created_skus:
        offer_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingPolicies": {
                "paymentPolicyId": payment_policy_id,
                "fulfillmentPolicyId": fulfillment_policy_id,
                "returnPolicyId": return_policy_id
            },
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc",
            "categoryId": "261328",
            "pricingSummary": {
                "price": {
                    "value": "1.00",
                    "currency": "USD"
                }
            },
            "availableQuantity": 1,
            "listingDuration": "GTC"
        }
        
        response = client._make_request('POST', '/sell/inventory/v1/offer', data=offer_data)
        
        if response.status_code in [200, 201]:
            offer_id = response.json().get('offerId')
            offer_ids.append(offer_id)
            print(f"  [OK] Offer created for {sku}: {offer_id}")
        else:
            print(f"  [ERROR] Offer failed for {sku}: {response.status_code}")
            print(f"    {response.text}")
    
    if len(offer_ids) < 2:
        print("[ERROR] Need at least 2 offers for variation listing")
        return
    print()
    
    # Step 5: Wait for propagation
    print("Step 5: Waiting 5 seconds for propagation...")
    time.sleep(5)
    print()
    
    # Step 6: Publish variation listing
    print("Step 6: Publishing variation listing...")
    print("[WARNING] This will make the listing LIVE on eBay!")
    print()
    
    publish_data = {
        "inventoryItemGroupKey": group_key,
        "marketplaceId": "EBAY_US"
    }
    
    response = client._make_request(
        'POST',
        '/sell/inventory/v1/offer/publish_by_inventory_item_group',
        data=publish_data
    )
    
    print(f"[DEBUG] Status: {response.status_code}")
    print(f"[DEBUG] Response: {response.text}")
    print()
    
    if response.status_code in [200, 201]:
        listing_id = response.json().get('listingId')
        print("=" * 80)
        print("[SUCCESS] VARIATION LISTING PUBLISHED!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print(f"View: https://www.ebay.com/itm/{listing_id}")
        print()
        print("This listing has 3 variations (cards) in one listing!")
        print()
        print("Check Seller Hub -> Listings -> Active")
        print()
        print("[IMPORTANT] Delete this test listing when done!")
        return {"success": True, "listing_id": listing_id}
    else:
        errors = response.json().get('errors', []) if response.text else []
        print("=" * 80)
        print("[ERROR] Publish Failed")
        print("=" * 80)
        for error in errors:
            print(f"Error {error.get('errorId')}: {error.get('message')}")
        print()
        print(f"Group Key: {group_key}")
        return {"success": False}


if __name__ == "__main__":
    create_and_publish_variation()
