"""
Publish the listing without return policy (try removing it completely).
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def publish():
    """Publish without return policy."""
    print("=" * 80)
    print("Publishing Without Return Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Update offer - remove return policy completely
    listing_data = offer.get('listing', {})
    listing_policies = listing_data.get('listingPolicies', offer.get('listingPolicies', {}))
    
    # Remove return policy
    listing_policies.pop('returnPolicyId', None)
    
    # Ensure we have valid payment and fulfillment
    if 'paymentPolicyId' not in listing_policies:
        listing_policies['paymentPolicyId'] = '53240392019'
    if 'fulfillmentPolicyId' not in listing_policies:
        listing_policies['fulfillmentPolicyId'] = '229316003019'
    
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
    
    print("Updating offer (removing return policy)...")
    update_result = client.update_offer(offer_id, update_data)
    
    if update_result.get('success'):
        print("[OK] Offer updated")
        print()
        print("Updating group with description...")
        
        # Also update the group
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
            print("[OK] Group updated with description")
        else:
            print(f"[WARNING] Group update: {group_response.status_code}")
        
        print()
        print("Waiting 5 seconds...")
        time.sleep(5)
        print()
        print("Publishing...")
        
        # Try publishing the group
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
            print("The listing might need a return policy configured in Seller Hub.")
    else:
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")

if __name__ == "__main__":
    publish()
