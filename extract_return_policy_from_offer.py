"""
Try to extract return policy ID from an existing offer by SKU.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    print("=" * 80)
    print("Extract Return Policy from Existing Offer")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Try to get a specific offer by SKU (use a known SKU if available)
    # Or try to list offers differently
    
    print("Attempting to get offers...")
    print()
    
    # Try different approaches to get offers
    approaches = [
        ("GET /sell/inventory/v1/offer", {}),
        ("GET /sell/inventory/v1/offer with limit", {"limit": 5}),
        ("GET /sell/inventory/v1/offer with marketplace", {"marketplace_id": "EBAY_US", "limit": 5}),
    ]
    
    for approach_name, params in approaches:
        print(f"Trying: {approach_name}")
        try:
            response = client._make_request('GET', '/sell/inventory/v1/offer', params=params)
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('offers', [])
                
                if offers:
                    print(f"[OK] Found {len(offers)} offer(s)")
                    print()
                    
                    # Get full details of first offer
                    first_offer = offers[0]
                    offer_id = first_offer.get('offerId')
                    
                    if offer_id:
                        print(f"Getting full details for offer: {offer_id}")
                        offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
                        
                        if offer_response.status_code == 200:
                            offer_data = offer_response.json()
                            
                            # Check for return policy in different locations
                            listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                            root_policies = offer_data.get('listingPolicies', {})
                            
                            return_policy_id = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                            
                            if return_policy_id:
                                print(f"[OK] Found return policy ID: {return_policy_id}")
                                print()
                                
                                # Verify it
                                verify_response = client._make_request('GET', f'/sell/account/v1/return_policy/{return_policy_id}')
                                if verify_response.status_code == 200:
                                    policy = verify_response.json()
                                    print(f"[OK] Return policy is valid!")
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
                                        else:
                                            env_content += f"\nRETURN_POLICY_ID={return_policy_id}\n"
                                        
                                        with open('.env', 'w', encoding='utf-8') as f:
                                            f.write(env_content)
                                        
                                        print(f"[OK] Updated .env with RETURN_POLICY_ID={return_policy_id}")
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
                                    print(f"[WARNING] Return policy {return_policy_id} not verifiable via API")
                                    print("But it's being used in an offer, so it might work in listings")
                                    print()
                                    
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
                                        print("(Even though API can't verify it, it's used in existing offers)")
                                        print()
                                        print("Restart Streamlit and try creating the listing again!")
                                        return
                                    except Exception as e:
                                        print(f"[ERROR] Could not update .env: {e}")
                            else:
                                print("[WARNING] No return policy ID found in offer")
                                print(f"Offer data keys: {list(offer_data.keys())}")
                                if 'listing' in offer_data:
                                    print(f"Listing keys: {list(offer_data['listing'].keys())}")
                        else:
                            print(f"[ERROR] Could not get offer details: {response.status_code}")
                else:
                    print("[WARNING] No offers found")
            else:
                print(f"[ERROR] HTTP {response.status_code}")
                if response.status_code != 400:  # Don't print for expected 400s
                    print(response.text[:300])
        except Exception as e:
            print(f"[ERROR] Exception: {e}")
        
        print()
    
    print("=" * 80)
    print("Could not extract return policy from offers")
    print("=" * 80)
    print()
    print("Since return policies can't be created via API in sandbox,")
    print("and we can't find existing ones, you may need to:")
    print()
    print("1. Get the return policy ID from a working listing manually")
    print("2. Check eBay Seller Hub for the return policy ID")
    print("3. The ID might be in a different format than expected")

if __name__ == "__main__":
    main()
