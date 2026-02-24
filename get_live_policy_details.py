"""
Attempt to get details of the live account policy to see the exact service code.
This will help us understand what service code eBay actually uses.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Get Live Account Policy Details")
    print("=" * 80)
    print()
    
    config = Config()
    
    # Note: This would need production API access
    print("Policy URL from your live account:")
    print("https://www.ebay.com/bp/ship/edit/229316003019?lis=113")
    print()
    print("Policy ID: 229316003019")
    print("Used by: 113 listings")
    print()
    
    print("To get the exact service code, you have two options:")
    print()
    print("Option 1: Check via eBay Seller Hub")
    print("  1. Go to the URL above")
    print("  2. Look at the 'Primary service' field")
    print("  3. Note the exact service code shown")
    print()
    print("Option 2: Use Production API (if you have access)")
    print("  If you switch to production environment, we can query the policy")
    print("  directly via API to see the exact service code.")
    print()
    
    # Try to get it if we're in production
    if config.EBAY_ENVIRONMENT.lower() == 'production':
        print("You're in production mode. Attempting to get policy details...")
        print()
        client = eBayAPIClient()
        
        try:
            response = client._make_request('GET', '/sell/account/v1/fulfillment_policy/229316003019')
            
            if response.status_code == 200:
                policy = response.json()
                print("[OK] Retrieved policy from production:")
                print(json.dumps(policy, indent=2))
                
                # Extract shipping service code
                shipping_options = policy.get('shippingOptions', [])
                for option in shipping_options:
                    services = option.get('shippingServices', [])
                    for service in services:
                        service_code = service.get('shippingServiceCode', '')
                        carrier = service.get('shippingCarrierCode', '')
                        print()
                        print(f"Service Code: {service_code}")
                        print(f"Carrier: {carrier}")
            else:
                print(f"[ERROR] Could not get policy: {response.status_code}")
                print(response.text[:500])
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
    else:
        print("Currently in SANDBOX mode.")
        print("To check your live policy, either:")
        print("  1. View it in Seller Hub (URL above)")
        print("  2. Switch to production environment temporarily")
        print()
        print("Based on eBay documentation, the service code should be:")
        print("  US_eBayStandardEnvelope")
        print()
        print("But we can verify this from your live account if needed.")

if __name__ == "__main__":
    main()
