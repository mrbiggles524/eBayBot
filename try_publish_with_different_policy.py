"""
Try publishing with a different fulfillment policy.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def try_publish():
    """Try publishing with different policy."""
    print("=" * 80)
    print("Trying to Publish with Different Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    # Try using a policy that sounds like it has shipping
    # "Ground Advantage + $2 Handling" sounds like it should have shipping
    test_policy_id = "247148925019"
    
    print(f"SKU: {sku}")
    print(f"Group Key: {group_key}")
    print(f"Trying Policy ID: {test_policy_id} (Ground Advantage + $2 Handling)")
    print()
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    # Update offer with different policy
    print("Updating offer with different fulfillment policy...")
    
    listing_data = offer.get('listing', {})
    listing_policies = listing_data.get('listingPolicies', offer.get('listingPolicies', {}))
    
    # Update with test policy
    listing_policies['fulfillmentPolicyId'] = test_policy_id
    
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId'),
        "listing": {
            "title": listing_data.get('title', 'Test Listing - Please Delete'),
            "description": listing_data.get('description', 'Test listing description'),
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
        print("Waiting 3 seconds for propagation...")
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
            print("The fulfillment policy still needs shipping services configured.")
            print("Go to Seller Hub -> Business Policies and add shipping to your policy.")
    else:
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")

if __name__ == "__main__":
    try_publish()
