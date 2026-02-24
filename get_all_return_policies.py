"""
Get all return policies and update .env with a valid one.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    print("=" * 80)
    print("Get All Return Policies")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print("Fetching all return policies...")
    print()
    
    policies_result = client.get_return_policies()
    
    if policies_result.get('success'):
        policies = policies_result.get('policies', [])
        
        if policies:
            print(f"[OK] Found {len(policies)} return policy/policies:")
            print()
            
            for i, policy in enumerate(policies, 1):
                policy_id = policy.get('returnPolicyId', 'N/A')
                policy_name = policy.get('name', 'Unnamed')
                print(f"{i}. {policy_name}")
                print(f"   ID: {policy_id}")
                print()
            
            # Use the first one
            selected_policy = policies[0]
            policy_id = selected_policy.get('returnPolicyId')
            policy_name = selected_policy.get('name', 'Unnamed')
            
            print(f"Using: {policy_name} (ID: {policy_id})")
            print()
            
            # Update .env
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
                print("2. Try creating the listing again")
            except Exception as e:
                print(f"[ERROR] Could not update .env: {e}")
                print()
                print("Please manually update your .env file:")
                print(f"RETURN_POLICY_ID={policy_id}")
        else:
            print("[WARNING] No return policies found via API")
            print()
            print("This is common in sandbox - return policies may not be queryable via API.")
            print()
            print("Options:")
            print("1. Try using the hex ID format: 4b040f2c108e000")
            print("2. Create a return policy manually in eBay Seller Hub")
            print("3. Get the return policy ID from a working listing")
            print()
            print("Trying hex ID format...")
            
            # Try the hex ID from the user's message
            hex_id = "4b040f2c108e000"
            print(f"Trying return policy ID: {hex_id}")
            
            response = client._make_request('GET', f'/sell/account/v1/return_policy/{hex_id}')
            if response.status_code == 200:
                policy = response.json()
                print(f"[OK] Hex ID works! Name: {policy.get('name', 'N/A')}")
                
                # Update .env with hex ID
                try:
                    with open('.env', 'r', encoding='utf-8') as f:
                        env_content = f.read()
                    
                    pattern = r'RETURN_POLICY_ID=.*'
                    replacement = f'RETURN_POLICY_ID={hex_id}'
                    
                    if re.search(pattern, env_content):
                        env_content = re.sub(pattern, replacement, env_content)
                    else:
                        env_content += f"\nRETURN_POLICY_ID={hex_id}\n"
                    
                    with open('.env', 'w', encoding='utf-8') as f:
                        f.write(env_content)
                    
                    print(f"[OK] Updated .env with RETURN_POLICY_ID={hex_id}")
                    print()
                    print("Restart Streamlit and try creating the listing again!")
                except Exception as e:
                    print(f"[ERROR] Could not update .env: {e}")
            else:
                print(f"[ERROR] Hex ID also doesn't work: HTTP {response.status_code}")
                print(response.text[:500])
    else:
        error = policies_result.get('error', 'Unknown error')
        print(f"[ERROR] Could not get return policies: {error}")
        print()
        print("Trying alternative approaches...")
        print()
        
        # Try the hex ID
        hex_id = "4b040f2c108e000"
        print(f"Trying hex ID format: {hex_id}")
        response = client._make_request('GET', f'/sell/account/v1/return_policy/{hex_id}')
        
        if response.status_code == 200:
            policy = response.json()
            print(f"[OK] Hex ID works! Name: {policy.get('name', 'N/A')}")
            
            # Update .env
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    env_content = f.read()
                
                pattern = r'RETURN_POLICY_ID=.*'
                replacement = f'RETURN_POLICY_ID={hex_id}'
                
                if re.search(pattern, env_content):
                    env_content = re.sub(pattern, replacement, env_content)
                else:
                    env_content += f"\nRETURN_POLICY_ID={hex_id}\n"
                
                with open('.env', 'w', encoding='utf-8') as f:
                    f.write(env_content)
                
                print(f"[OK] Updated .env with RETURN_POLICY_ID={hex_id}")
                print()
                print("Restart Streamlit and try creating the listing again!")
            except Exception as e:
                print(f"[ERROR] Could not update .env: {e}")
        else:
            print(f"[ERROR] Hex ID doesn't work either: HTTP {response.status_code}")
            print(response.text[:500])

if __name__ == "__main__":
    main()
