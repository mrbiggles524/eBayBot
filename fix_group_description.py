"""
Fix a group's description to ensure it's valid.
"""
import sys
from ebay_api_client import eBayAPIClient
import re

sys.stdout.reconfigure(encoding='utf-8')

def fix_group_description(group_key):
    """Fix group description to be valid."""
    print("=" * 80)
    print(f"FIXING GROUP DESCRIPTION: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get current group
    print("Step 1: Getting current group...")
    result = client.get_inventory_item_group(group_key)
    
    if not result.get('success'):
        print(f"❌ Group not found: {result.get('error')}")
        return
    
    group_data = result.get('data', {})
    title = group_data.get('title', 'Variation Listing')
    varies_by = group_data.get('variesBy', {})
    variant_skus = group_data.get('variantSKUs', [])
    
    print(f"✅ Group found: {title}")
    print(f"   Variant SKUs: {len(variant_skus)}")
    print()
    
    # Get aspects from offers if needed
    aspects = {}
    if variant_skus:
        print("Step 2: Getting aspects from first offer...")
        offer_result = client.get_offer_by_sku(variant_skus[0])
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            listing = offer.get('listing', {})
            item_specifics = listing.get('itemSpecifics', {})
            if item_specifics:
                # Extract variation aspect
                for key, value in item_specifics.items():
                    if isinstance(value, list) and len(value) > 0:
                        aspects[key] = value
                print(f"   Found aspects: {list(aspects.keys())}")
    
    # Create a guaranteed valid description
    print()
    print("Step 3: Creating guaranteed valid description...")
    valid_description = f"""{title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
    
    print(f"   Description length: {len(valid_description)}")
    print(f"   Description preview: {valid_description[:100]}...")
    print()
    
    # Build update payload
    print("Step 4: Building update payload...")
    update_data = {
        "title": title,
        "variesBy": varies_by,
        "inventoryItemGroup": {
            "aspects": aspects,
            "description": valid_description
        },
        "variantSKUs": variant_skus
    }
    
    print(f"   Title: {title}")
    print(f"   Has inventoryItemGroup: True")
    print(f"   Has description: True (length: {len(valid_description)})")
    print()
    
    # Update the group
    print("Step 5: Updating group with valid description...")
    update_result = client.create_inventory_item_group(group_key, update_data)
    
    if update_result.get('success'):
        print("✅ Group updated successfully!")
        print()
        print("Step 6: Verifying update...")
        verify_result = client.get_inventory_item_group(group_key)
        if verify_result.get('success'):
            print("✅ Group verified - description should now be valid")
            print()
            print("The group now has a valid description and should be publishable.")
            print("Try publishing it again or check Seller Hub.")
        else:
            print(f"⚠️ Could not verify: {verify_result.get('error')}")
    else:
        print(f"❌ Update failed: {update_result.get('error')}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fix_group_description.py <group_key>")
        print("Example: python fix_group_description.py GROUPSET1768868451")
        sys.exit(1)
    
    fix_group_description(sys.argv[1])
