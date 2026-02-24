"""
Final attempt to publish - wait longer and ensure description is everywhere.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def final_publish():
    """Final publish attempt."""
    print("=" * 80)
    print("Final Publish Attempt")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    description = "Test Listing - Please Delete. Select your card from the variations below. All cards are in Near Mint or better condition. Fast shipping guaranteed."
    
    print("Step 1: Update offer with description...")
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    listing_policies = {
        "paymentPolicyId": "53240392019",
        "fulfillmentPolicyId": "229316003019",
        "returnPolicyId": "12906640019"
    }
    
    # Update offer with description
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId'),
        "listing": {
            "title": "Test Listing - Please Delete",
            "description": description,
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
    
    print("Step 2: Update group with description...")
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
            "description": description
        },
        "variantSKUs": [sku]
    }
    
    group_response = client._make_request('PUT', f'/sell/inventory/v1/inventory_item_group/{group_key}', data=group_update)
    if group_response.status_code not in [200, 204]:
        print(f"[WARNING] Group update: {group_response.status_code}")
    else:
        print("[OK] Group updated")
    
    print()
    print("Step 3: Waiting 15 seconds for everything to propagate...")
    time.sleep(15)
    print()
    
    print("Step 4: Publishing...")
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
        print("This appears to be a persistent eBay API issue with description persistence.")
        print("The listing exists as a draft but can't be published due to description validation.")

if __name__ == "__main__":
    final_publish()
