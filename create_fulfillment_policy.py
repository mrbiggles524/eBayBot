"""
Create a fulfillment policy with shipping service options.
This creates a basic policy that can be used for listings.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create Fulfillment Policy with Shipping Services")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Create a fulfillment policy with eBay shipping label service
    # Package: 3 oz, 6 x 4 x 1 inches, $1.99 shipping
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": "Cards Shipping $1.99 - eBay Label",
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "handlingTime": {
            "value": 1,
            "unit": "DAY"
        },
        "shippingOptions": [
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
    }
    
    print("Creating fulfillment policy with shipping services...")
    print()
    print("Policy data:")
    print(json.dumps(policy_data, indent=2))
    print()
    
    try:
        response = client._make_request('POST', '/sell/account/v1/fulfillment_policy', data=policy_data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            policy_id = result.get('fulfillmentPolicyId')
            print(f"[OK] Policy created successfully!")
            print(f"Policy ID: {policy_id}")
            print()
            print("Add this to your .env file:")
            print(f"FULFILLMENT_POLICY_ID={policy_id}")
            print()
            print("Or update it in Step 3 (Auto-Configure) in the Streamlit UI.")
        else:
            error_text = response.text
            print(f"[ERROR] Status {response.status_code}")
            try:
                error_json = response.json()
                print("Full error response:")
                print(json.dumps(error_json, indent=2))
                errors = error_json.get('errors', [])
                if errors:
                    for err in errors:
                        print(f"  Error ID: {err.get('errorId', 'N/A')}")
                        print(f"  Message: {err.get('message', 'N/A')}")
                        params = err.get('parameters', [])
                        if params:
                            print(f"  Parameters:")
                            for param in params:
                                print(f"    - {param.get('name', 'N/A')}: {param.get('value', 'N/A')}")
            except:
                print(f"Response text: {error_text[:1000]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
