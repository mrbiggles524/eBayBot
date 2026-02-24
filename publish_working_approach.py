"""
Try the EXACT structure from eBay's working examples.
Key difference: description at ROOT level of group, not inside inventoryItemGroup.
"""
from ebay_api_client import eBayAPIClient
import sys
import time
import json
import uuid

sys.stdout.reconfigure(encoding='utf-8')

def create_and_publish():
    """Create a fresh listing with the exact eBay-documented structure."""
    client = eBayAPIClient()
    
    print("=" * 80)
    print("Creating Listing with EXACT eBay Structure")
    print("=" * 80)
    print()
    
    # Generate unique identifiers
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8].upper()
    sku = f"TEST_CARD_{unique_id}"
    group_key = f"GROUP_{unique_id}"
    
    print(f"SKU: {sku}")
    print(f"Group Key: {group_key}")
    print()
    
    # Step 1: Create inventory item with description in PRODUCT
    print("Step 1: Creating inventory item...")
    
    item_data = {
        "sku": sku,
        "product": {
            "title": "Test Card - Please Delete",
            "description": "Test card listing created via API. Please delete after testing.",
            "aspects": {
                "Card Name": ["Test Card"],
                "Card Number": ["1"]
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
    
    # Step 2: Create inventory item group with description at ROOT level
    print("Step 2: Creating inventory item group...")
    print("[KEY] Using description at ROOT level (not inside inventoryItemGroup)")
    print()
    
    # This is the KEY difference - description at ROOT, not nested
    group_data = {
        "title": "Test Card Listing - Please Delete",
        "description": """<p>Test Card Listing - Please Delete</p>
<p>This is a test listing created via the eBay Inventory API.</p>
<p>Select your card from the variations below. Each card is listed as a separate variation option.</p>
<p>All cards are in Near Mint or better condition unless otherwise noted.</p>""",
        "variantSKUs": [sku],
        "variesBy": {
            "specifications": [
                {
                    "name": "Card Name",
                    "values": ["Test Card"]
                }
            ]
        },
        "aspects": {
            "Card Name": ["Test Card"],
            "Card Number": ["1"]
        }
    }
    
    # Make direct API call to ensure exact structure
    print("[DEBUG] Sending group data:")
    print(json.dumps(group_data, indent=2))
    print()
    
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
    
    # Step 3: Get valid policies
    print("Step 3: Getting valid policies...")
    
    try:
        # Payment policy
        resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
        payment_policies = resp.json().get('paymentPolicies', []) if resp.status_code == 200 else []
        payment_policy_id = payment_policies[0].get('paymentPolicyId') if payment_policies else None
        
        # Fulfillment policy
        resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        fulfillment_policies = resp.json().get('fulfillmentPolicies', []) if resp.status_code == 200 else []
        fulfillment_policy_id = None
        for policy in fulfillment_policies:
            if policy.get('shippingServices'):
                fulfillment_policy_id = policy.get('fulfillmentPolicyId')
                break
        if not fulfillment_policy_id and fulfillment_policies:
            fulfillment_policy_id = fulfillment_policies[0].get('fulfillmentPolicyId')
        
        # Return policy
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
    
    # Step 4: Create offer
    print("Step 4: Creating offer...")
    
    # Get merchant location key
    location_key = None
    try:
        resp = client._make_request('GET', '/sell/inventory/v1/location')
        if resp.status_code == 200:
            locations = resp.json().get('locations', [])
            if locations:
                location_key = locations[0].get('merchantLocationKey')
    except:
        pass
    
    if not location_key:
        location_key = "046afc77-1256-4755-9dae-ab4ebe56c8cc"  # Fallback
    
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
    
    print("[DEBUG] Sending offer data:")
    print(json.dumps(offer_data, indent=2))
    print()
    
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
    
    # Step 5: Wait for propagation
    print("Step 5: Waiting 10 seconds for data propagation...")
    time.sleep(10)
    print()
    
    # Step 6: Publish
    print("Step 6: Publishing listing...")
    print("[WARNING] This will make the listing LIVE on eBay!")
    print()
    
    publish_data = {
        "inventoryItemGroupKey": group_key,
        "marketplaceId": "EBAY_US"
    }
    
    print("[DEBUG] Sending publish request:")
    print(json.dumps(publish_data, indent=2))
    print()
    
    response = client._make_request(
        'POST',
        '/sell/inventory/v1/offer/publish_by_inventory_item_group',
        data=publish_data
    )
    
    print(f"[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Response body: {response.text}")
    print()
    
    if response.status_code in [200, 201]:
        result = response.json()
        listing_id = result.get('listingId')
        print("=" * 80)
        print("[SUCCESS] LISTING PUBLISHED!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print(f"View: https://www.ebay.com/itm/{listing_id}")
        print()
        print("Go to Seller Hub -> Listings -> Active to see your listing!")
        print()
        print("[IMPORTANT] Delete this test listing when done!")
        print()
        return {"success": True, "listing_id": listing_id}
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
        print(f"Group Key: {group_key}")
        print(f"SKU: {sku}")
        print()
        
        return {"success": False, "error": errors}


if __name__ == "__main__":
    create_and_publish()
