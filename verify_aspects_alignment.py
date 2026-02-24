"""
Verify that inventory item aspects align with group's variesBy specifications.
This might be why description validation fails.
"""
from ebay_api_client import eBayAPIClient
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def verify_alignment():
    """Verify aspects alignment."""
    client = eBayAPIClient()
    
    group_key = "GROUPSAHF8A3F381768715399"
    sku = "CARD_DIFF_APPROACH_TEST_1_0"
    
    print("=" * 80)
    print("Verifying Aspects Alignment")
    print("=" * 80)
    print()
    
    # Get group
    print("Step 1: Getting group structure...")
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print("[ERROR] Group not found")
        return
    
    group_data = group_result.get('data', {})
    varies_by = group_data.get('variesBy', {})
    specifications = varies_by.get('specifications', [])
    
    print(f"Group: {group_key}")
    print(f"Title: {group_data.get('title', 'N/A')}")
    print()
    print("variesBy specifications:")
    for spec in specifications:
        print(f"  - {spec.get('name', 'N/A')}: {spec.get('values', [])}")
    print()
    
    # Get inventory item
    print("Step 2: Getting inventory item...")
    item_result = client._make_request('GET', f'/sell/inventory/v1/inventory_item/{sku}')
    if item_result.status_code == 200:
        item_data = item_result.json()
        product = item_data.get('product', {})
        item_aspects = product.get('aspects', {})
        
        print(f"Inventory Item: {sku}")
        print("Item aspects:")
        for key, value in item_aspects.items():
            print(f"  - {key}: {value}")
        print()
        
        # Check if aspects align
        print("Step 3: Checking alignment...")
        spec_names = [s.get('name') for s in specifications]
        item_aspect_keys = list(item_aspects.keys())
        
        print(f"Specification names: {spec_names}")
        print(f"Item aspect keys: {item_aspect_keys}")
        print()
        
        # Check if all spec names have corresponding aspects
        missing_aspects = []
        for spec_name in spec_names:
            if spec_name not in item_aspect_keys:
                missing_aspects.append(spec_name)
        
        if missing_aspects:
            print(f"[WARNING] Missing aspects in inventory item: {missing_aspects}")
            print("This might cause publish validation to fail!")
        else:
            print("[OK] All specification names have corresponding aspects")
        
        # Check if aspect values match spec values
        print()
        print("Checking if aspect values match specification values...")
        for spec in specifications:
            spec_name = spec.get('name')
            spec_values = spec.get('values', [])
            
            if spec_name in item_aspects:
                item_values = item_aspects[spec_name]
                if isinstance(item_values, list):
                    item_values = item_values
                else:
                    item_values = [item_values]
                
                # Check if any item value matches any spec value
                matches = False
                for item_val in item_values:
                    for spec_val in spec_values:
                        if str(item_val).strip() in str(spec_val).strip() or str(spec_val).strip() in str(item_val).strip():
                            matches = True
                            break
                    if matches:
                        break
                
                if matches:
                    print(f"  [OK] {spec_name}: Values align")
                else:
                    print(f"  [WARNING] {spec_name}: Values may not align")
                    print(f"    Spec values: {spec_values}")
                    print(f"    Item values: {item_values}")
    else:
        print(f"[ERROR] Could not get inventory item: {item_result.status_code}")
        return
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("If aspects don't align, this might cause publish validation issues.")
    print("The description might be stored but validation fails due to")
    print("aspect misalignment or other structural issues.")
    print()

if __name__ == "__main__":
    verify_alignment()
