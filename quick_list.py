"""
=============================================================================
QUICK LIST - List a card set with one command
=============================================================================

Usage:
    python quick_list.py

This script will:
1. Use your card data from CARDS list below
2. Automatically use eBay shipping labels (PWE policy)
3. Use "No Returns Accepted" policy
4. Create a variation listing with all cards
5. Publish to eBay

=============================================================================
"""
from ebay_api_client import eBayAPIClient
import sys
import time
import uuid
import re

sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# YOUR CARD SET - EDIT THIS SECTION
# =============================================================================

SET_NAME = "2024-25 Topps Chrome Basketball"

# Your description (HTML supported)
DESCRIPTION = """<p><strong>2024-25 Topps Chrome Basketball Cards</strong></p>
<p>Premium chromium cards from the 2024-25 Topps Chrome Basketball set.</p>
<p><strong>Select your card from the dropdown menu.</strong></p>
<p>All cards are in Near Mint or better condition.</p>
<p>Ships in penny sleeve + top loader via PWE with eBay tracking.</p>"""

# Your cards - format: (number, name, price)
# Add as many as you want!
CARDS = [
    ("1", "LeBron James", 5.00),
    ("2", "Stephen Curry", 4.00),
    ("3", "Kevin Durant", 3.50),
    ("4", "Giannis Antetokounmpo", 3.00),
    ("5", "Luka Doncic", 4.50),
    # Add more cards here...
]

# Default image (replace with your card image URL)
IMAGE_URL = "https://i.ebayimg.com/images/g/WYsAAOSwpkFnRxqE/s-l1600.webp"

# =============================================================================
# END CONFIGURATION - Don't edit below unless you know what you're doing
# =============================================================================

def clean_text(text):
    clean = re.sub(r'[^a-zA-Z0-9]', '_', str(text))
    return re.sub(r'_+', '_', clean)[:25].upper()

