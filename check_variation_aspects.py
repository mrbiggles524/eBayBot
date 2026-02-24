"""
Check which aspects are allowed for variations in Trading Cards category 261328.
Only aspects with aspectEnabledForVariations=true can be used.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Check Variation Aspects for Trading Cards (Category 261328)")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    category_id = "261328"  # Trading Cards
    
    print(f"Checking category: {category_id}")
    print()
    
    # Call getItemAspectsForCategory
    try:
        response = client._make_request('GET', f'/sell/taxonomy/v1/category_tree/{category_id}/get_item_aspects_for_category', 
                                       params={'category_id': category_id})
        
        if response.status_code == 200:
            data = response.json()
            aspects = data.get('aspects', [])
            
            print(f"Found {len(aspects)} total aspects")
            print()
            
            # Find aspects enabled for variations
            variation_aspects = []
            for aspect in aspects:
                constraint = aspect.get('aspectConstraint', {})
                enabled_for_variations = constraint.get('aspectEnabledForVariations', False)
                
                if enabled_for_variations:
                    variation_aspects.append(aspect)
                    aspect_name = aspect.get('localizedAspectName', 'Unknown')
                    data_type = constraint.get('aspectDataType', 'Unknown')
                    cardinality = constraint.get('itemToAspectCardinality', 'Unknown')
                    required = constraint.get('aspectRequired', False)
                    
                    print(f"✅ {aspect_name}")
                    print(f"   Data Type: {data_type}")
                    print(f"   Cardinality: {cardinality}")
                    print(f"   Required: {required}")
                    print()
            
            if variation_aspects:
                print("=" * 80)
                print(f"VALID VARIATION ASPECTS ({len(variation_aspects)}):")
                print("=" * 80)
                for aspect in variation_aspects:
                    print(f"  - {aspect.get('localizedAspectName', 'Unknown')}")
                print()
                print("You can use these aspects in your variation specifications.")
            else:
                print("=" * 80)
                print("⚠️ NO ASPECTS ENABLED FOR VARIATIONS")
                print("=" * 80)
                print()
                print("This category may not support variations, or you need to use")
                print("predefined aspects. Consider creating separate listings instead.")
        else:
            print(f"[ERROR] Status {response.status_code}")
            print(response.text[:500])
            print()
            print("Trying alternative endpoint...")
            
            # Try alternative endpoint
            response2 = client._make_request('GET', '/sell/taxonomy/v1/get_item_aspects_for_category',
                                           params={'category_id': category_id})
            if response2.status_code == 200:
                print("[OK] Alternative endpoint worked!")
                data = response2.json()
                print(json.dumps(data, indent=2)[:1000])
            else:
                print(f"[ERROR] Alternative endpoint also failed: {response2.status_code}")
                
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 80)
        print("FALLBACK: Use Predefined Aspects")
        print("=" * 80)
        print()
        print("Since we can't query the API, try using common predefined aspects:")
        print("  - Brand")
        print("  - Set")
        print("  - Year")
        print("  - Team")
        print("  - Player")
        print()
        print("Or create separate listings instead of variations.")

if __name__ == "__main__":
    main()
