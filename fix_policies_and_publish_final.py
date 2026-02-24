"""Fix policies and publish final listing."""
from ebay_api_client import eBayAPIClient
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

group_key = "GROUPSET1768714571"
sku = "CARD_SET_FINAL_TEST_CARD_1_0"
client = eBayAPIClient()

print("Getting valid policies...")
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
    
    print("Updating offer with valid policies...")
    offer_result = client.get_offer_by_sku(sku)
    if offer_result.get('success'):
        offer = offer_result['offer']
        offer_id = offer.get('offerId')
        
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
                "title": "Final Test Listing - Please Delete",
                "description": "Final Test Listing - Please Delete. Select your card from the variations below. All cards are in Near Mint or better condition.",
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
        if update_result.get('success'):
            print("[OK] Offer updated")
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
                print(f"View: https://www.ebay.com/itm/{listing_id}")
                print()
            else:
                error = publish_result.get('error', 'Unknown')
                print(f"\n[FAILED] {error}")
                print("\nListing saved as draft.")
        else:
            print(f"[ERROR] Failed to update offer: {update_result.get('error')}")
    else:
        print("[ERROR] Could not get offer")
except Exception as e:
    print(f"[ERROR] {e}")
