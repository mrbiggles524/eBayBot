"""
Fix the fulfillment policy issue and publish the listing.
Error 25007 means the fulfillment policy needs shipping services.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def fix_and_publish():
    """Fix policy issue and publish."""
    print("=" * 80)
    print("Fixing Fulfillment Policy and Publishing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    print(f"SKU: {sku}")
    print(f"Group Key: {group_key}")
    print()
    
    # Get the offer
    print("Getting offer details...")
    offer_result = client.get_offer_by_sku(sku)
    
    if not offer_result.get('success') or not offer_result.get('offer'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    print(f"[OK] Offer ID: {offer_id}")
    print()
    
    # The issue is Error 25007 - fulfillment policy needs shipping services
    # We need to check if we can get a valid policy or update the offer
    
    print("Error 25007 means the fulfillment policy is missing shipping services.")
    print()
    print("Options:")
    print("  1. The policy ID might be wrong")
    print("  2. The policy might not have shipping services configured")
    print("  3. We might need to use a different policy")
    print()
    
    # Try to get all policies to find a valid one
    print("Trying to find a valid fulfillment policy...")
    try:
        # Try Account API to get policies
        response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        
        if response.status_code == 200:
            data = response.json()
            policies = data.get('fulfillmentPolicies', [])
            
            if policies:
                print(f"[OK] Found {len(policies)} fulfillment policy/policies")
                print()
                
                # Find one with shipping services
                valid_policy = None
                for policy in policies:
                    shipping_services = policy.get('shippingServices', [])
                    if shipping_services:
                        valid_policy = policy
                        break
                
                if valid_policy:
                    policy_id = valid_policy.get('fulfillmentPolicyId')
                    print(f"[OK] Found valid policy: {policy_id}")
                    print(f"     Name: {valid_policy.get('name', 'N/A')}")
                    print(f"     Shipping Services: {len(valid_policy.get('shippingServices', []))}")
                    print()
                    
                    # Update the offer with the valid policy
                    print("Updating offer with valid fulfillment policy...")
                    
                    listing_data = offer.get('listing', {})
                    listing_policies = listing_data.get('listingPolicies', offer.get('listingPolicies', {}))
                    
                    # Update with valid policy
                    listing_policies['fulfillmentPolicyId'] = policy_id
                    
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
                        print("[OK] Offer updated with valid policy")
                        print()
                        print("Now trying to publish...")
                        print()
                        
                        # Wait a moment
                        import time
                        time.sleep(3)
                        
                        # Publish
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
                            error = publish_result.get('error', 'Unknown error')
                            print(f"[ERROR] Publish failed: {error}")
                    else:
                        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")
                else:
                    print("[ERROR] No policies with shipping services found")
                    print()
                    print("You need to:")
                    print("  1. Go to eBay Seller Hub -> Business Policies")
                    print("  2. Edit your fulfillment policy")
                    print("  3. Add at least one shipping service")
                    print("  4. Then try publishing again")
            else:
                print("[ERROR] No fulfillment policies found")
                print("You need to create a fulfillment policy in Seller Hub first.")
        else:
            print(f"[ERROR] Could not get policies: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_and_publish()
