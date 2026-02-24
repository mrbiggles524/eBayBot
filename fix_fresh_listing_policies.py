"""
Fix the fresh listing's policies and publish.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def fix_and_publish():
    """Fix policies and publish."""
    print("=" * 80)
    print("Fixing Policies and Publishing Fresh Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    group_key = "GROUPSET1768713890"
    sku = "CARD_SET_FRESH_TEST_CARD_1_0"
    
    # Get valid policies
    print("Getting valid policies...")
    
    # Payment policy
    try:
        response = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            payment_policies = response.json().get('paymentPolicies', [])
            valid_payment = payment_policies[0].get('paymentPolicyId') if payment_policies else None
            print(f"  Payment: {valid_payment}")
        else:
            valid_payment = None
    except:
        valid_payment = None
    
    # Fulfillment policy
    try:
        response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            fulfillment_policies = response.json().get('fulfillmentPolicies', [])
            # Use one that sounds like it has shipping
            valid_fulfillment = None
            for policy in fulfillment_policies:
                name = policy.get('name', '').upper()
                if 'GROUND' in name or 'SHIPPING' in name or 'ADVANTAGE' in name:
                    valid_fulfillment = policy.get('fulfillmentPolicyId')
                    print(f"  Fulfillment: {valid_fulfillment} ({policy.get('name', 'N/A')})")
                    break
            if not valid_fulfillment and fulfillment_policies:
                valid_fulfillment = fulfillment_policies[0].get('fulfillmentPolicyId')
                print(f"  Fulfillment: {valid_fulfillment} ({fulfillment_policies[0].get('name', 'N/A')})")
        else:
            valid_fulfillment = None
    except:
        valid_fulfillment = None
    
    # Return policy
    try:
        response = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            return_policies = response.json().get('returnPolicies', [])
            valid_return = return_policies[0].get('returnPolicyId') if return_policies else None
            print(f"  Return: {valid_return}")
        else:
            valid_return = None
    except:
        valid_return = None
    
    if not valid_payment or not valid_fulfillment:
        print("[ERROR] Could not get valid policies")
        return
    
    print()
    print("Updating offer with valid policies...")
    
    # Get offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Update offer
    listing_policies = {
        "paymentPolicyId": valid_payment,
        "fulfillmentPolicyId": valid_fulfillment
    }
    
    if valid_return:
        listing_policies["returnPolicyId"] = valid_return
    
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId'),
        "listing": {
            "title": "Fresh Test Listing - Please Delete",
            "description": "Fresh Test Listing - Please Delete. Select your card from the variations below. All cards are in Near Mint or better condition.",
            "listingPolicies": listing_policies
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
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")
        return
    
    print("[OK] Offer updated")
    print()
    print("Waiting 5 seconds...")
    time.sleep(5)
    print()
    print("Publishing...")
    
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
        print("Check Seller Hub -> Listings -> Active")
        print()
    else:
        error = publish_result.get('error', 'Unknown error')
        print(f"[ERROR] Publish failed: {error}")

if __name__ == "__main__":
    fix_and_publish()
