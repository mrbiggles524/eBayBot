"""
Fix existing offers by adding the fulfillment policy ID.
This addresses the critical issue where offers don't have the policy ID set.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Fix Offers - Add Fulfillment Policy ID")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    payment_policy_id = config.PAYMENT_POLICY_ID
    return_policy_id = config.RETURN_POLICY_ID
    
    print(f"Fulfillment Policy ID: {fulfillment_policy_id}")
    print(f"Payment Policy ID: {payment_policy_id}")
    print(f"Return Policy ID: {return_policy_id}")
    print()
    
    if not fulfillment_policy_id:
        print("[ERROR] FULFILLMENT_POLICY_ID not set in .env")
        return
    
    # Get all offers - use marketplace_id parameter
    print("Fetching offers...")
    response = client._make_request('GET', '/sell/inventory/v1/offer', params={
        'marketplace_id': 'EBAY_US',
        'limit': 50
    })
    
    if response.status_code != 200:
        print(f"[ERROR] Could not get offers: {response.status_code}")
        print(response.text[:500])
        return
    
    offers_data = response.json()
    offers = offers_data.get('offers', [])
    
    print(f"Found {len(offers)} offer(s)")
    print()
    
    fixed_count = 0
    for offer in offers:
        offer_id = offer.get('offerId')
        sku = offer.get('sku', 'N/A')
        
        # Check if offer has policy ID
        listing_policies = offer.get('listing', {}).get('listingPolicies', {})
        current_policy_id = listing_policies.get('fulfillmentPolicyId')
        
        if current_policy_id:
            print(f"✅ Offer {offer_id} (SKU: {sku}) already has policy ID: {current_policy_id}")
            continue
        
        print(f"❌ Offer {offer_id} (SKU: {sku}) is missing policy ID")
        print(f"   Fixing...")
        
        # Get full offer structure
        offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
        if offer_response.status_code != 200:
            print(f"   [ERROR] Could not get offer details: {offer_response.status_code}")
            continue
        
        offer_data = offer_response.json()
        
        # Ensure listing structure exists
        if 'listing' not in offer_data:
            offer_data['listing'] = {}
        if 'listingPolicies' not in offer_data['listing']:
            offer_data['listing']['listingPolicies'] = {}
        
        # Set the policy IDs
        offer_data['listing']['listingPolicies']['fulfillmentPolicyId'] = fulfillment_policy_id
        if payment_policy_id:
            offer_data['listing']['listingPolicies']['paymentPolicyId'] = payment_policy_id
        if return_policy_id:
            offer_data['listing']['listingPolicies']['returnPolicyId'] = return_policy_id
        
        # Update the offer
        update_response = client._make_request('PUT', f'/sell/inventory/v1/offer/{offer_id}', data=offer_data)
        
        if update_response.status_code in [200, 204]:
            print(f"   ✅ Successfully updated offer with policy ID: {fulfillment_policy_id}")
            fixed_count += 1
        else:
            error_text = update_response.text
            print(f"   ❌ Failed to update: {update_response.status_code}")
            try:
                error_json = update_response.json()
                errors = error_json.get('errors', [])
                if errors:
                    print(f"      Error: {errors[0].get('message', 'Unknown')}")
            except:
                print(f"      Response: {error_text[:200]}")
        print()
    
    print("=" * 80)
    print(f"Fixed {fixed_count} offer(s)")
    print("=" * 80)
    print()
    if fixed_count > 0:
        print("Offers have been updated with the fulfillment policy ID.")
        print("Try creating a listing again - the offers should now have the policy set.")

if __name__ == "__main__":
    main()
