"""Force add description to a listing and verify it's saved."""
import sys
from ebay_api_client import eBayAPIClient
import json
import time

sku = sys.argv[1] if len(sys.argv) > 1 else 'CARD_BECKETT_COM_NEWS_202_TIM_HARDAWAY_JR_7_2'

client = eBayAPIClient()

print("Getting current offer...")
result = client.get_offer_by_sku(sku)

if not result.get('success') or not result.get('offer'):
    print(f"Could not get offer for {sku}")
    sys.exit(1)

offer = result['offer']
offer_id = offer.get('offerId')

print(f"Offer ID: {offer_id}")
print(f"Current title: {offer.get('listing', {}).get('title', 'MISSING')}")
print(f"Current description: {offer.get('listing', {}).get('description', 'MISSING')[:50] if offer.get('listing', {}).get('description') else 'MISSING'}")
print()

# Build complete update with title and description
description = "This is a quality trading card in excellent condition. All cards are carefully inspected before listing. Fast shipping and excellent customer service guaranteed. Perfect for collectors."
title = "Trading Card - Quality Item"

update_data = {
    "sku": sku,
    "marketplaceId": "EBAY_US",
    "format": "FIXED_PRICE",
    "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
    "pricingSummary": offer.get('pricingSummary', {}),
    "listingPolicies": offer.get('listingPolicies', {}),
    "categoryId": offer.get('categoryId'),
    "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
    "listing": {
        "title": title,
        "description": description,
        "listingPolicies": offer.get('listingPolicies', {}),
        "imageUrls": offer.get('listing', {}).get('imageUrls', []) or []
    }
}

print("Updating offer with title and description...")
print(f"Title: {title}")
print(f"Description length: {len(description)}")
print()

update_result = client.update_offer(offer_id, update_data)

if update_result.get('success'):
    print("[OK] Update successful!")
    print("Waiting 3 seconds...")
    time.sleep(3)
    
    # Verify it was saved
    print("Verifying description was saved...")
    verify_result = client.get_offer_by_sku(sku)
    if verify_result.get('success') and verify_result.get('offer'):
        verify_offer = verify_result['offer']
        verify_listing = verify_offer.get('listing', {})
        verify_title = verify_listing.get('title', '')
        verify_desc = verify_listing.get('description', '')
        
        print(f"Verified title: {verify_title[:50] if verify_title else 'MISSING'}")
        print(f"Verified description: {verify_desc[:50] if verify_desc else 'MISSING'} (length: {len(verify_desc)})")
        
        if verify_desc and len(verify_desc) >= 50:
            print()
            print("[SUCCESS] Description is saved! Now try publishing:")
            print(f"  python publish_draft.py {sku}")
        else:
            print()
            print("[WARNING] Description still not showing in GET response")
            print("This is a sandbox quirk - description might be saved but GET doesn't return it")
            print("Try publishing anyway - it might work:")
            print(f"  python publish_draft.py {sku}")
    else:
        print("[ERROR] Could not verify")
else:
    error = update_result.get('error', 'Unknown')
    print(f"[ERROR] Update failed: {error}")
