"""
View your sandbox listings via the API.
Since the sandbox seller hub UI doesn't work well, use this to see your listings.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("View Sandbox Listings")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Method 1: Get offers (draft and published listings)
    print("Method 1: Checking offers (draft and published listings)...")
    print()
    
    try:
        # Get offers - this shows both drafts and published listings
        response = client._make_request('GET', '/sell/inventory/v1/offer', params={'limit': 50})
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            
            if offers:
                print(f"[OK] Found {len(offers)} offer(s):")
                print()
                for i, offer in enumerate(offers, 1):
                    offer_id = offer.get('offerId', 'N/A')
                    sku = offer.get('sku', 'N/A')
                    listing_id = offer.get('listingId', 'N/A')
                    status = offer.get('status', 'N/A')
                    title = offer.get('listing', {}).get('title', 'N/A')
                    
                    print(f"{i}. Offer ID: {offer_id}")
                    print(f"   SKU: {sku}")
                    print(f"   Status: {status}")
                    print(f"   Title: {title}")
                    
                    if listing_id and listing_id != 'N/A':
                        listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
                        print(f"   Listing ID: {listing_id}")
                        print(f"   View: {listing_url}")
                    else:
                        print(f"   (Draft - not yet published)")
                    print()
            else:
                print("[INFO] No offers found")
        else:
            print(f"[WARNING] Status {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Could not get offers: {e}")
    
    print()
    print("=" * 80)
    print("Method 2: Checking inventory items...")
    print("=" * 80)
    print()
    
    try:
        # Get inventory items
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 50})
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('inventoryItems', [])
            
            if items:
                print(f"[OK] Found {len(items)} inventory item(s):")
                print()
                for i, item in enumerate(items, 1):
                    sku = item.get('sku', 'N/A')
                    product = item.get('product', {})
                    title = product.get('title', 'N/A')
                    category = product.get('categoryId', 'N/A')
                    
                    print(f"{i}. SKU: {sku}")
                    print(f"   Title: {title}")
                    print(f"   Category: {category}")
                    print()
            else:
                print("[INFO] No inventory items found")
        else:
            print(f"[WARNING] Status {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Could not get inventory items: {e}")
    
    print()
    print("=" * 80)
    print("How to View Listings in Sandbox")
    print("=" * 80)
    print()
    print("The sandbox seller hub UI is limited and often redirects to production.")
    print("Use these methods instead:")
    print()
    print("1. View a specific listing:")
    print("   https://sandbox.ebay.com/itm/{LISTING_ID}")
    print("   (Replace {LISTING_ID} with the actual listing ID from above)")
    print()
    print("2. Use the API (this script) to view all your listings")
    print()
    print("3. The listing creation code should return a listing_id or group_key")
    print("   Check the Streamlit UI output for these values")

if __name__ == "__main__":
    main()
