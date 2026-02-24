"""
Fix specific offers that are missing the fulfillment policy ID.
Uses the SKUs from the error message.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Fix Specific Offers - Add Fulfillment Policy ID")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    payment_policy_id = config.PAYMENT_POLICY_ID
    return_policy_id = config.RETURN_POLICY_ID
    
    print(f"Fulfillment Policy ID: {fulfillment_policy_id}")
    print()
    
    # SKUs from the error message
    skus_to_fix = [
        "CARD_BECKETT_COM_NEWS_202_PASCAL_SIAKAM_1_0",
        "CARD_BECKETT_COM_NEWS_202_TOBIAS_HARRIS_6_1"
    ]
    
    for sku in skus_to_fix:
        print(f"Processing SKU: {sku}")
        
        # Get offer by SKU
        offer_result = client.get_offer_by_sku(sku)
        
        if not offer_result.get('success'):
            print(f"  [ERROR] Could not get offer for SKU: {offer_result.get('error', 'Unknown')}")
            continue
        
        offer = offer_result.get('offer')
        if not offer:
            print(f"  [ERROR] No offer found for SKU")
            continue
        
        offer_id = offer.get('offerId')
        print(f"  Offer ID: {offer_id}")
        
        # Check current policy ID
        listing_policies = offer.get('listing', {}).get('listingPolicies', {})
        current_policy_id = listing_policies.get('fulfillmentPolicyId')
        
        if current_policy_id:
            print(f"  [OK] Already has policy ID: {current_policy_id}")
            continue
        
        print(f"  [WARNING] Missing policy ID - fixing...")
        
        # Get full offer for update
        offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
        if offer_response.status_code != 200:
            print(f"  [ERROR] Could not get full offer: {offer_response.status_code}")
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
        
        print(f"  Updating offer with policy ID: {fulfillment_policy_id}...")
        
        # Update the offer
        update_response = client._make_request('PUT', f'/sell/inventory/v1/offer/{offer_id}', data=offer_data)
        
        if update_response.status_code in [200, 204]:
            print(f"  [OK] Successfully updated!")
            
            # Verify
            verify_result = client.get_offer_by_sku(sku)
            if verify_result.get('success') and verify_result.get('offer'):
                verified_policy_id = verify_result['offer'].get('listing', {}).get('listingPolicies', {}).get('fulfillmentPolicyId')
                if verified_policy_id:
                    print(f"  [OK] Verified: Policy ID is now {verified_policy_id}")
                else:
                    print(f"  [WARNING] Policy ID still missing after update")
        else:
            error_text = update_response.text
            print(f"  [ERROR] Failed to update: {update_response.status_code}")
            try:
                error_json = update_response.json()
                errors = error_json.get('errors', [])
                if errors:
                    print(f"     Error: {errors[0].get('message', 'Unknown')}")
            except:
                print(f"     Response: {error_text[:200]}")
        
        print()
    
    print("=" * 80)
    print("Done!")
    print("=" * 80)

if __name__ == "__main__":
    main()
