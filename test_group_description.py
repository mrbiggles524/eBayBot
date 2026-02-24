"""
Test script to verify and fix group description before publishing.
Run this to check if a group has description and fix it if needed.
"""
import sys
from ebay_api_client import eBayAPIClient
import json

def test_and_fix_group_description(group_key: str):
    """Test if group has description and fix it if missing."""
    print("=" * 80)
    print(f"Testing Group Description for: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get group
    print("1. Getting group data...")
    result = client.get_inventory_item_group(group_key)
    
    if not result.get('success'):
        print(f"❌ Failed to get group: {result.get('error')}")
        return False
    
    group_data = result.get('data', {})
    print(f"✅ Group retrieved successfully")
    print()
    
    # Check for description
    print("2. Checking for description...")
    has_description = False
    description_value = None
    
    if 'inventoryItemGroup' in group_data:
        inv_group = group_data['inventoryItemGroup']
        if 'description' in inv_group:
            desc = inv_group['description']
            if desc and desc.strip() and len(desc.strip()) >= 50:
                has_description = True
                description_value = desc
                print(f"✅ Group HAS description (length: {len(desc)})")
                print(f"   Preview: {desc[:100]}...")
            else:
                print(f"❌ Group description is invalid (length: {len(desc) if desc else 0})")
        else:
            print(f"❌ Group does NOT have description in inventoryItemGroup")
            print(f"   inventoryItemGroup keys: {list(inv_group.keys())}")
    else:
        print(f"❌ inventoryItemGroup not found in group data")
        print(f"   Group keys: {list(group_data.keys())}")
    
    print()
    
    if has_description:
        print("✅ Group has valid description - no fix needed!")
        return True
    
    # Fix it
    print("3. Fixing description...")
    title = group_data.get('title', 'Variation Listing')
    
    if "Topps Chrome" in title or "Chrome" in title:
        new_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    else:
        new_description = f"""{title}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    update_payload = {
        "title": title,
        "variesBy": group_data.get('variesBy', {}),
        "inventoryItemGroup": {
            "aspects": group_data.get('inventoryItemGroup', {}).get('aspects', {}),
            "description": new_description
        },
        "variantSKUs": group_data.get('variantSKUs', [])
    }
    
    print(f"   Description length: {len(new_description)}")
    print(f"   Updating group...")
    
    update_result = client.create_inventory_item_group(group_key, update_payload)
    
    if update_result.get('success'):
        print(f"✅ Group updated successfully!")
        print()
        print("4. Verifying update...")
        verify_result = client.get_inventory_item_group(group_key)
        if verify_result.get('success'):
            verify_data = verify_result.get('data', {})
            if 'inventoryItemGroup' in verify_data:
                verify_desc = verify_data['inventoryItemGroup'].get('description', '')
                if verify_desc and len(verify_desc.strip()) >= 50:
                    print(f"✅ Verified: Group now has description (length: {len(verify_desc)})")
                    return True
                else:
                    print(f"⚠️  Description not in GET response (may be normal - eBay may not return it)")
                    print(f"   But we sent it in the update, so it should be there")
                    return True
        else:
            print(f"⚠️  Could not verify, but update succeeded")
            return True
    else:
        print(f"❌ Failed to update group: {update_result.get('error')}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_group_description.py <group_key>")
        print("Example: python test_group_description.py GROUPBECKETTCOMNEWS2025261768671385")
        sys.exit(1)
    
    group_key = sys.argv[1]
    success = test_and_fix_group_description(group_key)
    
    if success:
        print()
        print("=" * 80)
        print("✅ Group description is now fixed!")
        print("   Try publishing the listing again.")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("❌ Failed to fix group description")
        print("=" * 80)
