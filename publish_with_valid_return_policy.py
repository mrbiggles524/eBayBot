"""
Publish with a valid return policy from the account.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def publish():
    """Publish with valid return policy."""
    print("=" * 80)
    print("Publishing With Valid Return Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    # Get valid return policy
    print("Getting valid return policy...")
    try:
        response = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
        if response.status_code == 200:
            data = response.json()
            return_policies = data.get('returnPolicies', [])
            if return_policies:
                valid_return_policy = return_policies[0].get('returnPolicyId')
                print(f"[OK] Using return policy: {valid_return_policy} ({return_policies[0].get('name', 'N/A')})")
            else:
                print("[ERROR] No return policies found")
                return
        else:
            print(f"[ERROR] {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Update offer with valid return policy
    listing_data = offer.get('listing', {})
    listing_policies = listing_data.get('listingPolicies', offer.get('listingPolicies', {}))
    
    # Set valid policies
    listing_policies['paymentPolicyId'] = '53240392019'
    listing_policies['fulfillmentPolicyId'] = '229316003019'
    listing_policies['returnPolicyId'] = valid_return_policy
    
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId'),
        "listing": {
            "title": "Test Listing - Please Delete",
            "description": "Test Listing - Please Delete. Select your card from the variations below. All cards are in Near Mint or better condition. Fast shipping guaranteed.",
            "listingPolicies": listing_policies
        },
        "listingPolicies": listing_policies,
        "pricingSummary": offer.get('pricingSummary', {}),
        "quantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "listingDuration": offer.get('listingDuration', 'GTC'),
        "merchantLocationKey": offer.get('merchantLocationKey')
    }
    
    print()
    print("Updating offer with valid policies...")
    update_result = client.update_offer(offer_id, update_data)
    
    if update_result.get('success'):
        print("[OK] Offer updated")
        print()
        print("Updating group with description...")
        
        # Update the group
        group_update = {
            "title": "Test Listing - Please Delete",
            "variesBy": {
                "specifications": [{
                    "name": "PICK YOUR CARD",
                    "values": ["1 Test Card"]
                }]
            },
            "inventoryItemGroup": {
                "aspects": {},
                "description": "Test Listing - Please Delete. Select your card from the variations below. All cards are in Near Mint or better condition. Fast shipping guaranteed."
            },
            "variantSKUs": [sku]
        }
        
        group_response = client._make_request('PUT', f'/sell/inventory/v1/inventory_item_group/{group_key}', data=group_update)
        if group_response.status_code in [200, 204]:
            print("[OK] Group updated")
        else:
            print(f"[WARNING] Group update: {group_response.status_code}")
        
        print()
        print("Waiting 7 seconds for propagation...")
        time.sleep(7)
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
    else:
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")

if __name__ == "__main__":
    publish()
