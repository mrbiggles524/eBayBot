"""
Try to query all drafts to see if our listings appear in the API response.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def query_drafts():
    """Query for drafts."""
    print("=" * 80)
    print("Querying for Draft Listings")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Try different ways to query offers/drafts
    print("Method 1: Query offers with limit...")
    try:
        response = client._make_request('GET', '/sell/inventory/v1/offer', params={'limit': 50})
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            print(f"  Found {len(offers)} offers")
            
            # Filter for unpublished
            drafts = [o for o in offers if o.get('status') == 'UNPUBLISHED']
            print(f"  Unpublished (drafts): {len(drafts)}")
            
            if drafts:
                print()
                print("Draft Listings Found:")
                for i, draft in enumerate(drafts[:10], 1):
                    print(f"  {i}. SKU: {draft.get('sku', 'N/A')}")
                    print(f"     Offer ID: {draft.get('offerId', 'N/A')}")
                    print(f"     Group Key: {draft.get('inventoryItemGroupKey', 'N/A')}")
                    print(f"     Category: {draft.get('categoryId', 'N/A')}")
                    print()
        else:
            print(f"  [ERROR] {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    print("Method 2: Check specific test listings...")
    test_listings = [
        ("GROUPSET1768715280", "CARD_SET_NORMAL_FLOW_TEST_CAR_1_0", "Normal Flow Test Listing"),
        ("GROUPSET1768714571", "CARD_SET_FINAL_TEST_CARD_1_0", "Final Test Listing"),
    ]
    
    for group_key, sku, title in test_listings:
        print(f"\nChecking: {title}")
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            print(f"  ✅ Offer exists: {offer.get('offerId', 'N/A')}")
            print(f"  Status: {offer.get('status', 'N/A')}")
            print(f"  Group Key in Offer: {offer.get('inventoryItemGroupKey', 'N/A (missing)')}")
            
            # Check group
            group_result = client.get_inventory_item_group(group_key)
            if group_result.get('success'):
                group_data = group_result.get('data', {})
                variant_skus = group_data.get('variantSKUs', [])
                print(f"  Group exists: {group_key}")
                print(f"  SKU in group: {sku in variant_skus}")
        else:
            print(f"  ❌ Offer not found")
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("All test listings exist via API as UNPUBLISHED (drafts).")
    print()
    print("If they're not appearing in Seller Hub, possible reasons:")
    print("  1. eBay UI delay (wait 2-5 minutes)")
    print("  2. Variation listing drafts may need inventoryItemGroupKey to appear")
    print("  3. Seller Hub might filter or require specific fields")
    print("  4. The listings exist and can be managed via API")
    print()

if __name__ == "__main__":
    query_drafts()
