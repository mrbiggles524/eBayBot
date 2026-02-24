"""
Check the existing offers to see their status and why groups aren't being created.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json

sys.stdout.reconfigure(encoding='utf-8')

def check_offers():
    """Check existing offers."""
    print("=" * 80)
    print("CHECKING EXISTING OFFERS")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get inventory items
    print("Fetching inventory items...")
    response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 200})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    items_data = response.json()
    inventory_items = items_data.get('inventoryItems', [])
    print(f"Found {len(inventory_items)} inventory items")
    print()
    
    # Check offers
    print("Checking offers for each item...")
    print()
    
    offers_with_groups = []
    offers_without_groups = []
    
    for item in inventory_items[:20]:  # Check first 20
        sku = item.get('sku', '')
        if not sku:
            continue
        
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success') and offer_result.get('offer'):
            offer = offer_result['offer']
            group_key = offer.get('inventoryItemGroupKey', '')
            listing_id = offer.get('listingId', '')
            status = offer.get('status', '')
            start_date = offer.get('listingStartDate', '')
            
            offer_info = {
                'sku': sku,
                'group_key': group_key,
                'listing_id': listing_id,
                'status': status,
                'start_date': start_date
            }
            
            if group_key:
                offers_with_groups.append(offer_info)
            else:
                offers_without_groups.append(offer_info)
    
    print(f"Offers WITH groups: {len(offers_with_groups)}")
    print(f"Offers WITHOUT groups: {len(offers_without_groups)}")
    print()
    
    if offers_without_groups:
        print("=" * 80)
        print("OFFERS WITHOUT GROUPS (These won't appear in Seller Hub):")
        print("=" * 80)
        for offer in offers_without_groups:
            print(f"SKU: {offer['sku']}")
            print(f"  Status: {offer['status']}")
            print(f"  Listing ID: {offer['listing_id'] or 'NONE'}")
            print(f"  Group Key: {offer['group_key'] or 'MISSING!'}")
            print()
    
    if offers_with_groups:
        print("=" * 80)
        print("OFFERS WITH GROUPS:")
        print("=" * 80)
        for offer in offers_with_groups:
            print(f"SKU: {offer['sku']}")
            print(f"  Group Key: {offer['group_key']}")
            print(f"  Status: {offer['status']}")
            print(f"  Listing ID: {offer['listing_id'] or 'NONE'}")
            print()
    
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    if len(offers_without_groups) > 0:
        print("❌ PROBLEM FOUND: Offers exist but are NOT linked to groups!")
        print()
        print("This means:")
        print("  1. Inventory items and offers were created")
        print("  2. But group creation FAILED (Error 25016 or 25703)")
        print("  3. Without groups, offers can't be published as variation listings")
        print("  4. They won't appear in Seller Hub")
        print()
        print("SOLUTION:")
        print("  The group creation is failing due to Error 25016 (description) or 25703 (SKU conflict)")
        print("  We need to fix the group creation process to handle these errors better")
    else:
        print("✅ All offers are linked to groups")

if __name__ == "__main__":
    check_offers()
