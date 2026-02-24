"""
Check your eBay listings via API (works for both sandbox and production).
This bypasses the web interface redirect issues.
"""
import json
import sys
import io
# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ebay_api_client import eBayAPIClient
from config import Config

def check_listings():
    """Check all listings in your eBay account."""
    print("=" * 80)
    print("Checking Your eBay Listings via API")
    print("=" * 80)
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"API URL: {config.ebay_api_url}")
    print()
    
    try:
        api_client = eBayAPIClient()
        
        # Get active listings
        print("Fetching active listings...")
        active_endpoint = "/sell/inventory/v1/offer"
        response = api_client._make_request('GET', active_endpoint, params={'limit': 100})
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            print(f"[OK] Found {len(offers)} active offers/listings")
            print()
            
            if offers:
                print("Active Listings:")
                print("-" * 80)
                for i, offer in enumerate(offers, 1):
                    offer_id = offer.get('offerId', 'N/A')
                    sku = offer.get('sku', 'N/A')
                    title = offer.get('listing', {}).get('title', 'No title')
                    listing_id = offer.get('listingId', 'Draft (not published)')
                    status = offer.get('listing', {}).get('listingStatus', 'Unknown')
                    
                    print(f"\n{i}. Listing ID: {listing_id}")
                    print(f"   Offer ID: {offer_id}")
                    print(f"   SKU: {sku}")
                    print(f"   Title: {title}")
                    print(f"   Status: {status}")
            else:
                print("No active listings found.")
        else:
            print(f"[ERROR] Error fetching listings: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        
        # Try to get inventory item groups (for variation listings)
        print("\n" + "=" * 80)
        print("Checking for Inventory Item Groups (Variation Listings)...")
        print("=" * 80)
        print()
        
        # Note: eBay API doesn't have a direct "list all groups" endpoint
        # But we can check if we know the group key
        print("💡 To check a specific group, you would need the group key.")
        print("   The group key from your listing was likely: GROUPCARDSMITHSBREAKSCOM...")
        print()
        
        # Check for draft offers
        print("Checking for draft/unscheduled offers...")
        draft_response = api_client._make_request('GET', active_endpoint, params={
            'limit': 100,
            'offset': 0
        })
        
        if draft_response.status_code == 200:
            draft_data = draft_response.json()
            all_offers = draft_data.get('offers', [])
            
            # Filter for drafts
            drafts = [o for o in all_offers if o.get('listing', {}).get('listingStatus') in ['DRAFT', 'UNPUBLISHED']]
            
            if drafts:
                print(f"[OK] Found {len(drafts)} draft listings:")
                print("-" * 80)
                for i, draft in enumerate(drafts, 1):
                    offer_id = draft.get('offerId', 'N/A')
                    sku = draft.get('sku', 'N/A')
                    title = draft.get('listing', {}).get('title', 'No title')
                    
                    print(f"\n{i}. Draft Offer")
                    print(f"   Offer ID: {offer_id}")
                    print(f"   SKU: {sku}")
                    print(f"   Title: {title}")
            else:
                print("No draft listings found via offers endpoint.")
                print()
                print("💡 Note: Variation listings created via publishOfferByInventoryItemGroup")
                print("   may not appear in the offers endpoint until published.")
                print("   They should be visible in eBay Seller Hub once you can access it.")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("If you don't see your listing here, it might be:")
    print("1. Created as a draft variation listing (may not show in offers endpoint)")
    print("2. Need to be checked via the inventory item group endpoint")
    print("3. Successfully created but requires Seller Hub access to view")
    print()
    print("Your listing was created successfully earlier, so it exists in your account.")
    print("The group key format was: GROUPCARDSMITHSBREAKSCOM...")

if __name__ == "__main__":
    check_listings()
