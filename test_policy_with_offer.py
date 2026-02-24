"""
Test if the fulfillment policy works by creating a minimal offer.
This will help diagnose if the issue is with the policy or the offer structure.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Test Fulfillment Policy with Minimal Offer")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    print(f"Using fulfillment policy ID: {fulfillment_policy_id}")
    print()
    
    # First, verify the policy exists and has shipping services
    print("1. Verifying policy...")
    policy_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
    if policy_response.status_code != 200:
        print(f"[ERROR] Could not get policy: {policy_response.status_code}")
        print(policy_response.text[:500])
        return
    
    policy = policy_response.json()
    shipping_options = policy.get('shippingOptions', [])
    if not shipping_options:
        print("[ERROR] Policy has no shipping options!")
        return
    
    print(f"[OK] Policy has {len(shipping_options)} shipping option(s)")
    for option in shipping_options:
        services = option.get('shippingServices', [])
        print(f"  - {option.get('optionType')}: {len(services)} service(s)")
        for service in services:
            print(f"    * {service.get('shippingServiceCode')} ({service.get('shippingCarrierCode')})")
    print()
    
    # Get other required policies
    policies = client.get_policy_ids()
    payment_policy_id = policies.get('payment_policy_id')
    return_policy_id = policies.get('return_policy_id')
    merchant_location_key = policies.get('merchant_location_key')
    
    if not payment_policy_id or not return_policy_id:
        print("[ERROR] Missing payment or return policy")
        print(f"  Payment: {payment_policy_id}")
        print(f"  Return: {return_policy_id}")
        return
    
    print(f"2. Using policies:")
    print(f"   Payment: {payment_policy_id}")
    print(f"   Return: {return_policy_id}")
    print(f"   Merchant Location: {merchant_location_key or 'NOT SET'}")
    print()
    
    # Try to create a minimal test offer (this will fail but show us the exact error)
    print("3. Creating minimal test offer...")
    print("   (This will likely fail, but will show us the exact validation error)")
    print()
    
    test_offer = {
        "sku": "TEST_POLICY_CHECK_001",
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": "261328",  # Trading Cards
        "listing": {
            "title": "Test Policy Validation",
            "description": "Testing fulfillment policy",
            "listingPolicies": {
                "fulfillmentPolicyId": fulfillment_policy_id,
                "paymentPolicyId": payment_policy_id,
                "returnPolicyId": return_policy_id
            }
        },
        "pricingSummary": {
            "price": {
                "value": "1.00",
                "currency": "USD"
            }
        },
        "quantity": 1,
        "listingDuration": "GTC"
    }
    
    if merchant_location_key:
        test_offer["merchantLocationKey"] = merchant_location_key
    
    print("Offer payload:")
    print(json.dumps(test_offer, indent=2))
    print()
    
    result = client.create_offer(test_offer)
    
    if result.get("success"):
        print("[OK] Test offer created successfully!")
        print("This means the policy is valid!")
        offer_id = result.get("data", {}).get("offerId")
        if offer_id:
            print(f"Offer ID: {offer_id}")
            print("Deleting test offer...")
            # Try to delete it
            delete_response = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
            if delete_response.status_code in [200, 204]:
                print("[OK] Test offer deleted")
    else:
        error = result.get("error", {})
        print("[ERROR] Test offer creation failed:")
        if isinstance(error, dict):
            errors = error.get('errors', [])
            if errors:
                for err in errors:
                    error_id = err.get('errorId', 'N/A')
                    message = err.get('message', 'N/A')
                    print(f"  Error ID: {error_id}")
                    print(f"  Message: {message}")
                    if error_id == 25007:
                        print()
                        print("  [DIAGNOSIS] This confirms the fulfillment policy validation issue.")
                        print("  The policy has shipping services, but eBay is rejecting them.")
                        print("  Possible causes:")
                        print("  1. Shipping service code not valid for category 261328")
                        print("  2. Policy needs to be re-saved/refreshed")
                        print("  3. Service code needs to be more specific (e.g., USPSFirstClassPackage)")
            else:
                print(json.dumps(error, indent=2))
        else:
            print(f"  {error}")

if __name__ == "__main__":
    main()
