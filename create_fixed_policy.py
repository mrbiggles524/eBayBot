"""
Create a NEW fulfillment policy with buyerResponsibleForShipping=True.
We'll use a unique name to avoid conflicts, then update .env to use it.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

def main():
    print("=" * 80)
    print("Create Fixed Fulfillment Policy (Buyer Pays)")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Create policy with unique name and buyerResponsibleForShipping=True
    timestamp = int(time.time())
    policy_data = {
        "name": f"Buyer Pays Policy {timestamp}",
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
                        "shippingServiceCode": "USPSStandardPost",
                        "shippingCarrierCode": "USPS",
                        "freeShipping": False,
                        "shippingCost": {
                            "value": "1.99",
                            "currency": "USD"
                        },
                        "buyerResponsibleForShipping": True,  # CRITICAL
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
    
    print("Creating new policy with buyerResponsibleForShipping=True...")
    print(f"Policy Name: {policy_data['name']}")
    print()
    
    response = client._make_request('POST', '/sell/account/v1/fulfillment_policy', data=policy_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        policy_id = result.get('fulfillmentPolicyId')
        print(f"[OK] Policy created successfully!")
        print(f"Policy ID: {policy_id}")
        print()
        
        # Verify the policy was saved correctly
        print("Verifying policy...")
        verify_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{policy_id}')
        if verify_response.status_code == 200:
            policy = verify_response.json()
            print(f"Policy Name: {policy.get('name')}")
            for option in policy.get('shippingOptions', []):
                for service in option.get('shippingServices', []):
                    svc_code = service.get('shippingServiceCode', 'N/A')
                    buyer_responsible = service.get('buyerResponsibleForShipping', False)
                    status = "✅" if buyer_responsible else "❌"
                    print(f"  {status} {svc_code}: buyerResponsibleForShipping = {buyer_responsible}")
            
            if buyer_responsible:
                print()
                print("=" * 80)
                print("SUCCESS - Policy Created with Buyer Pays Shipping")
                print("=" * 80)
                print()
                print(f"Update your .env file:")
                print(f"FULFILLMENT_POLICY_ID={policy_id}")
                print()
                print("Then restart Streamlit and try creating a listing again!")
            else:
                print()
                print("[WARNING] Policy was created but buyerResponsibleForShipping is still False!")
                print("eBay API may be ignoring this field. You may need to:")
                print("1. Manually edit the policy in eBay Seller Hub")
                print("2. Or try a different shipping service code")
        else:
            print(f"[WARNING] Could not verify policy: {verify_response.status_code}")
    else:
        error_text = response.text
        print(f"[ERROR] Failed to create policy: HTTP {response.status_code}")
        try:
            error_json = response.json()
            errors = error_json.get('errors', [])
            if errors:
                for err in errors:
                    print(f"Error ID: {err.get('errorId')}")
                    print(f"Message: {err.get('message')}")
        except:
            print(f"Response: {error_text[:500]}")

if __name__ == "__main__":
    main()
