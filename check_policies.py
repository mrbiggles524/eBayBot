"""
Check your eBay policies - shipping, returns, payment.
"""
from ebay_api_client import eBayAPIClient
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def check_policies():
    client = eBayAPIClient()
    
    print("=" * 80)
    print("YOUR EBAY POLICIES")
    print("=" * 80)
    print()
    
    # Payment Policies
    print("PAYMENT POLICIES:")
    print("-" * 40)
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        policies = resp.json().get('paymentPolicies', [])
        for p in policies:
            print(f"  ID: {p.get('paymentPolicyId')}")
            print(f"  Name: {p.get('name')}")
            print(f"  Managed Payments: {p.get('immediatePay', 'N/A')}")
            print()
    else:
        print(f"  Error: {resp.status_code}")
    print()
    
    # Fulfillment/Shipping Policies
    print("SHIPPING/FULFILLMENT POLICIES:")
    print("-" * 40)
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        policies = resp.json().get('fulfillmentPolicies', [])
        for p in policies:
            print(f"  ID: {p.get('fulfillmentPolicyId')}")
            print(f"  Name: {p.get('name')}")
            
            # Check shipping services
            services = p.get('shippingServices', [])
            if services:
                print(f"  Shipping Services:")
                for s in services:
                    carrier = s.get('shippingCarrierCode', 'N/A')
                    service = s.get('shippingServiceCode', 'N/A')
                    cost = s.get('shippingCost', {}).get('value', 'N/A')
                    print(f"    - {carrier} {service} (${cost})")
            else:
                print(f"  Shipping Services: None configured!")
            
            # Check handling time
            handling = p.get('handlingTime', {})
            print(f"  Handling Time: {handling.get('value', 'N/A')} {handling.get('unit', '')}")
            print()
    else:
        print(f"  Error: {resp.status_code}")
    print()
    
    # Return Policies
    print("RETURN POLICIES:")
    print("-" * 40)
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    if resp.status_code == 200:
        policies = resp.json().get('returnPolicies', [])
        for p in policies:
            print(f"  ID: {p.get('returnPolicyId')}")
            print(f"  Name: {p.get('name')}")
            print(f"  Returns Accepted: {p.get('returnsAccepted', 'N/A')}")
            
            if p.get('returnsAccepted'):
                print(f"  Return Period: {p.get('returnPeriod', {}).get('value', 'N/A')} {p.get('returnPeriod', {}).get('unit', '')}")
                print(f"  Return Shipping Paid By: {p.get('returnShippingCostPayer', 'N/A')}")
            print()
    else:
        print(f"  Error: {resp.status_code}")
    print()
    
    # Check merchant location
    print("MERCHANT LOCATION:")
    print("-" * 40)
    resp = client._make_request('GET', '/sell/inventory/v1/location')
    if resp.status_code == 200:
        locations = resp.json().get('locations', [])
        for loc in locations:
            print(f"  Key: {loc.get('merchantLocationKey')}")
            print(f"  Name: {loc.get('name', 'N/A')}")
            address = loc.get('location', {}).get('address', {})
            print(f"  City: {address.get('city', 'N/A')}")
            print(f"  State: {address.get('stateOrProvince', 'N/A')}")
            print(f"  Country: {address.get('country', 'N/A')}")
            print()
    else:
        print(f"  Error: {resp.status_code}")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    print()
    print("1. RETURNS: For trading cards, 'No Returns Accepted' is common")
    print("   - Go to Seller Hub -> Business Policies -> Return Policies")
    print("   - Create a 'No Returns' policy if you don't have one")
    print()
    print("2. SHIPPING: Use eBay shipping labels for tracking")
    print("   - Set up calculated or flat rate shipping")
    print("   - PWE (Plain White Envelope) for cheap cards: ~$1")
    print("   - BMWT (Bubble Mailer with Tracking) for valuable cards: ~$4-5")
    print()

if __name__ == "__main__":
    check_policies()
