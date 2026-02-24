"""
Create a fulfillment policy using USPS Priority Mail instead of Standard Post.
Sometimes different shipping services work better in sandbox.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

def main():
    print("=" * 80)
    print("Create Fulfillment Policy - USPS Priority (Alternative)")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try USPS Priority - sometimes works better than Standard Post
    timestamp = int(time.time())
    policy_data = {
        "name": f"Priority Mail Policy {timestamp}",
        "marketplaceId": "EBAY_US",
        "categoryTypes": [
            {
                "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
            }
        ],
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
                        "buyerResponsibleForLocalPickup": False,
                        "sortOrder": 1
                    }
                ]
            }
        ],
        "handlingTime": {
            "value": 1,
            "unit": "DAY"
        },
        "shipToLocations": {
            "regionIncluded": [
                {
                    "regionName": "Americas",
                    "regionType": "WORLDWIDE"
                }
            ]
        }
    }
    
    print("Creating policy with USPS Priority...")
    print(f"Policy Name: {policy_data['name']}")
    print(f"Service: USPSPriority")
    print(f"Cost: $1.99")
    print(f"Buyer Pays: True")
    print()
    
    response = client._make_request('POST', '/sell/account/v1/fulfillment_policy', data=policy_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        policy_id = result.get('fulfillmentPolicyId')
        print(f"[OK] Policy created!")
        print(f"Policy ID: {policy_id}")
        print()
        
        # Verify
        verify_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{policy_id}')
        if verify_response.status_code == 200:
            policy = verify_response.json()
            print("Policy Details:")
            for option in policy.get('shippingOptions', []):
                for service in option.get('shippingServices', []):
                    svc_code = service.get('shippingServiceCode', 'N/A')
                    buyer_responsible = service.get('buyerResponsibleForShipping', False)
                    print(f"  Service: {svc_code}")
                    print(f"  Buyer Pays: {buyer_responsible}")
            
            print()
            print("=" * 80)
            print("NEXT STEPS:")
            print("=" * 80)
            print()
            print(f"1. Update .env file:")
            print(f"   FULFILLMENT_POLICY_ID={policy_id}")
            print()
            print("2. Restart Streamlit")
            print()
            print("3. Try creating a listing again")
            print()
            print("NOTE: Even if buyerResponsibleForShipping shows False,")
            print("      the policy may still work for publishing.")
    else:
        error_text = response.text
        print(f"[ERROR] Failed: HTTP {response.status_code}")
        try:
            error_json = response.json()
            errors = error_json.get('errors', [])
            if errors:
                for err in errors:
                    print(f"  Error ID: {err.get('errorId')}")
                    print(f"  Message: {err.get('message')}")
        except:
            print(f"  Response: {error_text[:500]}")

if __name__ == "__main__":
    main()
