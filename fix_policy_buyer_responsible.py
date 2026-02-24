"""
Fix the fulfillment policy to set buyerResponsibleForShipping to true.
This ensures the buyer pays for shipping, not the seller.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Fix Fulfillment Policy - Set Buyer Responsible for Shipping")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    
    if not fulfillment_policy_id:
        print("[ERROR] FULFILLMENT_POLICY_ID not set in .env")
        return
    
    print(f"Policy ID: {fulfillment_policy_id}")
    print()
    
    # Get existing policy
    try:
        get_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
        if get_response.status_code != 200:
            print(f"[ERROR] Could not get policy: {get_response.status_code}")
            print(get_response.text[:500])
            return
        
        existing_policy = get_response.json()
        print("[OK] Retrieved existing policy")
        
        # Update buyerResponsibleForShipping to true in shipping services
        if 'shippingOptions' in existing_policy:
            for option in existing_policy['shippingOptions']:
                if 'shippingServices' in option:
                    for service in option['shippingServices']:
                        service['buyerResponsibleForShipping'] = True
                        print(f"[INFO] Updated buyerResponsibleForShipping to True for {service.get('shippingServiceCode', 'N/A')}")
        
        # Remove default field from categoryTypes if present
        if "categoryTypes" in existing_policy:
            for cat_type in existing_policy["categoryTypes"]:
                if "default" in cat_type:
                    del cat_type["default"]
        
        print()
        print("Updating policy...")
        print()
        
        # Update the policy
        response = client._make_request('PUT', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}', data=existing_policy)
        
        if response.status_code in [200, 204]:
            print(f"[OK] Policy updated successfully!")
            print()
            print("Policy now configured with:")
            print("- buyerResponsibleForShipping: True (buyer pays for shipping)")
            print("- Shipping services preserved")
            print()
            print("Try creating a listing again!")
        else:
            error_text = response.text
            print(f"[ERROR] Status {response.status_code}")
            try:
                error_json = response.json()
                print("Full error response:")
                print(json.dumps(error_json, indent=2))
            except:
                print(f"Response text: {error_text[:1000]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
