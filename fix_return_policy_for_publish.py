"""
Fix return policy issue so listings can be published.
Removes invalid return policy from offers.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config

def fix_return_policy(sku: str = None):
    """Fix return policy for a specific SKU or all drafts."""
    print("=" * 80)
    print("Fixing Return Policy for Publishing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    if sku:
        # Fix specific SKU
        skus_to_fix = [sku]
        print(f"Fixing SKU: {sku}")
    else:
        # Get all inventory items
        print("Finding all draft listings...")
        items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
        
        if items_response.status_code != 200:
            print(f"[ERROR] Failed to fetch inventory items: {items_response.status_code}")
            return
        
        items_data = items_response.json()
        inventory_items = items_data.get('inventoryItems', [])
        
        # Get offers and find drafts
        skus_to_fix = []
        for item in inventory_items:
            item_sku = item.get('sku')
            if item_sku:
                offer_result = client.get_offer_by_sku(item_sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offer = offer_result['offer']
                    if not offer.get('listingId'):  # Draft
                        skus_to_fix.append(item_sku)
        
        print(f"Found {len(skus_to_fix)} draft listings to fix")
    
    print()
    
    fixed_count = 0
    for sku in skus_to_fix:
        print(f"Processing: {sku}")
        
        # Get the offer
        offer_result = client.get_offer_by_sku(sku)
        if not offer_result.get('success') or not offer_result.get('offer'):
            print(f"  [SKIP] Could not get offer")
            continue
        
        offer = offer_result['offer']
        offer_id = offer.get('offerId')
        listing_id = offer.get('listingId')
        
        if listing_id:
            print(f"  [SKIP] Already published (Listing ID: {listing_id})")
            continue
        
        print(f"  Offer ID: {offer_id}")
        
        # Get current data
        listing_data = offer.get('listing', {})
        listing_policies = offer.get('listingPolicies', {})
        
        # Remove invalid return policy
        if 'returnPolicyId' in listing_policies:
            invalid_policy = listing_policies.pop('returnPolicyId')
            print(f"  [FIX] Removing invalid return policy: {invalid_policy}")
        
        # Build update payload without return policy
        update_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
            "pricingSummary": offer.get('pricingSummary', {}),
            "listingPolicies": listing_policies,  # Without return policy
            "categoryId": offer.get('categoryId'),
            "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
            "listing": {
                "title": listing_data.get('title', ''),
                "description": listing_data.get('description', ''),
                "listingPolicies": listing_policies,  # Also update in listing
                "imageUrls": listing_data.get('imageUrls', []) or []
            }
        }
        
        # Include itemSpecifics if they exist
        if 'itemSpecifics' in listing_data:
            update_data['listing']['itemSpecifics'] = listing_data['itemSpecifics']
        
        # Update the offer
        print(f"  [UPDATE] Removing return policy from offer...")
        update_result = client.update_offer(offer_id, update_data)
        
        if update_result.get('success'):
            print(f"  [OK] Fixed! Return policy removed")
            fixed_count += 1
        else:
            error = update_result.get('error', 'Unknown error')
            print(f"  [ERROR] Failed: {error}")
        
        print()
    
    print("=" * 80)
    print(f"[SUCCESS] Fixed {fixed_count} listing(s)")
    print("=" * 80)
    print()
    print("[NOTE] eBay may still require a return policy for publishing.")
    print("   You may need to:")
    print("   1. Create a valid return policy in Seller Hub")
    print("   2. Or use the Streamlit UI to auto-configure policies")
    print()
    print("Now try publishing again:")
    if sku:
        print(f"   python publish_draft.py {sku}")
    else:
        print("   python publish_draft.py <SKU>")

if __name__ == "__main__":
    sku = sys.argv[1] if len(sys.argv) > 1 else None
    fix_return_policy(sku)
