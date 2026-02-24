"""
Check if the payment policy exists and is valid.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Check Payment Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    payment_policy_id = config.PAYMENT_POLICY_ID
    
    if not payment_policy_id:
        print("[ERROR] PAYMENT_POLICY_ID not set in .env")
        return
    
    print(f"Checking payment policy ID: {payment_policy_id}")
    print()
    
    # Try to get the policy
    response = client._make_request('GET', f'/sell/account/v1/payment_policy/{payment_policy_id}')
    
    if response.status_code == 200:
        policy = response.json()
        print("[OK] Payment policy exists!")
        print()
        print("Policy Details:")
        print(f"  Policy ID: {policy.get('paymentPolicyId', 'N/A')}")
        print(f"  Name: {policy.get('name', 'N/A')}")
        print(f"  Marketplace: {policy.get('marketplaceId', 'N/A')}")
        print()
        print("Policy is valid and ready to use.")
    else:
        print(f"[ERROR] Payment policy not found: HTTP {response.status_code}")
        print()
        try:
            error_json = response.json()
            errors = error_json.get('errors', [])
            if errors:
                for err in errors:
                    print(f"Error ID: {err.get('errorId')}")
                    print(f"Message: {err.get('message')}")
        except:
            print(f"Response: {response.text[:500]}")
        print()
        print("=" * 80)
        print("SOLUTION:")
        print("=" * 80)
        print()
        print("The payment policy ID in your .env file is invalid or doesn't exist.")
        print("You need to:")
        print("1. Get a valid payment policy ID from eBay")
        print("2. Update PAYMENT_POLICY_ID in your .env file")
        print()
        print("To get payment policies, run:")
        print("  python -c \"from ebay_api_client import eBayAPIClient; client = eBayAPIClient(); policies = client.get_payment_policies(); print(json.dumps(policies, indent=2))\"")
        print()
        print("Or check your eBay Seller Hub:")
        print("  https://sandbox.ebay.com/sh/account/policies")

if __name__ == "__main__":
    main()
