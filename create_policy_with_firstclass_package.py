"""
Create a new fulfillment policy using USPSFirstClassPackage instead of USPSPriority.
Some categories may require more specific service codes.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create Fulfillment Policy - USPS First Class Package")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try USPSFirstClassPackage - more specific code that might be required
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": "Cards First Class Package $1.99",
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
                        "shippingServiceCode": "USPSFirstClassPackage",
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
    
    print("Creating new fulfillment policy with USPS First Class Package...")
    print()
    print("Policy configuration:")
    print("- Shipping Service: USPSFirstClassPackage (more specific code)")
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
            print("USPSFirstClassPackage is a more specific service code that")
            print("may be required for Trading Cards category (261328).")
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
                        # If service code is invalid, try USPSPriorityFlatRateEnvelope
                        if 'service' in err.get('message', '').lower() or 'invalid' in err.get('message', '').lower():
                            print()
                            print("  [SUGGESTION] Service code might be invalid.")
                            print("  Try USPSPriorityFlatRateEnvelope or USPSPriority instead.")
            except:
                print(f"Response text: {error_text[:1000]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
