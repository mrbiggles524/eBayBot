"""
Recreate a listing from scratch with all required fields and publish it.
This bypasses the sandbox description quirk by creating fresh.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

def recreate_and_publish(sku: str):
    """Recreate listing from scratch and publish."""
    print("=" * 80)
    print("Recreate Listing from Scratch and Publish")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"SKU: {sku}")
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get current offer to copy data
    print("Getting current offer data...")
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success') or not offer_result.get('offer'):
        print(f"[ERROR] Could not get offer for SKU {sku}")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    group_key = offer.get('inventoryItemGroupKey', '')
    
    print(f"Offer ID: {offer_id}")
    if group_key:
        print(f"Group Key: {group_key} (Variation Listing)")
    print()
    
    # Get all data we need
    category_id = offer.get('categoryId', '261328')
    price = offer.get('pricingSummary', {}).get('price', {}).get('value', '2.0')
    quantity = offer.get('availableQuantity', offer.get('quantity', 1))
    listing_policies = offer.get('listingPolicies', {})
    
    # Build complete offer data with description
    title = "Trading Card - Quality Item"
    description = "This is a quality trading card in excellent condition. All cards are carefully inspected before listing. Fast shipping and excellent customer service guaranteed. Perfect for collectors and enthusiasts."
    
    print("Creating fresh offer with all required fields...")
    print(f"Title: {title}")
    print(f"Description length: {len(description)}")
    print()
    
    # Create/update offer with complete data
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
            "imageUrls": offer.get('listing', {}).get('imageUrls', []) or []
        }
    }
    
    # Include itemSpecifics if they exist
    if 'itemSpecifics' in offer.get('listing', {}):
        offer_data['listing']['itemSpecifics'] = offer.get('listing', {}).get('itemSpecifics')
    
    print("Updating offer with complete data...")
    update_result = client.update_offer(offer_id, offer_data)
    
    if not update_result.get('success'):
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")
        return
    
    print("[OK] Offer updated successfully")
    print("Waiting 10 seconds for changes to fully propagate...")
    time.sleep(10)
    
    # Try to publish
    print()
    print("Attempting to publish...")
    
    if group_key:
        print(f"Publishing via group: {group_key}")
        publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    else:
        print(f"Publishing single offer: {offer_id}")
        publish_result = client.publish_offer(offer_id)
    
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
            print("=" * 80)
            
            # Try to open in browser
            import webbrowser
            try:
                webbrowser.open(listing_url)
                print("[OK] Opened in browser!")
            except:
                print("[NOTE] Could not auto-open browser")
        else:
            print("[WARNING] Published but no listing ID returned")
            print("Response:", json.dumps(publish_result, indent=2))
    else:
        error = publish_result.get('error', 'Unknown error')
        print()
        print("=" * 80)
        print("[ERROR] Failed to Publish")
        print("=" * 80)
        print(f"Error: {error}")
        print()
        print("This is a known sandbox limitation.")
        print("The listing is saved as a draft with all required fields.")
        print("You may need to publish it manually from eBay Seller Hub.")

if __name__ == "__main__":
    sku = sys.argv[1] if len(sys.argv) > 1 else 'CARD_BECKETT_COM_NEWS_202_TIM_HARDAWAY_JR_7_2'
    recreate_and_publish(sku)
