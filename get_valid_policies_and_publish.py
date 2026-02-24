"""
Get valid policies and publish the listing.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def get_and_publish():
    """Get valid policies and publish."""
    print("=" * 80)
    print("Getting Valid Policies and Publishing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    # Get valid policies
    print("Getting valid policies...")
    print()
    
    # Get payment policies
    print("Payment Policies:")
    try:
        response = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            data = response.json()
            payment_policies = data.get('paymentPolicies', [])
            if payment_policies:
                valid_payment_policy = payment_policies[0].get('paymentPolicyId')
                print(f"  [OK] Using: {valid_payment_policy} ({payment_policies[0].get('name', 'N/A')})")
            else:
                print("  [ERROR] No payment policies found")
                return
        else:
            print(f"  [ERROR] {response.status_code}")
            return
    except Exception as e:
        print(f"  [ERROR] {e}")
        return
    
    # Get fulfillment policies
    print()
    print("Fulfillment Policies:")
    try:
        response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            data = response.json()
            fulfillment_policies = data.get('fulfillmentPolicies', [])
            if fulfillment_policies:
                # Try to find one that sounds like it has shipping
                valid_fulfillment_policy = None
                for policy in fulfillment_policies:
                    name = policy.get('name', '').upper()
                    if 'GROUND' in name or 'SHIPPING' in name or 'ADVANTAGE' in name:
                        valid_fulfillment_policy = policy.get('fulfillmentPolicyId')
                        print(f"  [OK] Using: {valid_fulfillment_policy} ({policy.get('name', 'N/A')})")
                        break
                
                if not valid_fulfillment_policy:
                    valid_fulfillment_policy = fulfillment_policies[0].get('fulfillmentPolicyId')
                    print(f"  [OK] Using: {valid_fulfillment_policy} ({fulfillment_policies[0].get('name', 'N/A')})")
            else:
                print("  [ERROR] No fulfillment policies found")
                return
        else:
            print(f"  [ERROR] {response.status_code}")
            return
    except Exception as e:
        print(f"  [ERROR] {e}")
        return
    
    # Get return policies
    print()
    print("Return Policies:")
    try:
        response = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            data = response.json()
            return_policies = data.get('returnPolicies', [])
            if return_policies:
                valid_return_policy = return_policies[0].get('returnPolicyId')
                print(f"  [OK] Using: {valid_return_policy} ({return_policies[0].get('name', 'N/A')})")
            else:
                print("  [WARNING] No return policies found (may be optional)")
                valid_return_policy = None
        else:
            print(f"  [WARNING] {response.status_code} - return policy may be optional")
            valid_return_policy = None
    except Exception as e:
        print(f"  [WARNING] {e} - return policy may be optional")
        valid_return_policy = None
    
    print()
    print("=" * 80)
    print("Updating Offer with Valid Policies")
    print("=" * 80)
    print()
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Update offer with valid policies
    listing_data = offer.get('listing', {})
    
    listing_policies = {
        "fulfillmentPolicyId": valid_fulfillment_policy,
        "paymentPolicyId": valid_payment_policy
    }
    
    if valid_return_policy:
        listing_policies["returnPolicyId"] = valid_return_policy
    
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId'),
        "listing": {
            "title": "Test Listing - Please Delete",
            "description": "Test Listing - Please Delete. Select your card from the variations below. All cards are in Near Mint or better condition.",
            "listingPolicies": listing_policies
        },
        "listingPolicies": listing_policies,
        "pricingSummary": offer.get('pricingSummary', {}),
        "quantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "listingDuration": offer.get('listingDuration', 'GTC'),
        "merchantLocationKey": offer.get('merchantLocationKey')
    }
    
    print("Updating offer...")
    update_result = client.update_offer(offer_id, update_data)
    
    if update_result.get('success'):
        print("[OK] Offer updated with valid policies")
        print()
        print("Waiting 3 seconds...")
        time.sleep(3)
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
            print()
            print("This might be a policy configuration issue.")
            print("Check your Business Policies in Seller Hub.")
    else:
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")

if __name__ == "__main__":
    get_and_publish()
