"""
Check the latest group (GROUPSET1768801675) and verify offers are linked.
"""
import sys
from ebay_api_client import eBayAPIClient

sys.stdout.reconfigure(encoding='utf-8')

def check_group(group_key: str):
    """Check group and verify offers are linked."""
    print("=" * 80)
    print(f"CHECKING GROUP: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get group
    print("1. Getting group...")
    result = client.get_inventory_item_group(group_key)
    
    if not result.get('success'):
        print(f"❌ Group not found: {result.get('error')}")
        return
    
    group_data = result.get('data', {})
    title = group_data.get('title', 'N/A')
    variant_skus = group_data.get('variantSKUs', [])
    
    print(f"✅ Group exists")
    print(f"   Title: {title}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print(f"   SKUs: {variant_skus}")
    print()
    
    # Check each offer
    print("2. Checking offers...")
    offers_linked = 0
    offers_unlinked = 0
    
    for sku in variant_skus:
        offer_result = client.get_offer_by_sku(sku)
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            offer_id = offer.get('offerId')
            group_key_in_offer = offer.get('inventoryItemGroupKey')
            
            if group_key_in_offer == group_key:
                offers_linked += 1
                print(f"   ✅ {sku}: Linked to group (Offer ID: {offer_id})")
            else:
                offers_unlinked += 1
                print(f"   ❌ {sku}: NOT linked! Group in offer: {group_key_in_offer}")
        else:
            offers_unlinked += 1
            print(f"   ❌ {sku}: Could not get offer: {offer_result.get('error')}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total SKUs: {len(variant_skus)}")
    print(f"Linked to group: {offers_linked}")
    print(f"NOT linked: {offers_unlinked}")
    print()
    
    if offers_unlinked > 0:
        print("⚠️ WARNING: Some offers are not linked to the group!")
        print("This means the listing won't appear in Seller Hub.")
        print()
        print("The group exists but offers aren't part of it.")
        print("This is why listings don't appear anywhere.")
    else:
        print("✅ All offers are linked to the group.")
        print("If listing doesn't appear, it's likely Error 25016 preventing publish.")

if __name__ == "__main__":
    group_key = "GROUPSET1768801675"
    check_group(group_key)
