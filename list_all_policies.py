"""
List all policies to see what's available.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def list_policies():
    """List all policies."""
    print("=" * 80)
    print("Listing All Policies")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Get fulfillment policies
    print("Fulfillment Policies:")
    print("-" * 80)
    try:
        response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        
        if response.status_code == 200:
            data = response.json()
            policies = data.get('fulfillmentPolicies', [])
            
            for i, policy in enumerate(policies, 1):
                policy_id = policy.get('fulfillmentPolicyId')
                name = policy.get('name', 'N/A')
                shipping_services = policy.get('shippingServices', [])
                
                print(f"{i}. {name}")
                print(f"   ID: {policy_id}")
                print(f"   Shipping Services: {len(shipping_services)}")
                
                if shipping_services:
                    print("   [OK] Has shipping services")
                    for service in shipping_services[:3]:
                        print(f"      - {service.get('shippingServiceName', 'N/A')}")
                else:
                    print("   [WARNING] No shipping services!")
                print()
        else:
            print(f"[ERROR] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print()
    print("=" * 80)
    print("Solution")
    print("=" * 80)
    print()
    print("The fulfillment policy needs shipping services configured.")
    print()
    print("To fix:")
    print("  1. Go to: https://www.ebay.com/sh/landing")
    print("  2. Navigate to: Account -> Business Policies")
    print("  3. Find your fulfillment policy (ID: 6213866000)")
    print("  4. Edit it and add at least one shipping service")
    print("  5. Save")
    print("  6. Then try publishing again")
    print()

if __name__ == "__main__":
    list_policies()
