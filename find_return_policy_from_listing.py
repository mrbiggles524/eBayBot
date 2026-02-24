"""
Try to find return policy ID from existing offers/listings.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Find Return Policy from Existing Listings")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print("Checking existing offers for return policy ID...")
    print()
    
    # Get offers
    response = client._make_request('GET', '/sell/inventory/v1/offer', params={
        'marketplace_id': 'EBAY_US',
        'limit': 10
    })
    
    if response.status_code == 200:
        data = response.json()
        offers = data.get('offers', [])
        
        if offers:
            print(f"Found {len(offers)} offer(s)")
            print()
            
            for i, offer in enumerate(offers[:5], 1):  # Check first 5
                offer_id = offer.get('offerId', 'N/A')
                sku = offer.get('sku', 'N/A')
                
                # Get full offer details
                offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
                if offer_response.status_code == 200:
                    offer_data = offer_response.json()
                    listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                    return_policy_id = listing_policies.get('returnPolicyId')
                    
                    if return_policy_id:
                        print(f"[OK] Found return policy ID: {return_policy_id}")
                        print(f"  From offer: {offer_id} (SKU: {sku})")
                        print()
                        
                        # Verify it exists
                        verify_response = client._make_request('GET', f'/sell/account/v1/return_policy/{return_policy_id}')
                        if verify_response.status_code == 200:
                            policy = verify_response.json()
                            print(f"[OK] Return policy is valid!")
                            print(f"  Name: {policy.get('name', 'N/A')}")
                            print()
                            
                            # Update .env
                            print("Updating .env file...")
                            try:
                                import re
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
                                print()
                                print("Restart Streamlit and try creating the listing again!")
                                return
                            except Exception as e:
                                print(f"[ERROR] Could not update .env: {e}")
                                print()
                                print("Please manually update your .env file:")
                                print(f"RETURN_POLICY_ID={return_policy_id}")
                                return
                        else:
                            print(f"[WARNING] Return policy {return_policy_id} not found")
        else:
            print("No offers found")
    else:
        print(f"[ERROR] Could not get offers: {response.status_code}")
        print(response.text[:500])
    
    print()
    print("=" * 80)
    print("Could not find return policy from existing listings")
    print("=" * 80)
    print()
    print("You may need to:")
    print("1. Create a return policy manually in eBay Seller Hub")
    print("2. Or check if you have any existing listings with return policies")
    print("3. The return policy ID format is typically a long number")

if __name__ == "__main__":
    main()
