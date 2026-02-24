"""
Publish a complete single item with all required fields:
- Card Condition
- Image URL
- All aspects
"""
from ebay_api_client import eBayAPIClient
import sys
import time
import json
import uuid

sys.stdout.reconfigure(encoding='utf-8')

def create_and_publish():
    """Create and publish with all required fields."""
    client = eBayAPIClient()
    
    print("=" * 80)
    print("Creating Complete Single Item Listing")
    print("=" * 80)
    print()
    
    unique_id = str(uuid.uuid4())[:8].upper()
    sku = f"CARD_COMPLETE_{unique_id}"
    
    print(f"SKU: {sku}")
    print()
    
    # Step 1: Create inventory item with image
    print("Step 1: Creating inventory item with image...")
    
    # Use a placeholder image (you should replace with your actual card images)
    # This is a generic trading card placeholder
    image_url = "https://i.ebayimg.com/images/g/placeholder/s-l1600.jpg"
    
    item_data = {
        "sku": sku,
        "product": {
            "title": "Test Trading Card - Please Delete",
            "description": "<p>Test trading card listing created via API.</p><p>Please delete after testing.</p><p>This is a single item test with all required fields.</p>",
            "aspects": {
                "Card Name": ["Test Card"],
                "Card Number": ["1"],
                "Sport": ["Basketball"],
                "Card Manufacturer": ["Topps"],
                "Season": ["2024-25"],
                "Features": ["Base"],
                "Type": ["Sports Trading Card"],
                "Language": ["English"],
                "Original/Licensed Reprint": ["Original"]
            },
            "imageUrls": [
                "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"
            ]
        },
        "condition": "USED_VERY_GOOD",
        "conditionDescription": "Near Mint condition",
        "conditionDescriptors": [
            {
                "name": "40001",  # Card Condition
                "values": ["400010"]  # Near Mint or Better
            }
        ],
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "packageWeightAndSize": {
            "dimensions": {
                "width": 4.0,
                "length": 6.0,
                "height": 1.0,
                "unit": "INCH"
            },
            "weight": {
                "value": 0.19,
                "unit": "POUND"
            }
        }
    }
    
    item_result = client.create_inventory_item(sku, item_data)
    if not item_result.get('success'):
        print(f"[ERROR] Failed to create inventory item: {item_result.get('error')}")
        return
    print("[OK] Inventory item created with image")
    print()
    
    # Step 2: Get policies
    print("Step 2: Getting policies...")
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
    
    # Step 3: Create offer
    print("Step 3: Creating offer...")
    
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
        print(f"[OK] Offer created: {offer_id}")
    else:
        print(f"[ERROR] Offer creation failed: {response.status_code}")
        print(response.text)
        return
    print()
    
    # Step 4: Publish
    print("Step 4: Publishing...")
    print("[WARNING] This will make the listing LIVE on eBay!")
    print()
    
    response = client._make_request('POST', f'/sell/inventory/v1/offer/{offer_id}/publish')
    
    print(f"[DEBUG] Status: {response.status_code}")
    print(f"[DEBUG] Response: {response.text}")
    print()
    
    if response.status_code in [200, 201]:
        listing_id = response.json().get('listingId')
        print("=" * 80)
        print("[SUCCESS] LISTING PUBLISHED!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print(f"View: https://www.ebay.com/itm/{listing_id}")
        print()
        print("Check Seller Hub -> Listings -> Active")
        print()
        print("[IMPORTANT] Delete this test listing when done!")
        return {"success": True, "listing_id": listing_id, "sku": sku}
    else:
        errors = response.json().get('errors', []) if response.text else []
        print("=" * 80)
        print("[ERROR] Publish Failed")
        print("=" * 80)
        for error in errors:
            print(f"Error {error.get('errorId')}: {error.get('message')}")
        print()
        print(f"SKU: {sku}")
        print(f"Offer ID: {offer_id}")
        return {"success": False, "sku": sku, "offer_id": offer_id}


if __name__ == "__main__":
    create_and_publish()
