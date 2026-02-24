"""
List all fulfillment policies to find one with shipping services.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("List All Fulfillment Policies")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get all fulfillment policies
    result = client.get_fulfillment_policies()
    
    policies = result.get('policies', [])
    error = result.get('error')
    
    if error:
        print(f"[ERROR] {error}")
        print()
        print("This might mean:")
        print("1. No policies exist yet")
        print("2. Need to create a policy in eBay Seller Hub")
        print("3. API access issue")
        return
    
    if not policies:
        print("[INFO] No fulfillment policies found")
        print()
        print("You need to create a fulfillment policy in eBay Seller Hub:")
        print("1. Go to: https://sandbox.ebay.com/sh/account/policies")
        print("2. Create a new Fulfillment Policy")
        print("3. Add at least one shipping service (e.g., USPS First Class)")
        print("4. Save the policy")
        print("5. Copy the Policy ID and update FULFILLMENT_POLICY_ID in .env")
        return
    
    print(f"[OK] Found {len(policies)} fulfillment policy/policies:")
    print()
    
    for i, policy in enumerate(policies, 1):
        policy_id = policy.get('fulfillmentPolicyId', 'N/A')
        name = policy.get('name', 'Unnamed')
        shipping_options = policy.get('shippingOptions', [])
        
        print(f"{i}. {name}")
        print(f"   Policy ID: {policy_id}")
        
        if shipping_options:
            total_services = sum(len(opt.get('shippingServices', [])) for opt in shipping_options)
            print(f"   Shipping Services: {total_services} service(s) configured")
            print(f"   [OK] This policy has shipping services!")
        else:
            print(f"   [WARNING] NO shipping services configured!")
            print(f"   This policy won't work for publishing listings.")
        
        print()
    
    print("=" * 80)
    print("Next Steps")
    print("=" * 80)
    print()
    
    # Find a policy with shipping services
    good_policies = [p for p in policies if p.get('shippingOptions')]
    
    if good_policies:
        best_policy = good_policies[0]
        policy_id = best_policy.get('fulfillmentPolicyId')
        print(f"[OK] Use this policy: {best_policy.get('name')}")
        print(f"Policy ID: {policy_id}")
        print()
        print("Update your .env file:")
        print(f"FULFILLMENT_POLICY_ID={policy_id}")
    else:
        print("[ERROR] None of your policies have shipping services!")
        print()
        print("You need to:")
        print("1. Go to eBay Seller Hub → Account → Business Policies")
        print("2. Edit one of your fulfillment policies")
        print("3. Add at least one shipping service")
        print("4. Save the policy")
        print("5. Try creating listing again")

if __name__ == "__main__":
    main()
