"""
Create a new fulfillment policy using USPS Priority instead of First Class.
Sometimes First Class codes can have validation issues.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create New Fulfillment Policy - USPS Priority")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Create a new policy with USPS Priority (more commonly accepted)
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": "Cards Shipping Priority $1.99",
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
                        "shippingServiceCode": "USPSPriority",
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
    
    print("Creating new fulfillment policy with USPS Priority...")
    print()
    print("Policy configuration:")
    print("- Shipping Service: USPS Priority (more commonly accepted)")
    print("- Customer pays: $1.99 (flat rate)")
    print()
    print("Policy data:")
    print(json.dumps(policy_data, indent=2))
    print()
    
    try:
        response = client._make_request('POST', '/sell/account/v1/fulfillment_policy', data=policy_data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            policy_id = result.get('fulfillmentPolicyId')
            print(f"[OK] New policy created successfully!")
            print(f"Policy ID: {policy_id}")
            print()
            print("=" * 80)
            print("Next Steps")
            print("=" * 80)
            print()
            print("1. Update your .env file with the new policy ID:")
            print(f"   FULFILLMENT_POLICY_ID={policy_id}")
            print()
            print("2. Try creating a listing again")
            print()
            print("If this works, the issue was with the USPSFirstClass service code.")
            print("You can delete the old policy (6213834000) if desired.")
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
            except:
                print(f"Response text: {error_text[:1000]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
