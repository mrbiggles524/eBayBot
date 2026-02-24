"""
Create a default payment policy for sandbox.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

def main():
    print("=" * 80)
    print("Create Default Payment Policy")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Payment policy data - simplified structure
    timestamp = int(time.time())
    policy_data = {
        "marketplaceId": "EBAY_US",
        "name": f"Default Payment Policy {timestamp}",
        "categoryTypes": [
            {
                "name": "ALL_EXCLUDING_MOTORS_VEHICLES"
            }
        ]
    }
    
    print("Creating default payment policy...")
    print(f"Policy Name: {policy_data['name']}")
    print()
    
    response = client._make_request('POST', '/sell/account/v1/payment_policy', data=policy_data)
    
    if response.status_code in [200, 201]:
        result = response.json()
        policy_id = result.get('paymentPolicyId')
        print(f"[OK] Payment policy created!")
        print(f"Policy ID: {policy_id}")
        print()
        
        # Update .env file
        print("Updating .env file...")
        try:
            import re
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Replace PAYMENT_POLICY_ID
            pattern = r'PAYMENT_POLICY_ID=.*'
            replacement = f'PAYMENT_POLICY_ID={policy_id}'
            
            if re.search(pattern, env_content):
                env_content = re.sub(pattern, replacement, env_content)
            else:
                env_content += f"\nPAYMENT_POLICY_ID={policy_id}\n"
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print(f"[OK] Updated .env file with PAYMENT_POLICY_ID={policy_id}")
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()
            print("Restart Streamlit and try creating the listing again!")
        except Exception as e:
            print(f"[ERROR] Could not update .env: {e}")
            print()
            print("Please manually update your .env file:")
            print(f"PAYMENT_POLICY_ID={policy_id}")
    else:
        error_text = response.text
        print(f"[ERROR] Failed: HTTP {response.status_code}")
        try:
            error_json = response.json()
            errors = error_json.get('errors', [])
            if errors:
                for err in errors:
                    print(f"Error ID: {err.get('errorId')}")
                    print(f"Message: {err.get('message')}")
        except:
            print(f"Response: {error_text[:500]}")

if __name__ == "__main__":
    main()
