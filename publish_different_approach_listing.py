"""
Publish the different approach listing to see if it appears after publishing.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def publish_different():
    """Publish the different approach listing."""
    print("=" * 80)
    print("Publishing Different Approach Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    group_key = "GROUPSAHF8A3F381768715399"
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    
    print(f"Group Key: {group_key}")
    print(f"SKU: {sku}")
    print()
    
    # First, ensure offer has valid policies
    print("Step 1: Ensuring offer has valid policies...")
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Get valid policies
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
    except Exception as e:
        print(f"[ERROR] Could not get policies: {e}")
        return
    
    # Update offer with valid policies
    listing_policies = {
        "paymentPolicyId": valid_payment,
        "fulfillmentPolicyId": valid_fulfillment
    }
    if valid_return:
        listing_policies["returnPolicyId"] = valid_return
    
    title = "Different Approach Test - Please Delete"
    description = """Different Approach Test - Please Delete

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    item_specifics = {
        "Type": ["Sports Trading Card"],
        "Card Size": ["Standard"],
        "Country of Origin": ["United States"],
        "Language": ["English"],
        "Original/Licensed Reprint": ["Original"],
        "Card Name": ["Different Approach Test Card"],
        "Card Number": ["1"]
    }
    
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId', '261328'),
        "listing": {
            "title": title,
            "description": description,
            "listingPolicies": listing_policies,
            "itemSpecifics": item_specifics
        },
        "listingPolicies": listing_policies,
        "pricingSummary": offer.get('pricingSummary', {}),
        "quantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "listingDuration": offer.get('listingDuration', 'GTC'),
        "merchantLocationKey": offer.get('merchantLocationKey')
    }
    
    update_result = client.update_offer(offer_id, update_data)
    if not update_result.get('success'):
        print(f"[WARNING] Offer update: {update_result.get('error')}")
    else:
        print("[OK] Offer updated with valid policies")
    
    print()
    print("Step 2: Ensuring group has description...")
    
    # Update group one more time
    group_update = {
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
        "variantSKUs": [sku]
    }
    
    group_result = client.create_inventory_item_group(group_key, group_update)
    if group_result.get('success'):
        print("[OK] Group updated")
    else:
        print(f"[WARNING] Group update: {group_result.get('error')}")
    
    print()
    print("Step 3: Waiting 5 seconds...")
    time.sleep(5)
    print()
    
    print("Step 4: Publishing listing...")
    print("[WARNING] This will make the listing LIVE in production!")
    print()
    
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    if publish_result.get('success'):
        listing_id = publish_result.get('listing_id')
        print()
        print("=" * 80)
        print("[SUCCESS] Listing Published!")
        print("=" * 80)
        print()
        print(f"Listing ID: {listing_id}")
        print()
        print("View your listing:")
        print(f"  https://www.ebay.com/itm/{listing_id}")
        print()
        print("Check Seller Hub:")
        print("  - Go to: https://www.ebay.com/sh/landing")
        print("  - Navigate to: Listings -> Active")
        print("  - You should see: 'Different Approach Test - Please Delete'")
        print()
        print("[IMPORTANT] This listing is now LIVE and visible to buyers!")
        print("           Delete it from Seller Hub when done testing.")
        print()
    else:
        error = publish_result.get('error', 'Unknown error')
        print()
        print("=" * 80)
        print("[ERROR] Publish Failed")
        print("=" * 80)
        print(f"Error: {error}")
        print()
        print("The listing remains as a draft.")
        print("You can try publishing from Seller Hub UI if it appears there.")
        print()

if __name__ == "__main__":
    publish_different()
