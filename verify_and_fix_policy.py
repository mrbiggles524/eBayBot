"""
Verify the fulfillment policy and try to fix any issues.
This will check the policy and attempt to recreate it if needed.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Verify and Fix Fulfillment Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    
    if not fulfillment_policy_id:
        print("[ERROR] FULFILLMENT_POLICY_ID not set in .env")
        return
    
    print(f"Checking policy ID: {fulfillment_policy_id}")
    print()
    
    # Get existing policy
    try:
        get_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
        if get_response.status_code != 200:
            print(f"[ERROR] Could not get policy: {get_response.status_code}")
            print(get_response.text[:500])
            return
        
        existing_policy = get_response.json()
        print("[OK] Policy retrieved")
        print()
        
        # Check shipping options
        shipping_options = existing_policy.get('shippingOptions', [])
        if not shipping_options:
            print("[ERROR] Policy has NO shipping options!")
            return
        
        print(f"[OK] Policy has {len(shipping_options)} shipping option(s)")
        for i, option in enumerate(shipping_options, 1):
            option_type = option.get('optionType', 'N/A')
            shipping_services = option.get('shippingServices', [])
            print(f"  Option {i}: {option_type} - {len(shipping_services)} service(s)")
            for service in shipping_services:
                service_code = service.get('shippingServiceCode', 'N/A')
                carrier_code = service.get('shippingCarrierCode', 'N/A')
                buyer_responsible = service.get('buyerResponsibleForShipping', False)
                print(f"    - Service: {service_code}, Carrier: {carrier_code}, Buyer Pays: {buyer_responsible}")
        
        print()
        print("Policy appears to have shipping services configured.")
        print()
        print("Possible issues:")
        print("1. Policy may need to be re-saved to refresh validation")
        print("2. Shipping service codes may need verification")
        print("3. There may be a timing issue with eBay processing")
        print()
        print("Trying to 'refresh' the policy by updating it with the same data...")
        print()
        
        # Try to update the policy with the same data (this might refresh validation)
        # Remove fields that can't be updated
        policy_update = existing_policy.copy()
        if "fulfillmentPolicyId" in policy_update:
            del policy_update["fulfillmentPolicyId"]
        if "categoryTypes" in policy_update:
            for cat_type in policy_update["categoryTypes"]:
                if "default" in cat_type:
                    del cat_type["default"]
        
        # Ensure buyerResponsibleForShipping is True
        for option in policy_update.get('shippingOptions', []):
            for service in option.get('shippingServices', []):
                service['buyerResponsibleForShipping'] = True
        
        response = client._make_request('PUT', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}', data=policy_update)
        
        if response.status_code in [200, 204]:
            print("[OK] Policy refreshed successfully!")
            print()
            print("Try creating a listing again.")
        else:
            error_text = response.text
            print(f"[WARNING] Could not refresh policy: {response.status_code}")
            try:
                error_json = response.json()
                print("Error details:")
                print(json.dumps(error_json, indent=2))
            except:
                print(f"Response: {error_text[:500]}")
            print()
            print("Since the policy has shipping services, the issue might be:")
            print("1. The shipping service code 'USPSFirstClass' may not be valid for your marketplace")
            print("2. Try creating a listing again - sometimes eBay needs time to process policy changes")
            print("3. Consider creating a new policy with verified shipping service codes")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
