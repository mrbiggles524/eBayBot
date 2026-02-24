"""
Check details of the test offer to see why it's not showing in Seller Hub.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def check_offer():
    """Check offer details."""
    print("=" * 80)
    print("Checking Test Offer Details")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    
    print(f"SKU: {sku}")
    print()
    
    # Get offer by SKU
    print("Fetching offer details...")
    try:
        response = client._make_request('GET', f'/sell/inventory/v1/offer?sku={sku}')
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            
            if offers:
                offer = offers[0]
                print("[OK] Offer found!")
                print()
                print("Offer Details:")
                print(f"  Offer ID: {offer.get('offerId', 'N/A')}")
                print(f"  SKU: {offer.get('sku', 'N/A')}")
                
                listing = offer.get('listing', {})
                print(f"  Title: {listing.get('title', 'N/A')}")
                print(f"  Listing Status: {listing.get('listingStatus', 'N/A')}")
                print(f"  Format: {listing.get('format', 'N/A')}")
                print(f"  Category ID: {listing.get('categoryId', 'N/A')}")
                
                # Check if it's published
                listing_status = listing.get('listingStatus', '')
                if listing_status == 'PUBLISHED':
                    print()
                    print("[INFO] Offer is PUBLISHED (not a draft)")
                    print("       It should appear in 'Active' listings, not 'Drafts'")
                elif listing_status == 'INACTIVE':
                    print()
                    print("[INFO] Offer is INACTIVE")
                    print("       It might appear in 'Unsold' or 'Ended' listings")
                elif listing_status == '' or listing_status is None:
                    print()
                    print("[INFO] Offer has no listing status")
                    print("       It should be a draft, but might not be showing in Seller Hub")
                else:
                    print()
                    print(f"[INFO] Listing status: {listing_status}")
                
                print()
                print("Full offer data:")
                print(json.dumps(offer, indent=2))
            else:
                print("[ERROR] No offers found for this SKU")
        else:
            print(f"[ERROR] Failed to get offer: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_offer()
