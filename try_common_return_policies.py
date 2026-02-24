"""
Try common return policy ID patterns to find one that works.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import re

def main():
    print("=" * 80)
    print("Try Common Return Policy IDs")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Common return policy ID patterns to try
    # Based on payment policy ID format (6213868000) and fulfillment policy IDs
    test_ids = [
        "6213869000",  # Next number after payment policy
        "6213870000",  # Next increment
        "6213871000",  # Another increment
        "6213800000",  # Lower range
        "6213900000",  # Higher range
        "243552423019",  # The one from URL (already tried, but retry)
    ]
    
    print("Testing return policy IDs...")
    print()
    
    for policy_id in test_ids:
        print(f"Testing: {policy_id}")
        
        response = client._make_request('GET', f'/sell/account/v1/return_policy/{policy_id}')
        
        if response.status_code == 200:
            policy = response.json()
            policy_name = policy.get('name', 'Unnamed')
            print(f"  [OK] Found valid return policy!")
            print(f"  Name: {policy_name}")
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
                else:
                    env_content += f"\nRETURN_POLICY_ID={policy_id}\n"
                
                with open('.env', 'w', encoding='utf-8') as f:
                    f.write(env_content)
                
                print(f"[OK] Updated .env with RETURN_POLICY_ID={policy_id}")
                print()
                print("=" * 80)
                print("SUCCESS!")
                print("=" * 80)
                print()
                print("Restart Streamlit and try creating the listing again!")
                return
            except Exception as e:
                print(f"[ERROR] Could not update .env: {e}")
        else:
            print(f"  [SKIP] Not found (HTTP {response.status_code})")
    
    print()
    print("=" * 80)
    print("None of the common patterns worked")
    print("=" * 80)
    print()
    print("The return policy must be created manually or obtained from a working listing.")
    print("Since sandbox APIs are limited, you'll need to:")
    print("1. Get the return policy ID from a working listing's details")
    print("2. Or create one manually (if sandbox UI works)")
    print()
    print("For now, the code will try creating listings WITHOUT a return policy.")
    print("This will likely fail, but you'll get a clearer error message.")

if __name__ == "__main__":
    main()
