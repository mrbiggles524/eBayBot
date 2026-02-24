"""
Create a fulfillment policy using eBay Standard Envelope shipping service.
This matches the user's live account policy for cards under $20.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Create Fulfillment Policy - eBay Standard Envelope")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # eBay Standard Envelope service code - this is the special eBay service for cards
    # Based on user's live account: $1.99 first item, $0.39 each additional
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": "PWE eBay Shipping Envelope ONLY Cards Under $20",
        "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
        "handlingTime": {
            "value": 0,  # Same business day
            "unit": "DAY"
        },
        "shippingOptions": [
            {
                "optionType": "DOMESTIC",
                "costType": "FLAT_RATE",
                "shippingServices": [
                    {
                        "shippingServiceCode": "US_eBayStandardEnvelope",  # eBay Standard Envelope
                        "shippingCarrierCode": "USPS",  # Must be USPS for eBay Standard Envelope
                        "freeShipping": False,
                        "shippingCost": {
                            "value": "1.99",
                            "currency": "USD"
                        },
                        "additionalShippingCost": {
                            "value": "0.39",
                            "currency": "USD"
                        },
                        "buyerResponsibleForShipping": True,
                        "sortOrder": 1
                    }
                ]
            }
        ]
    }
    
    print("Creating fulfillment policy with eBay Standard Envelope...")
    print()
    print("Policy configuration (matching your live account):")
    print("- Service: eBay Standard Envelope (for cards under $20)")
    print("- Buyer pays: $1.99 (first item)")
    print("- Additional items: $0.39 each")
    print("- Handling time: Same business day")
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
            print("1. Update your .env file with the new policy ID:")
            print(f"   FULFILLMENT_POLICY_ID={policy_id}")
            print()
            print("2. This policy is specifically for cards under $20")
            print("   eBay Standard Envelope is only available for items up to $20")
            print()
            print("3. Try creating a listing again")
            print()
            print("Note: If StandardEnvelope service code doesn't work, we may")
            print("need to try alternative codes like:")
            print("  - eBayStandardEnvelope")
            print("  - StandardEnvelopeUS")
            print("  - Or check eBay's metadata API for the exact code")
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
                        error_id = err.get('errorId', 'N/A')
                        message = err.get('message', 'N/A')
                        print(f"  Error ID: {error_id}")
                        print(f"  Message: {message}")
                        
                        # If service code is invalid, suggest alternatives
                        if 'service' in message.lower() or 'invalid' in message.lower():
                            print()
                            print("  [SUGGESTION] The service code might be incorrect.")
                            print("  eBay Standard Envelope might use a different code.")
                            print("  We may need to query eBay's metadata API to get")
                            print("  the exact service code for your marketplace.")
            except:
                print(f"Response text: {error_text[:1000]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