def main():
    client = eBayAPIClient()
    
    print()
    print("=" * 70)
    print("QUICK LIST - eBay Card Set Listing")
    print("=" * 70)
    print()
    print(f"Set: {SET_NAME}")
    print(f"Cards: {len(CARDS)}")
    print()
    
    for num, name, price in CARDS:
        print(f"  #{num} {name} - ${price:.2f}")
    
    print()
    print("-" * 70)
    print()
    
    # Generate IDs
    uid = str(uuid.uuid4())[:6].upper()
    set_clean = clean_text(SET_NAME)[:10]
    group_key = f"SET_{set_clean}_{uid}"
    
    # Get policies
    print("Getting policies...")
    
    # Payment
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    payment_id = None
    if resp.status_code == 200:
        for p in resp.json().get('paymentPolicies', []):
            if p.get('immediatePay'):
                payment_id = p.get('paymentPolicyId')
                break
        if not payment_id:
            payment_id = resp.json().get('paymentPolicies', [{}])[0].get('paymentPolicyId')
    
    # Shipping - prefer PWE/flat rate
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    shipping_id = None
    if resp.status_code == 200:
        for p in resp.json().get('fulfillmentPolicies', []):
            name = p.get('name', '').upper()
            if 'PWE' in name or 'FLAT' in name or 'LABEL' in name:
                shipping_id = p.get('fulfillmentPolicyId')
                print(f"  Shipping: {p.get('name')}")
                break
        if not shipping_id:
            shipping_id = resp.json().get('fulfillmentPolicies', [{}])[0].get('fulfillmentPolicyId')
    
    # Returns - prefer No Returns
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    return_id = None
    if resp.status_code == 200:
        for p in resp.json().get('returnPolicies', []):
            if not p.get('returnsAccepted'):
                return_id = p.get('returnPolicyId')
                print(f"  Returns: {p.get('name')}")
                break
        if not return_id:
            return_id = resp.json().get('returnPolicies', [{}])[0].get('returnPolicyId')
    
    if not all([payment_id, shipping_id, return_id]):
        print("[ERROR] Missing policies!")
        return
    
    print()
    
    # Create inventory items
    print("Creating inventory items...")
    skus = []
    variations = []
    prices = {}
    
    for num, name, price in CARDS:
        sku = f"{set_clean}_{clean_text(name)}_{num}_{uid}"
        var_value = f"{num} {name}"
        variations.append(var_value)
        prices[sku] = price
        
        item = {
            "sku": sku,
            "product": {
                "title": f"{name} #{num} - {SET_NAME}"[:80],
                "description": f"<p>{name} #{num}</p>",
                "aspects": {
                    "Card Name": [name],
                    "Card Number": [str(num)],
                    "Sport": ["Basketball"],
                    "Card Manufacturer": ["Topps"],
                    "Season": ["2024-25"],
                    "Features": ["Base", "Chrome"],
                    "Type": ["Sports Trading Card"],
                    "Language": ["English"],
                    "Original/Licensed Reprint": ["Original"],
                    "Pick Your Card": [var_value]
                },
                "imageUrls": [IMAGE_URL]
            },
            "condition": "USED_VERY_GOOD",
            "conditionDescriptors": [{"name": "40001", "values": ["400010"]}],
            "availability": {"shipToLocationAvailability": {"quantity": 1}},
            "packageWeightAndSize": {
                "dimensions": {"width": 4.0, "length": 6.0, "height": 1.0, "unit": "INCH"},
                "weight": {"value": 0.19, "unit": "POUND"}
            }
        }
        
        result = client.create_inventory_item(sku, item)
        if result.get('success'):
            skus.append(sku)
            print(f"  [OK] #{num} {name}")
        else:
            print(f"  [X] #{num} {name} - {result.get('error', '')[:50]}")
    
    if not skus:
        print("[ERROR] No items created!")
        return
    
    print()
    
    # Create group
    print("Creating variation group...")
    group = {
        "title": SET_NAME[:80],
        "description": DESCRIPTION,
        "variantSKUs": skus,
        "variesBy": {"specifications": [{"name": "Pick Your Card", "values": variations}]},
        "aspects": {"Sport": ["Basketball"], "Card Manufacturer": ["Topps"], "Season": ["2024-25"], "Type": ["Sports Trading Card"]},
        "imageUrls": [IMAGE_URL]
    }
    
    resp = client._make_request('PUT', f'/sell/inventory/v1/inventory_item_group/{group_key}', data=group)
    if resp.status_code not in [200, 201, 204]:
        print(f"[ERROR] Group failed: {resp.text[:100]}")
        return
    print(f"  [OK] Group: {group_key}")
    print()
    
    # Create offers
    print("Creating offers...")
    for sku in skus:
        offer = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "listingPolicies": {"paymentPolicyId": payment_id, "fulfillmentPolicyId": shipping_id, "returnPolicyId": return_id},
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc",
            "categoryId": "261328",
            "pricingSummary": {"price": {"value": str(prices[sku]), "currency": "USD"}},
            "availableQuantity": 1,
            "listingDuration": "GTC"
        }
        client._make_request('POST', '/sell/inventory/v1/offer', data=offer)
    print(f"  [OK] {len(skus)} offers created")
    print()
    
    # Confirm
    print("=" * 70)
    print("READY TO PUBLISH")
    print("=" * 70)
    print()
    print(f"Set: {SET_NAME}")
    print(f"Cards: {len(skus)}")
    print(f"Shipping: eBay Labels (PWE)")
    print(f"Returns: No Returns Accepted")
    print()
    
    confirm = input("Type YES to publish LIVE on eBay: ")
    if confirm.strip().upper() != 'YES':
        print()
        print("[CANCELLED]")
        print(f"Group Key: {group_key}")
        return
    
    # Publish
    print()
    print("Publishing...")
    time.sleep(2)
    
    resp = client._make_request('POST', '/sell/inventory/v1/offer/publish_by_inventory_item_group', 
                                data={"inventoryItemGroupKey": group_key, "marketplaceId": "EBAY_US"})
    
    if resp.status_code in [200, 201]:
        listing_id = resp.json().get('listingId')
        print()
        print("=" * 70)
        print("SUCCESS! LISTING IS LIVE!")
        print("=" * 70)
        print()
        print(f"Listing ID: {listing_id}")
        print(f"URL: https://www.ebay.com/itm/{listing_id}")
        print()
        print("Check Seller Hub: https://www.ebay.com/sh/lst/active")
        print()
    else:
        print()
        print("[ERROR]")
        errors = resp.json().get('errors', []) if resp.text else []
        for e in errors:
            print(f"  {e.get('message')}")
        print()
        print(f"Group Key: {group_key}")


if __name__ == "__main__":
    main()
