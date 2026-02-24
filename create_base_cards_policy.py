"""
Create a fulfillment policy for base cards under $20.
Customer pays $1.99 for shipping (up to 3 oz).
Seller will use eBay shipping labels (costs ~$0.70 for 1 oz).
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create Fulfillment Policy - Base Cards Under $20")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Create fulfillment policy for base cards under $20
    # Customer pays $1.99, seller uses eBay labels (cheaper)
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": "Base Cards eBay Label Policy",
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
    
    print("Creating fulfillment policy for base cards under $20...")
    print()
    print("Policy configuration:")
    print("- Customer pays: $1.99 (flat rate, up to 3 oz)")
    print("- Shipping service: USPS First Class")
    print("- Seller will use eBay Labels API (costs ~$0.70 for 1 oz)")
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
            print("=" * 80)
            print("Next Steps")
            print("=" * 80)
            print()
            print("1. Add this to your .env file:")
            print(f"   BASE_CARDS_FULFILLMENT_POLICY_ID={policy_id}")
            print()
            print("2. Or update your listing code to use this policy for cards under $20")
            print()
            print("3. When a card sells, use eBay Logistics API to purchase labels:")
            print("   - Get shipping quote via createShippingQuote")
            print("   - Create label via createFromShippingQuote")
            print("   - You'll pay ~$0.70 for 1 oz, customer paid $1.99")
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
