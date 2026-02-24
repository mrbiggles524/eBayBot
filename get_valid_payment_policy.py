"""
Get valid payment policies and update .env file.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    print("=" * 80)
    print("Get Valid Payment Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print("Fetching payment policies...")
    print()
    
    policies_result = client.get_payment_policies()
    
    if policies_result.get('success'):
        policies = policies_result.get('policies', [])
        
        if not policies:
            print("[ERROR] No payment policies found")
            print("You need to create a payment policy in eBay Seller Hub first.")
            return
        
        print(f"[OK] Found {len(policies)} payment policy/policies:")
        print()
        
        for i, policy in enumerate(policies, 1):
            policy_id = policy.get('paymentPolicyId', 'N/A')
            policy_name = policy.get('name', 'Unnamed')
            marketplace = policy.get('marketplaceId', 'N/A')
            
            print(f"{i}. {policy_name}")
            print(f"   Policy ID: {policy_id}")
            print(f"   Marketplace: {marketplace}")
            print()
        
        # Use the first policy (or you can select based on name)
        selected_policy = policies[0]
        policy_id = selected_policy.get('paymentPolicyId')
        policy_name = selected_policy.get('name', 'Unnamed')
        
        print("=" * 80)
        print("SELECTED POLICY:")
        print("=" * 80)
        print(f"Name: {policy_name}")
        print(f"Policy ID: {policy_id}")
        print()
        
        # Update .env file
        print("Updating .env file...")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Replace PAYMENT_POLICY_ID
            pattern = r'PAYMENT_POLICY_ID=.*'
            replacement = f'PAYMENT_POLICY_ID={policy_id}'
            
            if re.search(pattern, env_content):
                env_content = re.sub(pattern, replacement, env_content)
                print(f"[OK] Updated PAYMENT_POLICY_ID to {policy_id}")
            else:
                # Add it if it doesn't exist
                env_content += f"\nPAYMENT_POLICY_ID={policy_id}\n"
                print(f"[OK] Added PAYMENT_POLICY_ID={policy_id}")
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()
            print(f"Updated .env file with payment policy ID: {policy_id}")
            print()
            print("Next steps:")
            print("1. Restart Streamlit app")
            print("2. Try creating the listing again")
        except Exception as e:
            print(f"[ERROR] Could not update .env file: {e}")
            print()
            print("Please manually update your .env file:")
            print(f"PAYMENT_POLICY_ID={policy_id}")
    else:
        error = policies_result.get('error', 'Unknown error')
        print(f"[ERROR] Could not get payment policies: {error}")
        print()
        print("You may need to:")
        print("1. Create a payment policy in eBay Seller Hub")
        print("2. Or check your API credentials")

if __name__ == "__main__":
    main()
