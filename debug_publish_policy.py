"""
Debug script to check what policy is actually being used when publishing.
This will help diagnose why Error 25007 persists.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Debug Publish Policy Issue")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    print(f"1. Fulfillment Policy ID from config: {fulfillment_policy_id}")
    print()
    
    # Get the policy details
    print("2. Checking policy details...")
    policy_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
    
    if policy_response.status_code == 200:
        policy = policy_response.json()
        print(f"   Policy Name: {policy.get('name')}")
        print(f"   Marketplace: {policy.get('marketplaceId')}")
        
        shipping_options = policy.get('shippingOptions', [])
        print(f"   Shipping Options: {len(shipping_options)}")
        
        for i, option in enumerate(shipping_options, 1):
            services = option.get('shippingServices', [])
            print(f"     Option {i} ({option.get('optionType')}): {len(services)} service(s)")
            for service in services:
                print(f"       - {service.get('shippingServiceCode')} ({service.get('shippingCarrierCode')})")
                print(f"         Buyer Pays: {service.get('buyerResponsibleForShipping', False)}")
                print(f"         Cost: ${service.get('shippingCost', {}).get('value', 'N/A')}")
    else:
        print(f"   [ERROR] Could not get policy: {policy_response.status_code}")
        print(policy_response.text[:500])
        return
    
    print()
    print("3. Checking if there are any existing offers...")
    # Try to get a recent offer to see what policy it's using
    try:
        offers_response = client._make_request('GET', '/sell/inventory/v1/offer', params={'limit': 1})
        if offers_response.status_code == 200:
            offers_data = offers_response.json()
            offers = offers_data.get('offers', [])
            if offers:
                offer = offers[0]
                print(f"   Found offer: {offer.get('offerId', 'N/A')}")
                listing_policies = offer.get('listing', {}).get('listingPolicies', {})
                offer_policy_id = listing_policies.get('fulfillmentPolicyId', 'N/A')
                print(f"   Policy ID in offer: {offer_policy_id}")
                if offer_policy_id != fulfillment_policy_id:
                    print(f"   [WARNING] Policy mismatch! Offer uses {offer_policy_id}, config has {fulfillment_policy_id}")
            else:
                print("   No offers found")
        else:
            print(f"   Could not get offers: {offers_response.status_code}")
    except Exception as e:
        print(f"   Error checking offers: {e}")
    
    print()
    print("4. Possible causes of Error 25007:")
    print("   - Policy needs time to propagate (wait 5-10 minutes)")
    print("   - Shipping service code not valid for Trading Cards category")
    print("   - Policy validation happens differently during publish vs offer creation")
    print("   - Category-specific shipping requirements")
    print()
    print("5. Recommendations:")
    print("   a) Wait 5-10 minutes and try again (policy propagation)")
    print("   b) Try creating listing again (may be transient)")
    print("   c) Check if policy works in eBay Seller Hub manually")
    print("   d) Consider using a different shipping service code")

if __name__ == "__main__":
    main()
