"""
Check the actual details of a fulfillment policy to see what eBay saved.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Check Fulfillment Policy Details")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    policy_id = config.FULFILLMENT_POLICY_ID
    print(f"Checking policy ID: {policy_id}")
    print()
    
    response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{policy_id}')
    
    if response.status_code == 200:
        policy = response.json()
        print("Policy Details:")
        print(json.dumps(policy, indent=2))
        print()
        
        # Check shipping services
        shipping_options = policy.get('shippingOptions', [])
        print(f"Shipping Options: {len(shipping_options)}")
        for opt in shipping_options:
            print(f"  Option Type: {opt.get('optionType')}")
            services = opt.get('shippingServices', [])
            print(f"  Services: {len(services)}")
            for svc in services:
                print(f"    Service Code: {svc.get('shippingServiceCode')}")
                print(f"    Carrier: {svc.get('shippingCarrierCode')}")
                print(f"    Cost: {svc.get('shippingCost', {}).get('value', 'N/A')}")
                buyer_responsible = svc.get('buyerResponsibleForShipping')
                print(f"    buyerResponsibleForShipping: {buyer_responsible}")
                print(f"    (Type: {type(buyer_responsible)})")
                print()
    else:
        print(f"[ERROR] Status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
