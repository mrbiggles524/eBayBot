"""
Check fulfillment policy for shipping services.
"""
import sys
from ebay_api_client import eBayAPIClient
import json

sys.stdout.reconfigure(encoding='utf-8')

def check_policy(policy_id):
    """Check if fulfillment policy has shipping services."""
    print("=" * 80)
    print(f"CHECKING FULFILLMENT POLICY: {policy_id}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get policy details
    print("Getting policy details...")
    result = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{policy_id}', params={'marketplace_id': 'EBAY_US'})
    
    if result.status_code == 200:
        policy = result.json()
        name = policy.get('name', 'N/A')
        shipping_services = policy.get('shippingServices', [])
        
        print(f"✅ Policy found")
        print(f"   Name: {name}")
        print(f"   Shipping Services: {len(shipping_services)}")
        print()
        
        if shipping_services:
            print("✅ Policy HAS shipping services:")
            for service in shipping_services:
                service_code = service.get('shippingServiceCode', 'N/A')
                cost = service.get('shippingCost', {})
                cost_type = service.get('shippingCostType', 'N/A')
                print(f"   - {service_code} (Cost Type: {cost_type})")
        else:
            print("❌ Policy does NOT have shipping services!")
            print("   This will cause Error 25007 when publishing.")
            print()
            print("SOLUTION:")
            print("1. Go to: https://www.ebay.com/sh/account/policies")
            print(f"2. Find and edit policy: {policy_id}")
            print("3. Add at least one shipping service (e.g., USPS First Class)")
            print("4. Save the policy")
            print("5. Try creating listing again")
    else:
        print(f"❌ Failed to get policy: {result.status_code}")
        print(f"   Response: {result.text[:200]}")

if __name__ == "__main__":
    # Check the policy ID from the request
    policy_id = "229316003019"  # From the user's request
    check_policy(policy_id)
