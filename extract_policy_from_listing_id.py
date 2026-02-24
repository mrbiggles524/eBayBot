"""
Extract return policy ID from a specific listing ID.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    listing_id = "295755540338"
    
    print("=" * 80)
    print(f"Extract Return Policy from Listing ID: {listing_id}")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Try to get the listing via Inventory API
    # First, we need to find the SKU or offer ID for this listing
    
    print("Method 1: Trying to find offer by listing ID...")
    print()
    
    # eBay Inventory API doesn't have a direct "get by listing ID" endpoint
    # But we can try the Trading API or Browse API
    
    # Actually, let's try to get offers and look for this listing ID
    print("Querying offers to find this listing...")
    
    # Try to get offers with limit
    response = client._make_request('GET', '/sell/inventory/v1/offer', params={
        'marketplace_id': 'EBAY_US',
        'limit': 250  # Get more offers
    })
    
    if response.status_code == 200:
        data = response.json()
        offers = data.get('offers', [])
        
        print(f"Found {len(offers)} offer(s)")
        print()
        
        # Look for the listing ID
        found_offer = None
        for offer in offers:
            offer_listing_id = offer.get('listingId', '')
            if str(offer_listing_id) == listing_id:
                found_offer = offer
                break
        
        if found_offer:
            offer_id = found_offer.get('offerId')
            sku = found_offer.get('sku', 'N/A')
            
            print(f"[OK] Found offer for listing {listing_id}")
            print(f"  Offer ID: {offer_id}")
            print(f"  SKU: {sku}")
            print()
            print("Getting full offer details...")
            
            # Get full offer details
            offer_response = client._make_request('GET', f'/sell/inventory/v1/offer/{offer_id}')
            
            if offer_response.status_code == 200:
                offer_data = offer_response.json()
                
                # Extract return policy
                listing_policies = offer_data.get('listing', {}).get('listingPolicies', {})
                root_policies = offer_data.get('listingPolicies', {})
                
                return_policy_id = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                fulfillment_policy_id = listing_policies.get('fulfillmentPolicyId') or root_policies.get('fulfillmentPolicyId')
                payment_policy_id = listing_policies.get('paymentPolicyId') or root_policies.get('paymentPolicyId')
                
                print(f"[OK] Found policies:")
                print(f"  Fulfillment: {fulfillment_policy_id}")
                print(f"  Payment: {payment_policy_id}")
                print(f"  Return: {return_policy_id}")
                print()
                
                if return_policy_id:
                    print("Updating .env file with return policy ID...")
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
                        print(f"Updated .env with RETURN_POLICY_ID={return_policy_id}")
                        print()
                        print("Restart Streamlit and try creating the listing again!")
                        return
                    except Exception as e:
                        print(f"[ERROR] Could not update .env: {e}")
                else:
                    print("[WARNING] No return policy ID found in offer")
                    print("Full offer data:")
                    print(json.dumps(offer_data, indent=2)[:1000])
            else:
                print(f"[ERROR] Could not get offer details: {offer_response.status_code}")
                print(offer_response.text[:500])
        else:
            print(f"[WARNING] Listing ID {listing_id} not found in offers")
            print()
            print("Trying alternative method - query by SKU pattern...")
            print("(This listing might be published and not in draft offers)")
    else:
        print(f"[ERROR] Could not get offers: {response.status_code}")
        print(response.text[:500])
        print()
        print("Trying alternative: Use Trading API to get item details...")
        
        # Try Trading API
        try:
            trading_response = client._make_request('GET', '/Trading', params={
                'callname': 'GetItem',
                'version': '967',
                'ItemID': listing_id,
                'DetailLevel': 'ReturnAll'
            })
            
            if trading_response.status_code == 200:
                print("[OK] Got response from Trading API")
                print(trading_response.text[:500])
        except Exception as e:
            print(f"[ERROR] Trading API failed: {e}")

if __name__ == "__main__":
    main()
