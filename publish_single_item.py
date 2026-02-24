"""
Try publishing as a SINGLE item (non-variation) first to verify the flow works.
Then we can figure out variation specifics.
"""
from ebay_api_client import eBayAPIClient
import sys
import time
import json
import uuid

sys.stdout.reconfigure(encoding='utf-8')

def create_and_publish_single():
    """Create and publish a single item listing (not variation)."""
    client = eBayAPIClient()
    
    print("=" * 80)
    print("Creating SINGLE Item Listing (Non-Variation)")
    print("=" * 80)
    print()
    
    # Generate unique identifiers
    unique_id = str(uuid.uuid4())[:8].upper()
    sku = f"SINGLE_TEST_{unique_id}"
    
    print(f"SKU: {sku}")
    print()
    
    # Step 1: Create inventory item
    print("Step 1: Creating inventory item...")
    
    item_data = {
        "sku": sku,
        "product": {
            "title": "Test Trading Card - Please Delete",
            "description": "Test trading card listing created via API. Please delete after testing. This is a single item test.",
            "aspects": {
                "Card Name": ["Test Card"],
                "Card Number": ["1"],
                "Sport": ["Basketball"],
                "Card Manufacturer": ["Topps"]
            }
        },
        "condition": "USED_VERY_GOOD",
        "conditionDescription": "Near Mint condition",
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
    print("[OK] Inventory item created")
    print()
    
    # Step 2: Get valid policies
    print("Step 2: Getting valid policies...")
    
    try:
        resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
        payment_policies = resp.json().get('paymentPolicies', []) if resp.status_code == 200 else []
        payment_policy_id = payment_policies[0].get('paymentPolicyId') if payment_policies else None
        
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
        return_policies = resp.json().get('returnPolicies', []) if resp.status_code == 200 else []
        return_policy_id = return_policies[0].get('returnPolicyId') if return_policies else None
        
        print(f"  Payment Policy: {payment_policy_id}")
        print(f"  Fulfillment Policy: {fulfillment_policy_id}")
        print(f"  Return Policy: {return_policy_id}")
    except Exception as e:
        print(f"[ERROR] Failed to get policies: {e}")
        return
    print()
    
    # Step 3: Create offer (single item, no group)
    print("Step 3: Creating offer (single item)...")
    
    location_key = "046afc77-1256-4755-9dae-ab4ebe56c8cc"
    
    offer_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "listingPolicies": {
            "paymentPolicyId": payment_policy_id,
            "fulfillmentPolicyId": fulfillment_policy_id,
            "returnPolicyId": return_policy_id
        },
        "merchantLocationKey": location_key,
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
        offer_response = response.json()
        offer_id = offer_response.get('offerId')
        print(f"[OK] Offer created: {offer_id}")
    else:
        print(f"[ERROR] Offer creation failed: {response.status_code}")
        print(response.text)
        return
    print()
    
    # Step 4: Publish single offer (not group)
    print("Step 4: Publishing single offer...")
    print("[WARNING] This will make the listing LIVE on eBay!")
    print()
    
    # For single items, use publishOffer endpoint
    response = client._make_request(
        'POST',
        f'/sell/inventory/v1/offer/{offer_id}/publish'
    )
    
    print(f"[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Response body: {response.text}")
    print()
    
    if response.status_code in [200, 201]:
        result = response.json()
        listing_id = result.get('listingId')
        print("=" * 80)
        print("[SUCCESS] SINGLE ITEM LISTING PUBLISHED!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print(f"View: https://www.ebay.com/itm/{listing_id}")
        print()
        print("Go to Seller Hub -> Listings -> Active to see your listing!")
        print()
        print("[IMPORTANT] Delete this test listing when done!")
        print()
        return {"success": True, "listing_id": listing_id, "sku": sku}
    else:
        error_data = response.json() if response.text else {}
        errors = error_data.get('errors', [])
        
        print("=" * 80)
        print("[ERROR] Publish Failed")
        print("=" * 80)
        print()
        
        for error in errors:
            error_id = error.get('errorId')
            message = error.get('message')
            print(f"Error {error_id}: {message}")
        
        print()
        print(f"SKU: {sku}")
        print(f"Offer ID: {offer_id}")
        print()
        
        return {"success": False, "error": errors, "sku": sku, "offer_id": offer_id}


if __name__ == "__main__":
    create_and_publish_single()
