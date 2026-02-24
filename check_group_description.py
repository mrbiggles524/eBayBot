"""
Check if a group has a description.
"""
import sys
from ebay_api_client import eBayAPIClient

sys.stdout.reconfigure(encoding='utf-8')

def check_group(group_key):
    """Check group description."""
    print("=" * 80)
    print(f"CHECKING GROUP: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    result = client.get_inventory_item_group(group_key)
    
    if not result.get('success'):
        print(f"❌ Group not found: {result.get('error')}")
        return
    
    group_data = result.get('data', {})
    
    print(f"✅ Group found")
    print(f"   Title: {group_data.get('title', 'N/A')}")
    print()
    
    # Check for description
    inv_group = group_data.get('inventoryItemGroup', {})
    if inv_group:
        desc = inv_group.get('description', '')
        if desc:
            print(f"✅ Description found!")
            print(f"   Length: {len(desc)}")
            print(f"   Preview: {desc[:150]}...")
            print(f"   Valid (>50 chars): {len(desc.strip()) >= 50}")
        else:
            print(f"❌ NO DESCRIPTION in inventoryItemGroup!")
            print(f"   inventoryItemGroup keys: {list(inv_group.keys())}")
    else:
        print(f"❌ NO inventoryItemGroup in group data!")
        print(f"   Group data keys: {list(group_data.keys())}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python check_group_description.py <group_key>")
        sys.exit(1)
    
    check_group(sys.argv[1])
