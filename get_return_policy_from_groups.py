"""
Get return policy ID from existing inventory item groups.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    print("=" * 80)
    print("Extract Return Policy from Inventory Item Groups")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print("Querying inventory item groups...")
    print()
    
    # Get inventory item groups
    response = client._make_request('GET', '/sell/inventory/v1/inventory_item_group', params={'limit': 50})
    
    if response.status_code == 200:
        data = response.json()
        groups = data.get('inventoryItemGroups', [])
        
        if groups:
            print(f"[OK] Found {len(groups)} inventory item group(s)")
            print()
            
            for group in groups:
                group_key = group.get('inventoryItemGroupKey', 'N/A')
                title = group.get('title', 'N/A')
                variant_skus = group.get('variantSKUs', [])
                
                print(f"Checking group: {title}")
                print(f"  Group Key: {group_key}")
                print(f"  Variant SKUs: {len(variant_skus)}")
                
                # Get first SKU and check its offer
                if variant_skus:
                    first_sku = variant_skus[0]
                    print(f"  Checking offer for SKU: {first_sku}")
                    
                    # Try to get offer by SKU - need to query offers
                    # Actually, let's try to get the group details which might have offer info
                    group_response = client._make_request('GET', f'/sell/inventory/v1/inventory_item_group/{group_key}')
                    
                    if group_response.status_code == 200:
                        group_data = group_response.json()
                        # Group data might not have offers, need to query offers separately
                        
                        # Try to get offers - but we need offer IDs or SKUs
                        # Let's try a different approach - query offers with a known SKU pattern
                        print(f"  Querying offers for SKU: {first_sku}")
                        
                        # eBay API doesn't let us query by SKU directly, but we can try to get offer by SKU
                        # Actually, the offer endpoint might accept SKU as a parameter
                        offer_response = client._make_request('GET', f'/sell/inventory/v1/offer', params={
                            'sku': first_sku,
                            'marketplace_id': 'EBAY_US'
                        })
                        
                        if offer_response.status_code == 200:
                            offers_data = offer_response.json()
                            offers = offers_data.get('offers', [])
                            
                            if offers:
                                # Get first offer details
                                offer = offers[0]
                                offer_id = offer.get('offerId')
                                
                                if offer_id:
                                    print(f"  Found offer ID: {offer_id}")
                                    print(f"  Getting full offer details...")
                                    
                                    full_offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
                                    
                                    if full_offer_response.status_code == 200:
                                        offer_data = full_offer_response.json()
                                        
                                        # Check for return policy
                                        listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                                        root_policies = offer_data.get('listingPolicies', {})
                                        
                                        return_policy_id = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                                        
                                        if return_policy_id:
                                            print(f"  [OK] Found return policy ID: {return_policy_id}")
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
                                            print(f"  [WARNING] No return policy ID in offer")
                                    else:
                                        print(f"  [ERROR] Could not get offer details: {full_offer_response.status_code}")
                            else:
                                print(f"  [WARNING] No offers found for SKU")
                        else:
                            print(f"  [WARNING] Could not query offers: {offer_response.status_code}")
                            # Try alternative - maybe we can get it from the group's published listing
                            print(f"  Trying alternative approach...")
                            
                            # Maybe the group has a published listing we can query
                            # But we'd need the listing ID which we don't have
                            
        else:
            print("[WARNING] No inventory item groups found")
            print()
            print("Trying to query offers directly...")
            
            # Try to get any offers
            offers_response = client._make_request('GET', '/sell/inventory/v1/offer', params={
                'marketplace_id': 'EBAY_US',
                'limit': 10
            })
            
            if offers_response.status_code == 200:
                offers_data = offers_response.json()
                offers = offers_data.get('offers', [])
                
                if offers:
                    print(f"[OK] Found {len(offers)} offer(s)")
                    print()
                    
                    # Check first offer
                    offer = offers[0]
                    offer_id = offer.get('offerId')
                    
                    if offer_id:
                        print(f"Getting details for offer: {offer_id}")
                        full_offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
                        
                        if full_offer_response.status_code == 200:
                            offer_data = full_offer_response.json()
                            
                            listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                            root_policies = offer_data.get('listingPolicies', {})
                            
                            return_policy_id = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                            
                            if return_policy_id:
                                print(f"[OK] Found return policy ID: {return_policy_id}")
                                
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
                                    print("Restart Streamlit and try creating the listing again!")
                                    return
                                except Exception as e:
                                    print(f"[ERROR] Could not update .env: {e}")
    else:
        print(f"[ERROR] Could not get inventory item groups: {response.status_code}")
        print(response.text[:500])
    
    print()
    print("=" * 80)
    print("Could not extract return policy")
    print("=" * 80)
    print()
    print("Trying one more thing - omitting return policy to see if eBay accepts it...")
    print("(This will likely fail, but we'll see the exact error)")

if __name__ == "__main__":
    main()
