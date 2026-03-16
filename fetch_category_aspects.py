"""
Fetch required aspects for Trading Cards category 261328 from eBay Taxonomy API.
Run: python fetch_category_aspects.py
"""
import os
import requests
from dotenv import load_dotenv
load_dotenv()

def main():
    token = os.getenv('EBAY_PRODUCTION_TOKEN')
    if not token:
        print("ERROR: EBAY_PRODUCTION_TOKEN not set")
        return
    
    # Step 1: Get default category tree ID for EBAY_US
    tree_url = "https://api.ebay.com/commerce/taxonomy/v1/get_default_category_tree_id"
    r = requests.get(tree_url, params={"marketplace_id": "EBAY_US"}, 
                     headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        print(f"Tree ID failed: {r.status_code} {r.text[:300]}")
        return
    tree_id = r.json().get("categoryTreeId") or r.json().get("category_tree_id")
    print(f"Category tree ID: {tree_id}")
    
    # Step 2: Get item aspects for category 261328
    aspects_url = f"https://api.ebay.com/commerce/taxonomy/v1/category_tree/{tree_id}/get_item_aspects_for_category"
    r2 = requests.get(aspects_url, params={"category_id": "261328"},
                      headers={"Authorization": f"Bearer {token}", "Content-Language": "en-US"})
    if r2.status_code != 200:
        print(f"Aspects failed: {r2.status_code} {r2.text[:500]}")
        return
    
    data = r2.json()
    aspects = data.get("aspects", [])
    print(f"\nFound {len(aspects)} aspects for category 261328\n")
    
    # Find Sport and required aspects
    for a in aspects:
        name = a.get("localizedAspectName") or a.get("aspectIdentifier", "?")
        ident = a.get("aspectIdentifier", "")
        req = a.get("aspectConstraint", {}).get("aspectRequired", False)
        if "sport" in name.lower() or "sport" in ident.lower():
            print(f"*** SPORT ASPECT ***")
            print(f"  localizedAspectName: {name}")
            print(f"  aspectIdentifier: {ident}")
            print(f"  aspectRequired: {req}")
            vals = a.get("aspectValues", []) or a.get("aspectValuesForCatalogProduct", [])
            if vals:
                print(f"  Allowed values (first 10): {[v.get('localizedValue') or v.get('value') for v in vals[:10]]}")
            print()
        elif req:
            print(f"REQUIRED: {name} (ident={ident})")
    
    # List all required
    print("\n--- ALL REQUIRED ASPECTS ---")
    for a in aspects:
        if a.get("aspectConstraint", {}).get("aspectRequired"):
            print(f"  {a.get('localizedAspectName') or a.get('aspectIdentifier')}")

if __name__ == "__main__":
    main()
