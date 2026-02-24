"""
Fix the fulfillment policy to ensure buyer pays and verify it's being used correctly.
Then provide recommendations for fixing Error 25007.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Fix Fulfillment Policy and Diagnose Error 25007")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    fulfillment_policy_id = config.FULFILLMENT_POLICY_ID
    print(f"Current Policy ID: {fulfillment_policy_id}")
    print()
    
    # Get policy details
    print("1. Checking current policy...")
    policy_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
    
    if policy_response.status_code != 200:
        print(f"[ERROR] Could not get policy: {policy_response.status_code}")
        return
    
    policy = policy_response.json()
    print(f"   Policy Name: {policy.get('name')}")
    print(f"   Service: {policy.get('shippingOptions', [{}])[0].get('shippingServices', [{}])[0].get('shippingServiceCode', 'N/A')}")
    buyer_pays = policy.get('shippingOptions', [{}])[0].get('shippingServices', [{}])[0].get('buyerResponsibleForShipping', False)
    print(f"   Buyer Pays: {buyer_pays}")
    print()
    
    if not buyer_pays:
        print("[WARNING] Policy shows seller pays, but we want buyer to pay.")
        print("This might be causing validation issues during publish.")
        print()
        print("Since we can't update via API (categoryTypes.default issue),")
        print("you'll need to update it manually in eBay Seller Hub:")
        print("1. Go to: https://sandbox.ebay.com/sh/account/policies")
        print(f"2. Find policy ID: {fulfillment_policy_id}")
        print("3. Edit and ensure 'Buyer pays for shipping' is selected")
        print("4. Save")
        print()
    
    print("2. Error 25007 Diagnosis:")
    print("   The policy HAS shipping services configured.")
    print("   But eBay is rejecting it during PUBLISHING.")
    print()
    print("   This suggests:")
    print("   a) Policy validation is stricter during publish")
    print("   b) Shipping service code may not be valid for Trading Cards (261328)")
    print("   c) Policy needs time to propagate")
    print("   d) buyerResponsibleForShipping setting might matter")
    print()
    
    print("3. Solutions to try (in order):")
    print()
    print("   SOLUTION 1: Wait and Retry")
    print("   - Wait 5-10 minutes for policy to fully propagate")
    print("   - Restart Streamlit app to reload policies")
    print("   - Try creating listing again")
    print()
    print("   SOLUTION 2: Update Policy in Seller Hub")
    print("   - Go to: https://sandbox.ebay.com/sh/account/policies")
    print(f"   - Edit policy {fulfillment_policy_id}")
    print("   - Ensure 'Buyer pays for shipping' is selected")
    print("   - Verify shipping service is configured")
    print("   - Save and try again")
    print()
    print("   SOLUTION 3: Try Different Shipping Service")
    print("   - USPSFirstClass might not be valid for Trading Cards during publish")
    print("   - We could try USPSPriority (already created policy 6213856000)")
    print("   - Update .env: FULFILLMENT_POLICY_ID=6213856000")
    print("   - Restart Streamlit and try again")
    print()
    
    # Check if the newer policy exists
    print("4. Checking if newer policy (6213856000) exists...")
    new_policy_response = client._make_request('GET', '/sell/account/v1/fulfillment_policy/6213856000')
    if new_policy_response.status_code == 200:
        new_policy = new_policy_response.json()
        print(f"   [OK] Newer policy exists: {new_policy.get('name')}")
        service = new_policy.get('shippingOptions', [{}])[0].get('shippingServices', [{}])[0].get('shippingServiceCode', 'N/A')
        print(f"   Service: {service}")
        print()
        print("   You can try switching to this policy:")
        print("   - Update .env: FULFILLMENT_POLICY_ID=6213856000")
        print("   - Restart Streamlit app")
        print("   - Try creating listing again")
    else:
        print("   [INFO] Newer policy not found or not accessible")
    
    print()
    print("=" * 80)
    print("Recommendation")
    print("=" * 80)
    print()
    print("Try SOLUTION 3 first (switch to policy 6213856000 with USPSPriority):")
    print("1. Update .env file: FULFILLMENT_POLICY_ID=6213856000")
    print("2. Restart Streamlit app")
    print("3. Try creating listing again")
    print()
    print("If that doesn't work, try SOLUTION 2 (update policy in Seller Hub)")

if __name__ == "__main__":
    main()
