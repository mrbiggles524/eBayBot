"""
Create a simple, working fulfillment policy that should work in sandbox.
Using the most basic shipping service that's almost certainly valid.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create Working Fulfillment Policy for Sandbox")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try USPSGroundAdvantage - newer, commonly accepted service
    # If that doesn't work, we'll try others
    services_to_try = [
        {
            "code": "USPSGroundAdvantage",
            "carrier": "USPS",
            "name": "USPS Ground Advantage"
        },
        {
            "code": "USPSStandardPost",
            "carrier": "USPS",
            "name": "USPS Standard Post"
        },
        {
            "code": "USPSPriority",
            "carrier": "USPS",
            "name": "USPS Priority"
        }
    ]
    
    for service in services_to_try:
        print(f"Trying {service['name']} ({service['code']})...")
        print()
        
        policy_data = {
            "marketplaceId": "EBAY_US",
            "name": f"Working Policy - {service['name']}",
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
                            "shippingServiceCode": service["code"],
                            "shippingCarrierCode": service["carrier"],
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
        
        try:
            response = client._make_request('POST', '/sell/account/v1/fulfillment_policy', data=policy_data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                policy_id = result.get('fulfillmentPolicyId')
                print(f"[OK] Policy created successfully!")
                print(f"Policy ID: {policy_id}")
                print(f"Service: {service['name']} ({service['code']})")
                print()
                print("=" * 80)
                print("SUCCESS - Use This Policy")
                print("=" * 80)
                print()
                print(f"Update your .env file:")
                print(f"FULFILLMENT_POLICY_ID={policy_id}")
                print()
                print("Then restart Streamlit and try creating a listing again!")
                return policy_id
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    errors = error_json.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('message', '')
                        print(f"[ERROR] {error_msg}")
                        if 'service' in error_msg.lower() or 'invalid' in error_msg.lower():
                            print(f"   Service code {service['code']} not valid, trying next...")
                            print()
                            continue
                except:
                    pass
                print(f"[ERROR] Status {response.status_code}, trying next service...")
                print()
                
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            print("Trying next service...")
            print()
            continue
    
    print("[ERROR] Could not create policy with any of the tried services.")
    print("You may need to check what services are valid for your marketplace.")

if __name__ == "__main__":
    main()
