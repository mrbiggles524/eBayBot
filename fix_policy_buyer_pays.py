"""
Fix the existing fulfillment policy to set buyerResponsibleForShipping to True.
eBay API sometimes ignores this field during creation, so we need to update it.
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
        print(f"Policy Name: {existing_policy.get('name')}")
        print()
        
        # Check current buyerResponsibleForShipping status
        print("Current shipping services:")
        for option in existing_policy.get('shippingOptions', []):
            for service in option.get('shippingServices', []):
                svc_code = service.get('shippingServiceCode', 'N/A')
                buyer_responsible = service.get('buyerResponsibleForShipping', False)
                print(f"  {svc_code}: buyerResponsibleForShipping = {buyer_responsible}")
        print()
        
        # Update buyerResponsibleForShipping to True in shipping services
        updated = False
        if 'shippingOptions' in existing_policy:
            for option in existing_policy['shippingOptions']:
                if 'shippingServices' in option:
                    for service in option['shippingServices']:
                        if service.get('buyerResponsibleForShipping') is not True:
                            service['buyerResponsibleForShipping'] = True
                            updated = True
                            print(f"[INFO] Will update buyerResponsibleForShipping to True for {service.get('shippingServiceCode', 'N/A')}")
        
        if not updated:
            print("[INFO] All services already have buyerResponsibleForShipping=True")
            return
        
        # Remove default field from categoryTypes if present (can't update this)
        if "categoryTypes" in existing_policy:
            for cat_type in existing_policy["categoryTypes"]:
                if "default" in cat_type:
                    del cat_type["default"]
        
        # Remove fields that can't be updated
        fields_to_remove = ['fulfillmentPolicyId']  # Read-only field
        for field in fields_to_remove:
            if field in existing_policy:
                del existing_policy[field]
        
        print()
        print("Updating policy...")
        print()
        
        # Update the policy
        response = client._make_request('PUT', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}', data=existing_policy)
        
        if response.status_code in [200, 204]:
            print(f"[OK] Policy updated successfully!")
            print()
            print("Verifying update...")
            # Verify the update
            verify_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
            if verify_response.status_code == 200:
                updated_policy = verify_response.json()
                print("Updated shipping services:")
                for option in updated_policy.get('shippingOptions', []):
                    for service in option.get('shippingServices', []):
                        svc_code = service.get('shippingServiceCode', 'N/A')
                        buyer_responsible = service.get('buyerResponsibleForShipping', False)
                        status = "✅" if buyer_responsible else "❌"
                        print(f"  {status} {svc_code}: buyerResponsibleForShipping = {buyer_responsible}")
            print()
            print("Policy is now configured with buyerResponsibleForShipping=True")
            print("Try creating a listing again!")
        else:
            error_text = response.text
            print(f"[ERROR] Status {response.status_code}")
            try:
                error_json = response.json()
                errors = error_json.get('errors', [])
                if errors:
                    for err in errors:
                        print(f"Error ID: {err.get('errorId')}")
                        print(f"Message: {err.get('message')}")
                else:
                    print(json.dumps(error_json, indent=2))
            except:
                print(f"Response text: {error_text[:1000]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
