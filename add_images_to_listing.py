"""
Add images to a listing via eBay API.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json

def add_images_to_listing(sku: str, image_urls: list):
    """Add images to a listing."""
    print("=" * 80)
    print("Adding Images to Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"SKU: {sku}")
    print(f"Images: {len(image_urls)}")
    print()
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success') or not offer_result.get('offer'):
        print(f"[ERROR] Could not get offer for SKU {sku}")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    print(f"Offer ID: {offer_id}")
    print()
    
    # Get current offer data
    listing_data = offer.get('listing', {})
    current_images = listing_data.get('imageUrls', []) or []
    
    print(f"Current images: {len(current_images)}")
    
    # Merge with new images (avoid duplicates)
    all_images = list(current_images)
    for img_url in image_urls:
        if img_url not in all_images:
            all_images.append(img_url)
    
    print(f"Total images after merge: {len(all_images)}")
    print()
    
    # Build update payload
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
            "title": listing_data.get('title', ''),
            "description": listing_data.get('description', ''),
            "listingPolicies": offer.get('listingPolicies', {}),
            "imageUrls": all_images  # Add images here
        }
    }
    
    # Also include itemSpecifics if they exist
    if 'itemSpecifics' in listing_data:
        update_data['listing']['itemSpecifics'] = listing_data['itemSpecifics']
    
    print("Updating offer with images...")
    print(f"Image URLs: {all_images}")
    print()
    
    # Update the offer
    update_result = client.update_offer(offer_id, update_data)
    
    if update_result.get('success'):
        print("[SUCCESS] Images added successfully!")
        print()
        print(f"Total images: {len(all_images)}")
        for i, img in enumerate(all_images, 1):
            print(f"  {i}. {img}")
    else:
        error = update_result.get('error', 'Unknown error')
        print(f"[ERROR] Failed to add images: {error}")
        print()
        print("This might be because:")
        print("1. Image URLs are not accessible")
        print("2. Image format is not supported")
        print("3. Offer is in an invalid state")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_images_to_listing.py <SKU> <image_url1> [image_url2] ...")
        print()
        print("Example:")
        print("  python add_images_to_listing.py CARD_BECKETT_COM_NEWS_202_TIM_HARDAWAY_JR_7_2 https://example.com/image1.jpg https://example.com/image2.jpg")
        sys.exit(1)
    
    sku = sys.argv[1]
    image_urls = sys.argv[2:]
    
    add_images_to_listing(sku, image_urls)
