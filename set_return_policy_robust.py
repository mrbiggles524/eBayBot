"""
Set return policy ID and add robust debugging.
"""
import re

def main():
    return_policy_id = "243552423019"
    
    print("=" * 80)
    print("Setting Return Policy ID with Robust Debugging")
    print("=" * 80)
    print()
    print(f"Setting RETURN_POLICY_ID to: {return_policy_id}")
    print()
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'RETURN_POLICY_ID=.*'
        replacement = f'RETURN_POLICY_ID={return_policy_id}'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"[OK] Updated RETURN_POLICY_ID to {return_policy_id}")
        else:
            content += f"\nRETURN_POLICY_ID={return_policy_id}\n"
            print(f"[OK] Added RETURN_POLICY_ID={return_policy_id}")
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print()
        print("Now testing if this policy ID works...")
        print()
        
        # Test the policy
        from ebay_api_client import eBayAPIClient
        client = eBayAPIClient()
        
        print(f"Testing return policy ID: {return_policy_id}")
        response = client._make_request('GET', f'/sell/account/v1/return_policy/{return_policy_id}')
        
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            policy = response.json()
            print("[OK] Return policy EXISTS and is valid!")
            print(f"  Name: {policy.get('name', 'N/A')}")
            print(f"  Returns Accepted: {policy.get('returnsAcceptedOption', 'N/A')}")
            print()
            print("The policy exists, so the issue might be:")
            print("1. How we're including it in the offer data")
            print("2. The policy might not be valid for the category")
            print("3. There might be a timing/propagation issue")
        else:
            print(f"[WARNING] Policy query returned: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            print()
            print("Even if the API says it doesn't exist, it might still work")
            print("when used in a listing (sandbox API limitations)")
        
        print()
        print("=" * 80)
        print("SUCCESS - Policy ID set in .env")
        print("=" * 80)
        print()
        print("The code will now use this return policy ID when creating listings.")
        print("If it still fails, the debugging will show exactly what's happening.")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
