"""
Get offer directly by SKU to extract return policy.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    print("=" * 80)
    print("Get Return Policy from Existing SKUs")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Get inventory items
    print("Getting inventory items...")
    response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 50})
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('inventoryItems', [])
        
        print(f"[OK] Found {len(items)} inventory item(s)")
        print()
        print("Trying to get offers for each SKU...")
        print()
        
        for i, item in enumerate(items[:20], 1):  # Check first 20
            sku = item.get('sku', '')
            if not sku:
                continue
            
            print(f"{i}. Trying SKU: {sku}")
            
            # Try to get offer directly by SKU
            # eBay API: GET /sell/inventory/v1/offer/{offerId}
            # But we don't have offerId, we have SKU
            # Let's try: GET /sell/inventory/v1/offer?sku={sku}
            # Actually, eBay might accept SKU in the path: /sell/inventory/v1/offer/{sku}
            
            # Try path-based first
            try:
                offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{sku}')
                
                if offer_response.status_code == 200:
                    offer_data = offer_response.json()
                    
                    # Check if this offer has a listing ID that matches
                    listing_id = offer_data.get('listingId', '')
                    
                    listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                    root_policies = offer_data.get('listingPolicies', {})
                    
                    return_policy_id = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                    
                    if return_policy_id:
                        print(f"  [OK] Found return policy ID: {return_policy_id}")
                        if listing_id:
                            print(f"  Listing ID: {listing_id}")
                        print()
                        
                        # Update .env
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
                        print(f"  [SKIP] No return policy ID in this offer")
                elif offer_response.status_code == 404:
                    # No offer for this SKU yet
                    pass
                else:
                    # Try query parameter method
                    try:
                        offer_response2 = client._make_request('GET', '/sell/inventory/v1/offer', params={
                            'sku': sku
                        })
                        if offer_response2.status_code == 200:
                            offers_data = offer_response2.json()
                            offers = offers_data.get('offers', [])
                            if offers:
                                offer = offers[0]
                                listing_policies = offer.get('listing', {}).get('listingPolicies', {})
                                return_policy_id = listing_policies.get('returnPolicyId')
                                if return_policy_id:
                                    print(f"  [OK] Found return policy ID: {return_policy_id}")
                                    # Update .env (same code as above)
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
                                        print("Restart Streamlit and try creating the listing again!")
                                        return
                                    except Exception as e:
                                        print(f"[ERROR] Could not update .env: {e}")
                    except:
                        pass
            except Exception as e:
                # Skip if error
                pass
    
    print()
    print("=" * 80)
    print("Could not extract return policy from existing offers")
    print("=" * 80)
    print()
    print("The offers might not exist yet, or the API endpoint format is different.")
    print()
    print("Since you have a working listing (295755540338), the return policy ID")
    print("must exist. The code is now set to try without it, or you can")
    print("manually check the listing details to find the return policy ID.")

if __name__ == "__main__":
    main()
