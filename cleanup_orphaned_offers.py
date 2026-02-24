"""
Clean up orphaned offers that don't have group keys.
These offers can't be published and won't appear in Seller Hub.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config

sys.stdout.reconfigure(encoding='utf-8')

def cleanup_orphaned_offers():
    """Delete offers that don't have group keys."""
    print("=" * 80)
    print("CLEANUP ORPHANED OFFERS")
    print("=" * 80)
    print()
    print("This will delete offers that don't have group keys.")
    print("These offers can't be published and won't appear in Seller Hub.")
    print()
    
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    client = eBayAPIClient()
    
    # Get inventory items
    print("\nFetching inventory items...")
    response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 200})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    items_data = response.json()
    inventory_items = items_data.get('inventoryItems', [])
    print(f"Found {len(inventory_items)} inventory items")
    print()
    
    # Find orphaned offers
    orphaned_offers = []
    
    print("Checking offers...")
    for item in inventory_items:
        sku = item.get('sku', '')
        if not sku:
            continue
        
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success') and offer_result.get('offer'):
            offer = offer_result['offer']
            group_key = offer.get('inventoryItemGroupKey', '')
            listing_id = offer.get('listingId', '')
            
            # Orphaned if no group key and no listing ID (unpublished)
            if not group_key and not listing_id:
                offer_id = offer.get('offerId', '')
                if offer_id:
                    orphaned_offers.append({
                        'sku': sku,
                        'offer_id': offer_id,
                        'title': offer.get('listing', {}).get('title', 'N/A')
                    })
    
    print(f"\nFound {len(orphaned_offers)} orphaned offers")
    print()
    
    if not orphaned_offers:
        print("✅ No orphaned offers found!")
        return
    
    print("Orphaned offers:")
    for i, offer in enumerate(orphaned_offers, 1):
        print(f"  {i}. SKU: {offer['sku']}")
        print(f"     Offer ID: {offer['offer_id']}")
        print(f"     Title: {offer['title']}")
    print()
    
    confirm2 = input(f"Delete {len(orphaned_offers)} orphaned offers? (yes/no): ")
    if confirm2.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Delete orphaned offers
    print("\nDeleting orphaned offers...")
    deleted = 0
    failed = 0
    
    for offer in orphaned_offers:
        try:
            delete_response = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer["offer_id"]}')
            if delete_response.status_code in [200, 204]:
                print(f"  ✅ Deleted: {offer['sku']}")
                deleted += 1
            else:
                print(f"  ❌ Failed: {offer['sku']} - {delete_response.status_code}")
                failed += 1
        except Exception as e:
            print(f"  ❌ Error deleting {offer['sku']}: {e}")
            failed += 1
    
    print()
    print("=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"Deleted: {deleted}")
    print(f"Failed: {failed}")
    print()
    print("Now try creating a new listing - it should work better!")

if __name__ == "__main__":
    cleanup_orphaned_offers()
