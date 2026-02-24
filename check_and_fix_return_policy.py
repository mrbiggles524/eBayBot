"""
Check return policy and create one if needed.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re
import time

def main():
    print("=" * 80)
    print("Check and Fix Return Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    return_policy_id = config.RETURN_POLICY_ID
    
    if return_policy_id:
        print(f"Checking existing return policy ID: {return_policy_id}")
        print()
        
        # Check if it exists
        response = client._make_request('GET', f'/sell/account/v1/return_policy/{return_policy_id}')
        
        if response.status_code == 200:
            policy = response.json()
            print("[OK] Return policy exists!")
            print(f"  Name: {policy.get('name', 'N/A')}")
            print()
            print("Policy is valid. No changes needed.")
            return
        else:
            print(f"[WARNING] Return policy {return_policy_id} not found")
            print()
    
    # Get existing policies
    print("Fetching return policies...")
    policies_result = client.get_return_policies()
    
    if policies_result.get('success'):
        policies = policies_result.get('policies', [])
        
        if policies:
            print(f"[OK] Found {len(policies)} return policy/policies:")
            print()
            
            for i, policy in enumerate(policies, 1):
                policy_id = policy.get('returnPolicyId', 'N/A')
                policy_name = policy.get('name', 'Unnamed')
                print(f"{i}. {policy_name} (ID: {policy_id})")
            
            # Use the first one
            selected_policy = policies[0]
            policy_id = selected_policy.get('returnPolicyId')
            policy_name = selected_policy.get('name', 'Unnamed')
            
            print()
            print(f"Using: {policy_name} (ID: {policy_id})")
        else:
            print("[WARNING] No return policies found. Creating a new one...")
            print()
            
            # Create a default return policy - minimal structure
            timestamp = int(time.time())
            policy_data = {
                "marketplaceId": "EBAY_US",
                "name": f"Default Return Policy {timestamp}",
                "categoryTypes": [
                    {
                        "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
                    }
                ]
            }
            
            print("Creating default return policy...")
            print(f"Policy data: {json.dumps(policy_data, indent=2)}")
            print()
            
            response = client._make_request('POST', '/sell/account/v1/return_policy', data=policy_data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                policy_id = result.get('returnPolicyId')
                print(f"[OK] Return policy created! (ID: {policy_id})")
            else:
                error_text = response.text
                print(f"[ERROR] Failed to create: HTTP {response.status_code}")
                print(f"Full response: {error_text}")
                try:
                    error_json = response.json()
                    errors = error_json.get('errors', [])
                    if errors:
                        print("\nDetailed errors:")
                        for err in errors:
                            print(f"  Error ID: {err.get('errorId')}")
                            print(f"  Message: {err.get('message')}")
                            print(f"  Parameters: {err.get('parameters', [])}")
                except:
                    pass
                
                # Try with all required fields
                print("\nTrying with all required fields...")
                policy_data2 = {
                    "marketplaceId": "EBAY_US",
                    "name": f"Default Return Policy {timestamp}",
                    "categoryTypes": [
                        {
                            "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
                        }
                    ],
                    "returnsAcceptedOption": "RETURNS_ACCEPTED",
                    "refundMethod": "MERCHANDISE_CREDIT",
                    "returnPeriod": {
                        "value": 30,
                        "unit": "DAY"
                    },
                    "returnShippingCostPayer": "BUYER"
                }
                
                response2 = client._make_request('POST', '/sell/account/v1/return_policy', data=policy_data2)
                if response2.status_code in [200, 201]:
                    result = response2.json()
                    policy_id = result.get('returnPolicyId')
                    print(f"[OK] Return policy created! (ID: {policy_id})")
                else:
                    print(f"[ERROR] Still failed: HTTP {response2.status_code}")
                    print(f"Response: {response2.text[:500]}")
                    print()
                    print("=" * 80)
                    print("SOLUTION:")
                    print("=" * 80)
                    print()
                    print("Could not create return policy automatically.")
                    print("You may need to:")
                    print("1. Create a return policy manually in eBay Seller Hub")
                    print("2. Or use an existing return policy ID")
                    print()
                    print("For sandbox, you can try using a default return policy ID")
                    print("or create one through the eBay UI.")
                    return
        
        # Update .env file
        print()
        print("Updating .env file...")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Replace RETURN_POLICY_ID
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
            print("2. Try creating the listing again")
        except Exception as e:
            print(f"[ERROR] Could not update .env: {e}")
            print()
            print("Please manually update your .env file:")
            print(f"RETURN_POLICY_ID={policy_id}")
    else:
        error = policies_result.get('error', 'Unknown error')
        print(f"[ERROR] Could not get return policies: {error}")

if __name__ == "__main__":
    main()
