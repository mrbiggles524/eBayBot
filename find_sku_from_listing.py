"""
Try to find SKUs from the listing by querying inventory items.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    listing_id = "295755540338"
    
    print("=" * 80)
    print(f"Find SKU from Listing: {listing_id}")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Try to get inventory items - maybe we can find ones related to this listing
    print("Querying inventory items...")
    print()
    
    # Try to get inventory items with limit
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={
            'limit': 100
        })
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('inventoryItems', [])
            
            print(f"[OK] Found {len(items)} inventory item(s)")
            print()
            
            if items:
                # Get the first few items and check their offers
                print("Checking first few items for offers...")
                print()
                
                for i, item in enumerate(items[:10], 1):  # Check first 10
                    sku = item.get('sku', 'N/A')
                    print(f"{i}. Checking SKU: {sku}")
                    
                    # Try to get offer for this SKU
                    # eBay API doesn't have direct "get offer by SKU" but we can try
                    # Actually, let's try to get the offer using the SKU in the path
                    try:
                        offer_response = client._make_request('GET', f'/sell/inventory/v1/offer', params={
                            'sku': sku,
                            'marketplace_id': 'EBAY_US'
                        })
                        
                        if offer_response.status_code == 200:
                            offers_data = offer_response.json()
                            offers = offers_data.get('offers', [])
                            
                            if offers:
                                offer = offers[0]
                                offer_listing_id = offer.get('listingId', '')
                                
                                if str(offer_listing_id) == listing_id:
                                    print(f"  [OK] Found matching listing!")
                                    print(f"  Offer ID: {offer.get('offerId')}")
                                    
                                    # Get full offer details
                                    offer_id = offer.get('offerId')
                                    full_offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
                                    
                                    if full_offer_response.status_code == 200:
                                        offer_data = full_offer_response.json()
                                        
                                        listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                                        root_policies = offer_data.get('listingPolicies', {})
                                        
                                        return_policy_id = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                                        
                                        if return_policy_id:
                                            print(f"  [OK] Found return policy ID: {return_policy_id}")
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
                            # Offer query failed, but that's OK - not all items have offers
                            pass
                    except Exception as e:
                        # Skip if we can't query this SKU
                        pass
                    
                    print()
        else:
            print(f"[ERROR] Could not get inventory items: {response.status_code}")
            print(response.text[:500])
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Could not find SKU automatically")
    print("=" * 80)
    print()
    print("I need either:")
    print("1. A SKU from one of the variations in this listing")
    print("2. Or the inventory item group key")
    print()
    print("You can find a SKU by:")
    print("- Looking at the listing page source code")
    print("- Or checking your inventory items list")
    print("- Or providing any SKU pattern you know (like CARD_* or similar)")

if __name__ == "__main__":
    main()
