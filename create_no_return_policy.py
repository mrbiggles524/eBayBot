"""
Create a "No Return Accepted" return policy with all required fields.
Based on web search: even for "no returns", you must include returnPeriod and returnShippingCostPayer.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re
import time

def main():
    print("=" * 80)
    print("Create 'No Return Accepted' Return Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print("Creating return policy with all required fields...")
    print("(Even for 'No Return Accepted', eBay requires returnPeriod and returnShippingCostPayer)")
    print()
    
    timestamp = int(time.time())
    
    # Create "No Return Accepted" policy with ALL required fields
    # According to web search, even when returnsAccepted=false, you need returnPeriod and returnShippingCostPayer
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": f"No Return Accepted Policy {timestamp}",
        "categoryTypes": [
            {
                "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
            }
        ],
        "returnsAcceptedOption": "RETURNS_NOT_ACCEPTED",
        # Even for "no returns", these fields are REQUIRED per web search
        "returnPeriod": {
            "value": 30,
            "unit": "DAY"
        },
        "refundMethod": "MERCHANDISE_CREDIT",
        "returnShippingCostPayer": "BUYER"
    }
    
    print("Policy data:")
    print(json.dumps(policy_data, indent=2))
    print()
    
    response = client._make_request('POST', '/sell/account/v1/return_policy', data=policy_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        policy_id = result.get('returnPolicyId')
        print(f"[OK] Return policy created successfully!")
        print(f"Policy ID: {policy_id}")
        print()
        
        # Wait a few seconds (web search suggests this helps)
        print("Waiting 3 seconds for policy to propagate...")
        time.sleep(3)
        
        # Verify it exists
        verify_response = client._make_request('GET', f'/sell/account/v1/return_policy/{policy_id}')
        if verify_response.status_code == 200:
            policy = verify_response.json()
            print(f"[OK] Policy verified! Name: {policy.get('name', 'N/A')}")
        else:
            print(f"[WARNING] Could not verify policy: {verify_response.status_code}")
        
        # Update .env
        print()
        print("Updating .env file...")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            pattern = r'RETURN_POLICY_ID=.*'
            replacement = f'RETURN_POLICY_ID={policy_id}'
            
            if re.search(pattern, env_content):
                env_content = re.sub(pattern, replacement, env_content)
                print(f"[OK] Updated RETURN_POLICY_ID to {policy_id}")
            else:
                env_content += f"\nRETURN_POLICY_ID={policy_id}\n"
                print(f"[OK] Added RETURN_POLICY_ID={policy_id}")
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()
            print(f"Updated .env file with return policy ID: {policy_id}")
            print()
            print("Next steps:")
            print("1. Restart Streamlit app")
            print("2. Wait a few more seconds (5-10) for policy to fully propagate")
            print("3. Try creating the listing again")
        except Exception as e:
            print(f"[ERROR] Could not update .env: {e}")
            print()
            print("Please manually update your .env file:")
            print(f"RETURN_POLICY_ID={policy_id}")
    else:
        error_text = response.text
        print(f"[ERROR] Failed to create: HTTP {response.status_code}")
        print()
        print("Full response:")
        try:
            error_json = response.json()
            print(json.dumps(error_json, indent=2))
            errors = error_json.get('errors', [])
            if errors:
                print()
                print("Errors:")
                for err in errors:
                    print(f"  Error ID: {err.get('errorId')}")
                    print(f"  Message: {err.get('message')}")
                    print(f"  Parameters: {err.get('parameters', [])}")
        except:
            print(error_text[:1000])
        
        print()
        print("=" * 80)
        print("Could not create return policy via API")
        print("=" * 80)
        print()
        print("This is a known sandbox limitation.")
        print("You may need to:")
        print("1. Create the return policy manually in eBay Seller Hub")
        print("2. Or use an existing return policy ID from a working listing")

if __name__ == "__main__":
    main()
