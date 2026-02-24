"""
Get return policy from listing using Browse API.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    listing_id = "295755540338"
    
    print("=" * 80)
    print(f"Get Return Policy from Listing: {listing_id}")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Try Browse API - this is for buyers but might have some info
    print("Trying Browse API...")
    try:
        # Browse API endpoint
        browse_response = client._make_request('GET', f'/buy/browse/v1/item/{listing_id}')
        
        if browse_response.status_code == 200:
            item_data = browse_response.json()
            print("[OK] Got item from Browse API")
            print(f"Title: {item_data.get('title', 'N/A')}")
            
            # Browse API might have return policy info
            # Check for returnTerms or similar
            print(f"Keys in response: {list(item_data.keys())}")
            
            # Look for return policy info
            if 'returnTerms' in item_data:
                print(f"Return terms: {item_data['returnTerms']}")
            if 'seller' in item_data:
                seller = item_data.get('seller', {})
                print(f"Seller info: {list(seller.keys())}")
            
            # Print full response to see what we have
            print("\nFull response (first 2000 chars):")
            print(json.dumps(item_data, indent=2)[:2000])
    except Exception as e:
        print(f"Browse API failed: {e}")
    
    print()
    print("=" * 80)
    print("Since Browse API is for buyers, it might not have policy IDs")
    print("=" * 80)
    print()
    print("Let me try a different approach - query the inventory item group")
    print("that this listing belongs to...")
    print()
    
    # Try to find the inventory item group
    # The listing title is "2022-23 Bowman University Chrome..."
    # Let's try to query groups and find one with a similar title
    
    print("Querying inventory item groups...")
    try:
        # Try to get groups - but the API might not support listing all groups
        # Let's try a different endpoint
        
        # Actually, let me try to use the listing ID to get the offer
        # Maybe the offer endpoint accepts listingId as a parameter
        
        print("Trying to query offers with listingId parameter...")
        offer_response = client._make_request('GET', '/sell/inventory/v1/offer', params={
            'listing_id': listing_id,
            'marketplace_id': 'EBAY_US'
        })
        
        if offer_response.status_code == 200:
            offers_data = offer_response.json()
            offers = offers_data.get('offers', [])
            if offers:
                offer = offers[0]
                offer_id = offer.get('offerId')
                print(f"[OK] Found offer ID: {offer_id}")
                
                # Get full offer
                full_offer = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
                if full_offer.status_code == 200:
                    offer_data = full_offer.json()
                    listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                    return_policy_id = listing_policies.get('returnPolicyId')
                    
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
                            print(f"[OK] Updated .env!")
                            print("Restart Streamlit and try again!")
                            return
                        except Exception as e:
                            print(f"[ERROR] {e}")
        else:
            print(f"Query by listingId failed: {offer_response.status_code}")
            print(offer_response.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
