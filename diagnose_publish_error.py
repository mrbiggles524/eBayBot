"""
Diagnose why publishing fails with error 25007.
Check if policies are loaded correctly and if there's a timing issue.
"""
from ebay_api_client import eBayAPIClient
from config import Config
from ebay_listing import eBayListingManager
import json

def main():
    print("=" * 80)
    print("Diagnose Publish Error 25007")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print("1. Checking configuration...")
    print(f"   FULFILLMENT_POLICY_ID from config: {config.FULFILLMENT_POLICY_ID}")
    print()
    
    print("2. Checking policies loaded by API client...")
    policies = client.get_policy_ids()
    print(f"   Fulfillment Policy ID: {policies.get('fulfillment_policy_id')}")
    print(f"   Payment Policy ID: {policies.get('payment_policy_id')}")
    print(f"   Return Policy ID: {policies.get('return_policy_id')}")
    print(f"   Merchant Location: {policies.get('merchant_location_key')}")
    print()
    
    if policies.get('fulfillment_policy_id') != config.FULFILLMENT_POLICY_ID:
        print("[WARNING] Policy ID mismatch!")
        print(f"   Config says: {config.FULFILLMENT_POLICY_ID}")
        print(f"   API client loaded: {policies.get('fulfillment_policy_id')}")
        print()
        print("   This could be the issue - the listing manager might be using")
        print("   a cached policy ID that's different from your .env file.")
        print()
        print("   Solution: Restart the Streamlit app to reload policies.")
    else:
        print("[OK] Policy IDs match")
    print()
    
    print("3. Verifying fulfillment policy details...")
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    policy_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
    
    if policy_response.status_code == 200:
        policy = policy_response.json()
        shipping_options = policy.get('shippingOptions', [])
        print(f"   Policy Name: {policy.get('name')}")
        print(f"   Marketplace: {policy.get('marketplaceId')}")
        print(f"   Shipping Options: {len(shipping_options)}")
        
        for i, option in enumerate(shipping_options, 1):
            services = option.get('shippingServices', [])
            print(f"     Option {i} ({option.get('optionType')}): {len(services)} service(s)")
            for service in services:
                print(f"       - {service.get('shippingServiceCode')} ({service.get('shippingCarrierCode')})")
                print(f"         Cost: ${service.get('shippingCost', {}).get('value', 'N/A')}")
                print(f"         Buyer Pays: {service.get('buyerResponsibleForShipping', False)}")
        
        print()
        print("[OK] Policy has shipping services configured")
    else:
        print(f"[ERROR] Could not get policy: {policy_response.status_code}")
        print(policy_response.text[:500])
        return
    
    print("4. Checking listing manager's cached policies...")
    listing_manager = eBayListingManager()
    manager_policies = listing_manager.policies
    print(f"   Listing Manager Fulfillment Policy: {manager_policies.get('fulfillment_policy_id')}")
    print()
    
    if manager_policies.get('fulfillment_policy_id') != config.FULFILLMENT_POLICY_ID:
        print("[WARNING] Listing manager is using a different policy ID!")
        print(f"   Expected: {config.FULFILLMENT_POLICY_ID}")
        print(f"   Actual: {manager_policies.get('fulfillment_policy_id')}")
        print()
        print("   SOLUTION: Restart your Streamlit app to reload policies.")
        print("   The listing manager caches policies on initialization.")
    else:
        print("[OK] Listing manager is using the correct policy ID")
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("If policy IDs match, the issue might be:")
    print("1. Shipping service code validation during publish (stricter than offer creation)")
    print("2. Policy needs time to propagate (wait 5-10 minutes)")
    print("3. Category-specific validation for Trading Cards (261328)")
    print()
    print("Try:")
    print("1. Restart Streamlit app to ensure policies are reloaded")
    print("2. Wait 5-10 minutes and try again (policy propagation)")
    print("3. If still failing, we may need to try a different shipping service code")

if __name__ == "__main__":
    main()
