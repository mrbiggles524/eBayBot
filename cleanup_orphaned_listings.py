"""
Clean up orphaned listings that aren't visible in Seller Hub.
This will delete offers and groups that exist in the API but aren't published.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import time

sys.stdout.reconfigure(encoding='utf-8')

def cleanup_orphaned_listings():
    """Clean up orphaned offers and groups."""
    print("=" * 80)
    print("CLEANING UP ORPHANED LISTINGS")
    print("=" * 80)
    print()
    print("This will:")
    print("1. Find all inventory items")
    print("2. Check their offers")
    print("3. Delete offers without listingId (unpublished)")
    print("4. Delete groups with no published offers")
    print()
    
    client = eBayAPIClient()
    config = Config()
    
    # Get all inventory items
    print("Step 1: Getting all inventory items...")
    inventory_result = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 200})
    
    if inventory_result.status_code != 200:
        print(f"❌ Failed to get inventory items: {inventory_result.status_code}")
        print(f"   Response: {inventory_result.text[:200]}")
        return
    
    inventory_data = inventory_result.json()
    inventory_items = inventory_data.get('inventoryItems', [])
    print(f"✅ Found {len(inventory_items)} inventory items")
    print()
    
    # Get all offers by iterating through inventory items
    print("Step 2: Getting all offers from inventory items...")
    all_offers = []
    for item in inventory_items:
        sku = item.get('sku')
        if sku:
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success') and offer_result.get('offer'):
                all_offers.append(offer_result.get('offer'))
    
    print(f"✅ Found {len(all_offers)} offers")
    print()
    
    # Find unpublished offers (no listingId)
    print("Step 3: Finding unpublished offers...")
    unpublished_offers = []
    for offer in all_offers:
        listing_id = offer.get('listingId')
        if not listing_id:
            unpublished_offers.append(offer)
    
    print(f"✅ Found {len(unpublished_offers)} unpublished offers")
    print()
    
    if not unpublished_offers:
        print("✅ No orphaned offers to clean up!")
        return
    
    # Show what will be deleted
    print("Unpublished offers to delete:")
    for i, offer in enumerate(unpublished_offers[:10], 1):
        sku = offer.get('sku', 'N/A')
        offer_id = offer.get('offerId', 'N/A')
        group_key = offer.get('inventoryItemGroupKey', 'None')
        print(f"  {i}. SKU: {sku}, Offer ID: {offer_id}, Group: {group_key}")
    if len(unpublished_offers) > 10:
        print(f"  ... and {len(unpublished_offers) - 10} more")
    print()
    
    # Auto-delete without confirmation (user requested cleanup)
    print("⚠️ WARNING: Deleting all unpublished offers...")
    print("   These offers are not visible in Seller Hub and cannot be published.")
    print()
    
    # Delete unpublished offers
    print()
    print("Step 4: Deleting unpublished offers...")
    deleted_count = 0
    failed_count = 0
    
    for offer in unpublished_offers:
        offer_id = offer.get('offerId')
        sku = offer.get('sku', 'N/A')
        
        if offer_id:
            delete_result = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
            if delete_result.status_code in [200, 204]:
                deleted_count += 1
                print(f"  ✅ Deleted offer {sku} (ID: {offer_id})")
            else:
                failed_count += 1
                print(f"  ❌ Failed to delete {sku}: {delete_result.status_code}")
            time.sleep(0.5)  # Rate limiting
    
    print()
    print(f"✅ Deleted {deleted_count} offers")
    if failed_count > 0:
        print(f"⚠️ Failed to delete {failed_count} offers")
    print()
    
    # Now find and delete orphaned groups
    print("Step 5: Finding orphaned groups...")
    # Get all groups (we'll need to check each one)
    groups_to_check = []
    for offer in all_offers:
        group_key = offer.get('inventoryItemGroupKey')
        if group_key and group_key not in groups_to_check:
            groups_to_check.append(group_key)
    
    print(f"Found {len(groups_to_check)} groups to check")
    print()
    
    orphaned_groups = []
    for group_key in groups_to_check:
        # Check if any offers in this group have listingId
        has_published = False
        for offer in all_offers:
            if offer.get('inventoryItemGroupKey') == group_key:
                if offer.get('listingId'):
                    has_published = True
                    break
        
        if not has_published:
            orphaned_groups.append(group_key)
    
    print(f"Found {len(orphaned_groups)} orphaned groups (no published offers)")
    print()
    
    if orphaned_groups:
        print("Orphaned groups to delete:")
        for i, group_key in enumerate(orphaned_groups[:10], 1):
            print(f"  {i}. {group_key}")
        if len(orphaned_groups) > 10:
            print(f"  ... and {len(orphaned_groups) - 10} more")
        print()
        
        # Auto-delete orphaned groups
        print("Deleting orphaned groups...")
        if True:
            deleted_groups = 0
            for group_key in orphaned_groups:
                delete_result = client._make_request('DELETE', f'/sell/inventory/v1/inventory_item_group/{group_key}')
                if delete_result.status_code in [200, 204]:
                    deleted_groups += 1
                    print(f"  ✅ Deleted group {group_key}")
                else:
                    print(f"  ❌ Failed to delete {group_key}: {delete_result.status_code}")
                time.sleep(0.5)
            
            print()
            print(f"✅ Deleted {deleted_groups} orphaned groups")
    
    print()
    print("=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Deleted {deleted_count} unpublished offers")
    print(f"  - Deleted {len(orphaned_groups) if 'orphaned_groups' in locals() else 0} orphaned groups")
    print()
    print("You can now create fresh listings.")

if __name__ == "__main__":
    cleanup_orphaned_listings()
