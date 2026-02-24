"""
Create a fulfillment policy with buyerResponsibleForShipping=True for Trading Cards.
This should fix Error 25007 for Trading Cards category.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create Fulfillment Policy with Buyer Pays Shipping")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Policy data with buyerResponsibleForShipping=True
    policy_data = {
        "name": "Buyer Pays - USPS Standard Post",
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
                        "buyerResponsibleForShipping": True,  # CRITICAL: Buyer pays
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
    
    print("Creating fulfillment policy with buyerResponsibleForShipping=True...")
    print()
    print("Policy Configuration:")
    print(f"  Name: {policy_data['name']}")
    print(f"  Shipping Service: USPSStandardPost")
    print(f"  Shipping Cost: $1.99")
    print(f"  Buyer Pays: True (CRITICAL)")
    print()
    
    # Create policy using direct API call
    response = client._make_request('POST', '/sell/account/v1/fulfillment_policy', data=policy_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        policy_id = result.get('fulfillmentPolicyId')
        print(f"[OK] Successfully created policy!")
        print(f"Policy ID: {policy_id}")
        print()
        print("=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print()
        print(f"1. Update your .env file:")
        print(f"   FULFILLMENT_POLICY_ID={policy_id}")
        print()
        print("2. Restart Streamlit app")
        print()
        print("3. Try creating a listing again")
        print()
        print("=" * 80)
    else:
        error_text = response.text
        print(f"[ERROR] Failed to create policy: HTTP {response.status_code}")
        print()
        
        # Try to parse error
        try:
            error_json = response.json()
            errors = error_json.get('errors', [])
            if errors:
                for err in errors:
                    error_id = err.get('errorId', 'N/A')
                    error_msg = err.get('message', 'Unknown error')
                    print(f"Error ID: {error_id}")
                    print(f"Message: {error_msg}")
                    print()
                    
                    # Check if policy already exists
                    if '20400' in str(error_id) or 'already exists' in error_msg.lower():
                        print("Policy with this name may already exist.")
                        print("Try using a different name or check existing policies.")
        except:
            print(f"Error response: {error_text[:500]}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
