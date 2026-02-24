"""
Update return policy ID in .env file.
Usage: python update_return_policy_id.py <policy_id>
"""
import sys
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_return_policy_id.py <return_policy_id>")
        print()
        print("Example: python update_return_policy_id.py 123456789012")
        sys.exit(1)
    
    policy_id = sys.argv[1].strip()
    
    print("=" * 80)
    print("Update Return Policy ID")
    print("=" * 80)
    print()
    print(f"Updating RETURN_POLICY_ID to: {policy_id}")
    print()
    
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
        print(f"Updated .env file with RETURN_POLICY_ID={policy_id}")
        print()
        print("Next steps:")
        print("1. Restart Streamlit app")
        print("2. Try creating the listing again")
    except Exception as e:
        print(f"[ERROR] Could not update .env: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
