"""
Diagnostic script to check if group description is actually stored in eBay.
This will help us understand why Error 25016 keeps occurring.
"""
import sys
from ebay_api_client import eBayAPIClient
import json

def diagnose_group(group_key: str):
    """Diagnose a group to see what eBay actually has stored."""
    print("=" * 80)
    print(f"DIAGNOSING GROUP: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get group
    print("1. Getting group via GET endpoint...")
    result = client.get_inventory_item_group(group_key)
    
    if not result.get('success'):
        print(f"❌ Failed to get group: {result.get('error')}")
        return
    
    group_data = result.get('data', {})
    print(f"✅ Group retrieved")
    print(f"   Group keys: {list(group_data.keys())}")
    print()
    
    # Check structure
    print("2. Checking group structure...")
    if 'inventoryItemGroup' in group_data:
        inv_group = group_data['inventoryItemGroup']
        print(f"✅ inventoryItemGroup found")
        print(f"   Keys: {list(inv_group.keys())}")
        
        if 'description' in inv_group:
            desc = inv_group['description']
            print(f"✅ Description found in GET response!")
            print(f"   Length: {len(desc)}")
            print(f"   Preview: {desc[:100]}...")
        else:
            print(f"❌ Description NOT in GET response")
            print(f"   This is normal - eBay GET may not return description")
    else:
        print(f"❌ inventoryItemGroup NOT in GET response")
        print(f"   This is a known eBay API quirk")
    print()
    
    # Try to update and see what happens
    print("3. Attempting to update group with description...")
    title = group_data.get('title', 'Variation Listing')
    desc = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    update_payload = {
        "title": title,
        "variesBy": group_data.get('variesBy', {}),
        "inventoryItemGroup": {
            "aspects": group_data.get('inventoryItemGroup', {}).get('aspects', {}),
            "description": desc
        },
        "variantSKUs": group_data.get('variantSKUs', [])
    }
    
    print(f"   Sending update with description (length: {len(desc)})...")
    update_result = client.create_inventory_item_group(group_key, update_payload)
    
    if update_result.get('success'):
        print(f"✅ Update succeeded (204)")
        print(f"   Waiting 10 seconds for propagation...")
        import time
        time.sleep(10)
        
        # Check again
        print()
        print("4. Checking group again after update...")
        check_result = client.get_inventory_item_group(group_key)
        if check_result.get('success'):
            check_data = check_result.get('data', {})
            if 'inventoryItemGroup' in check_data:
                check_desc = check_data['inventoryItemGroup'].get('description', '')
                if check_desc:
                    print(f"✅ Description now in GET response!")
                    print(f"   Length: {len(check_desc)}")
                else:
                    print(f"⚠️  Description still not in GET response")
                    print(f"   But update succeeded, so it should be stored")
            else:
                print(f"⚠️  inventoryItemGroup still not in GET response")
                print(f"   This is normal - eBay GET doesn't return it")
        else:
            print(f"❌ Could not check group: {check_result.get('error')}")
    else:
        print(f"❌ Update failed: {update_result.get('error')}")
    
    print()
    print("=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)
    print()
    print("CONCLUSION:")
    print("- If update succeeds (204), description should be stored")
    print("- If GET doesn't return it, that's a known eBay API quirk")
    print("- The description should still be there when publishing")
    print()
    print("If Error 25016 persists, it may be an eBay sandbox issue")
    print("or the description needs to be in a different format/location")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_group_description.py <group_key>")
        sys.exit(1)
    
    group_key = sys.argv[1]
    diagnose_group(group_key)
