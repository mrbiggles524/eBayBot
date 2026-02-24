"""
Verify the return policy ID.
"""
from ebay_api_client import eBayAPIClient
import re

def main():
    print("=" * 80)
    print("Verify Return Policy")
    print("=" * 80)
    print()
    
    return_policy_id = "243552423019"
    
    print(f"Checking return policy ID: {return_policy_id}")
    print()
    
    client = eBayAPIClient()
    
    # Check if it exists
    response = client._make_request('GET', f'/sell/account/v1/return_policy/{return_policy_id}')
    
    if response.status_code == 200:
        policy = response.json()
        print("[OK] Return policy exists and is valid!")
        print(f"  ID: {return_policy_id}")
        print(f"  Name: {policy.get('name', 'N/A')}")
        print()
        
        # Update .env
        print("Updating .env file...")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            pattern = r'RETURN_POLICY_ID=.*'
            replacement = f'RETURN_POLICY_ID={return_policy_id}'
            
            if re.search(pattern, env_content):
                env_content = re.sub(pattern, replacement, env_content)
                print(f"[OK] Updated RETURN_POLICY_ID to {return_policy_id}")
            else:
                env_content += f"\nRETURN_POLICY_ID={return_policy_id}\n"
                print(f"[OK] Added RETURN_POLICY_ID={return_policy_id}")
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()
            print(f"Updated .env file with return policy ID: {return_policy_id}")
            print()
            print("Next steps:")
            print("1. Restart Streamlit app")
            print("2. Try creating the listing again")
        except Exception as e:
            print(f"[ERROR] Could not update .env: {e}")
            print()
            print("Please manually update your .env file:")
            print(f"RETURN_POLICY_ID={return_policy_id}")
    else:
        print(f"[ERROR] Return policy not found: HTTP {response.status_code}")
        print(response.text[:500])
        print()
        print("However, you provided this ID, so we'll update .env anyway.")
        print("It might work when used in a listing.")
        
        # Update .env anyway
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            pattern = r'RETURN_POLICY_ID=.*'
            replacement = f'RETURN_POLICY_ID={return_policy_id}'
            
            if re.search(pattern, env_content):
                env_content = re.sub(pattern, replacement, env_content)
            else:
                env_content += f"\nRETURN_POLICY_ID={return_policy_id}\n"
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print(f"[OK] Updated .env with RETURN_POLICY_ID={return_policy_id}")
        except Exception as e:
            print(f"[ERROR] Could not update .env: {e}")

if __name__ == "__main__":
    main()
