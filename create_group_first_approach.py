"""
Different approach: Create group first, then create offer with explicit group reference.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time
import json

sys.stdout.reconfigure(encoding='utf-8')

def create_different_way():
    """Create listing using different approach."""
    print("=" * 80)
    print("Different Approach: Group First, Then Offer")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Step 1: Create inventory item first
    print("Step 1: Creating inventory item...")
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    
    inventory_item = {
        "product": {
            "categoryId": "261328",
            "aspects": {
                "Card Name": ["Different Approach Test Card"],
                "Card Number": ["1"]
            }
        },
        "condition": "USED_VERY_GOOD",
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        },
        "packageWeightAndSize": {
            "weight": {"value": "0.1875", "unit": "POUND"},
            "dimensions": {
                "length": "6", "width": "4", "height": "1", "unit": "INCH"
            }
        },
        "conditionDescriptors": [{
            "name": "40001",
            "values": ["400010"]
        }]
    }
    
    item_result = client._make_request('PUT', f'/sell/inventory/v1/inventory_item/{sku}', data=inventory_item)
    if item_result.status_code in [200, 204]:
        print(f"[OK] Inventory item created: {sku}")
    else:
        print(f"[ERROR] Failed to create item: {item_result.status_code}")
        return
    
    print()
    
    # Step 2: Create group FIRST
    print("Step 2: Creating inventory item group FIRST...")
    import random
    import string
    group_key = f"GROUP{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}{int(time.time())}"
    
    title = "Different Approach Test - Please Delete"
    description = """Different Approach Test - Please Delete

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    group_data = {
        "title": title,
        "variesBy": {
            "specifications": [{
                "name": "PICK YOUR CARD",
                "values": ["1 Different Approach Test Card"]
            }]
        },
        "inventoryItemGroup": {
            "aspects": {
                "Card Name": ["Different Approach Test Card"],
                "Card Number": ["1"]
            },
            "description": description
        },
        "variantSKUs": [sku]  # SKU that will be created
    }
    
    group_result = client.create_inventory_item_group(group_key, group_data)
    if not group_result.get('success'):
        print(f"[ERROR] Failed to create group: {group_result.get('error')}")
        return
    
    print(f"[OK] Group created: {group_key}")
    print()
    
    # Step 3: Wait a moment
    print("Step 3: Waiting 3 seconds for group to be ready...")
    time.sleep(3)
    print()
    
    # Step 4: Get valid policies
    print("Step 4: Getting valid policies...")
    try:
        response = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
        payment_policies = response.json().get('paymentPolicies', []) if response.status_code == 200 else []
        valid_payment = payment_policies[0].get('paymentPolicyId') if payment_policies else None
        
        response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        fulfillment_policies = response.json().get('fulfillmentPolicies', []) if response.status_code == 200 else []
        valid_fulfillment = None
        for policy in fulfillment_policies:
            name = policy.get('name', '').upper()
            if 'GROUND' in name or 'SHIPPING' in name or 'ADVANTAGE' in name:
                valid_fulfillment = policy.get('fulfillmentPolicyId')
                break
        if not valid_fulfillment and fulfillment_policies:
            valid_fulfillment = fulfillment_policies[0].get('fulfillmentPolicyId')
        
        response = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
        return_policies = response.json().get('returnPolicies', []) if response.status_code == 200 else []
        valid_return = return_policies[0].get('returnPolicyId') if return_policies else None
        
        print(f"  Payment: {valid_payment}")
        print(f"  Fulfillment: {valid_fulfillment}")
        print(f"  Return: {valid_return}")
        print()
    except Exception as e:
        print(f"[ERROR] Could not get policies: {e}")
        return
    
    # Step 5: Create offer WITH inventoryItemGroupKey explicitly
    print("Step 5: Creating offer WITH explicit inventoryItemGroupKey...")
    
    listing_policies = {
        "paymentPolicyId": valid_payment,
        "fulfillmentPolicyId": valid_fulfillment
    }
    if valid_return:
        listing_policies["returnPolicyId"] = valid_return
    
    item_specifics = {
        "Type": ["Sports Trading Card"],
        "Card Size": ["Standard"],
        "Country of Origin": ["United States"],
        "Language": ["English"],
        "Original/Licensed Reprint": ["Original"],
        "Card Name": ["Different Approach Test Card"],
        "Card Number": ["1"]
    }
    
    offer_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": "261328",
        "inventoryItemGroupKey": group_key,  # Try setting this explicitly
        "listing": {
            "title": title,
            "description": description,
            "listingPolicies": listing_policies,
            "itemSpecifics": item_specifics
        },
        "listingPolicies": listing_policies,
        "pricingSummary": {
            "price": {
                "value": "1.0",
                "currency": "USD"
            }
        },
        "quantity": 1,
        "availableQuantity": 1,
        "listingDuration": "GTC",
        "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc"
    }
    
    print(f"  Creating offer with inventoryItemGroupKey: {group_key}")
    create_result = client.create_offer(offer_data)
    
    if create_result.get('success'):
        offer_id = create_result.get('data', {}).get('offerId') or create_result.get('offerId')
        print(f"[OK] Offer created: {offer_id}")
    else:
        error = create_result.get('error', 'Unknown error')
        print(f"[ERROR] Failed to create offer: {error}")
        
        # If it fails because of inventoryItemGroupKey, try without it
        if "inventoryItemGroupKey" in str(error) or "group" in str(error).lower():
            print()
            print("Trying without explicit inventoryItemGroupKey...")
            offer_data.pop('inventoryItemGroupKey', None)
            create_result = client.create_offer(offer_data)
            if create_result.get('success'):
                offer_id = create_result.get('data', {}).get('offerId') or create_result.get('offerId')
                print(f"[OK] Offer created (without explicit group key): {offer_id}")
            else:
                print(f"[ERROR] Still failed: {create_result.get('error')}")
                return
        else:
            return
    
    print()
    print("Step 6: Waiting 5 seconds...")
    time.sleep(5)
    
    # Step 7: Verify the offer is linked
    print()
    print("Step 7: Verifying offer is linked to group...")
    verify_result = client.get_offer_by_sku(sku)
    if verify_result.get('success'):
        verify_offer = verify_result.get('offer', {})
        verify_group_key = verify_offer.get('inventoryItemGroupKey')
        print(f"  Offer ID: {verify_offer.get('offerId', 'N/A')}")
        print(f"  Status: {verify_offer.get('status', 'N/A')}")
        print(f"  inventoryItemGroupKey: {verify_group_key if verify_group_key else 'N/A (still missing)'}")
        
        if verify_group_key == group_key:
            print("  [SUCCESS] Offer is linked to group!")
        elif verify_group_key:
            print(f"  [WARNING] Different group key: {verify_group_key}")
        else:
            print("  [NOTE] Group key not in GET response (eBay API quirk)")
            print("         But offer should still be linked")
    
    print()
    print("=" * 80)
    print("Listing Created via Different Approach")
    print("=" * 80)
    print()
    print(f"Group Key: {group_key}")
    print(f"SKU: {sku}")
    print(f"Offer ID: {offer_id if 'offer_id' in locals() else 'N/A'}")
    print()
    print("Check Seller Hub:")
    print("  1. Go to: https://www.ebay.com/sh/landing")
    print("  2. Navigate to: Listings -> Drafts")
    print("  3. Look for: 'Different Approach Test - Please Delete'")
    print()
    print("Wait 1-2 minutes if it doesn't appear immediately.")
    print()

if __name__ == "__main__":
    create_different_way()
