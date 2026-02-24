"""
Delete and recreate an offer from scratch with description.
This bypasses sandbox quirks by starting fresh.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

sku = sys.argv[1] if len(sys.argv) > 1 else 'CARD_BECKETT_COM_NEWS_202_TIM_HARDAWAY_JR_7_2'

client = eBayAPIClient()
config = Config()

print("=" * 80)
print("Delete and Recreate Offer from Scratch")
print("=" * 80)
print()

print(f"SKU: {sku}")
print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
print()

# Get current offer to copy data
print("Getting current offer data...")
offer_result = client.get_offer_by_sku(sku)
if not offer_result.get('success') or not offer_result.get('offer'):
    print(f"[ERROR] Could not get offer for SKU {sku}")
    sys.exit(1)

offer = offer_result['offer']
offer_id = offer.get('offerId')

print(f"Current Offer ID: {offer_id}")
print()

# Get all data
category_id = offer.get('categoryId', '261328')
price = offer.get('pricingSummary', {}).get('price', {}).get('value', '2.0')
quantity = offer.get('availableQuantity', offer.get('quantity', 1))
listing_policies = offer.get('listingPolicies', {})

# Remove return policy if it's invalid
if 'returnPolicyId' in listing_policies:
    print(f"[FIX] Removing return policy: {listing_policies['returnPolicyId']}")
    listing_policies.pop('returnPolicyId')

# Build complete offer data
title = "Trading Card - Quality Item"
description = "This is a quality trading card in excellent condition. All cards are carefully inspected before listing. Fast shipping and excellent customer service guaranteed. Perfect for collectors and enthusiasts."

print("Deleting old offer...")
# Delete the offer
delete_response = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
if delete_response.status_code in [200, 204]:
    print("[OK] Offer deleted")
    time.sleep(3)
else:
    print(f"[WARNING] Could not delete offer: {delete_response.status_code}")
    print("Continuing anyway...")

print()
print("Creating new offer from scratch...")
print(f"Title: {title}")
print(f"Description length: {len(description)}")
print()

# Create fresh offer
offer_data = {
    "sku": sku,
    "marketplaceId": "EBAY_US",
    "format": "FIXED_PRICE",
    "availableQuantity": int(quantity),
    "pricingSummary": {
        "price": {
            "value": str(price),
            "currency": "USD"
        }
    },
    "listingPolicies": listing_policies,
    "categoryId": str(category_id),
    "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
    "listing": {
        "title": title,
        "description": description,
        "listingPolicies": listing_policies,
        "imageUrls": []
    }
}

print("Creating offer with description...")
create_response = client._make_request('POST', '/sell/inventory/v1/offer', data=offer_data)

if create_response.status_code in [200, 201]:
    print("[OK] Offer created successfully!")
    result = create_response.json()
    new_offer_id = result.get('offerId')
    print(f"New Offer ID: {new_offer_id}")
    print()
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    # Try to publish
    print("Attempting to publish...")
    publish_result = client.publish_offer(new_offer_id)
    
    if publish_result.get('success'):
        listing_id = publish_result.get('data', {}).get('listingId') or publish_result.get('listingId')
        if listing_id:
            listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
            print()
            print("=" * 80)
            print("[SUCCESS] Listing Published!")
            print("=" * 80)
            print()
            print(f"Listing ID: {listing_id}")
            print(f"Direct Link: {listing_url}")
            print()
            
            import webbrowser
            try:
                webbrowser.open(listing_url)
                print("[OK] Opened in browser!")
            except:
                pass
        else:
            print("[WARNING] Published but no listing ID")
    else:
        error = publish_result.get('error', 'Unknown')
        print(f"[ERROR] Failed to publish: {error}")
        print()
        print("This is a known sandbox limitation.")
else:
    error_text = create_response.text
    print(f"[ERROR] Failed to create offer: {create_response.status_code}")
    print(error_text[:500])
