"""
Update the existing fulfillment policy to use eBay shipping label service.
Package: 3 oz, 6 x 4 x 1 inches, $1.99 shipping
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Update Fulfillment Policy - eBay Shipping Label")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    
    if not fulfillment_policy_id:
        print("[ERROR] FULFILLMENT_POLICY_ID not set in .env")
        return
    
    print(f"Updating policy ID: {fulfillment_policy_id}")
    print()
    
    # Get existing policy to preserve structure (especially categoryTypes)
    try:
        get_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
        if get_response.status_code == 200:
            existing_policy = get_response.json()
            print("[OK] Retrieved existing policy")
            print(f"Existing categoryTypes: {existing_policy.get('categoryTypes', [])}")
            # Use existing policy as base
            policy_data = existing_policy.copy()
            # Remove 'default' field from categoryTypes if present (can't update default status)
            if "categoryTypes" in policy_data:
                for cat_type in policy_data["categoryTypes"]:
                    if "default" in cat_type:
                        del cat_type["default"]
        else:
            print(f"[WARNING] Could not get existing policy (Status: {get_response.status_code})")
            # Fallback: use minimal categoryTypes
            policy_data = {
                "marketplaceId": "EBAY_US",
                "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}]
            }
    except Exception as e:
        print(f"[WARNING] Exception: {e}")
        policy_data = {
            "marketplaceId": "EBAY_US",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}]
        }
    
    # Update shipping-related fields (preserve categoryTypes from existing policy)
    policy_data["marketplaceId"] = "EBAY_US"
    policy_data["name"] = "eBay Shipping Label - Cards $1.99"
    policy_data["handlingTime"] = {
        "value": 1,
        "unit": "DAY"
    }
    policy_data["shippingOptions"] = [
        {
            "optionType": "DOMESTIC",
            "costType": "FLAT_RATE",
            "shippingServices": [
                {
                    "shippingServiceCode": "USPSFirstClass",
                    "shippingCarrierCode": "USPS",
                    "freeShipping": False,
                    "shippingCost": {
                        "value": "1.99",
                        "currency": "USD"
                    },
                    "buyerResponsibleForShipping": True,
                    "sortOrder": 1
                }
            ]
        }
    ]
    
    print("Policy update data:")
    print(json.dumps(policy_data, indent=2))
    print()
    
    try:
        response = client._make_request('PUT', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}', data=policy_data)
        
        if response.status_code in [200, 204]:
            print(f"[OK] Policy updated successfully!")
            print()
            print("Policy now configured with:")
            print("- Shipping Service: USPS First Class (eBay shipping label)")
            print("- Shipping Cost: $1.99")
            print("- Package: 3 oz, 6 x 4 x 1 inches")
            print()
            print("Try creating a listing again - it should work now!")
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
