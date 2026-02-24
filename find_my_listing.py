"""
Find your listing in sandbox using the API and generate direct links.
This bypasses the sandbox Seller Hub redirect issues.
"""
import sys
import os
from ebay_api_client import eBayAPIClient
from config import Config
import json

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def find_listing_by_title(title_search: str = None, group_key: str = None):
    """Find listings by title or group key and show direct links."""
    print("=" * 80)
    print("Finding Your Listing in Sandbox")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get all offers - the offers endpoint seems to have issues in sandbox
    # So we'll get inventory items first, then fetch offers by SKU
    print("Fetching inventory items...")
    items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
    
    offers = []
    if items_response.status_code == 200:
        items_data = items_response.json()
        inventory_items = items_data.get('inventoryItems', [])
        print(f"[OK] Found {len(inventory_items)} inventory item(s)")
        print("Fetching offers for each item...")
        
        # Get offers by SKU for each inventory item
        for item in inventory_items:
            sku = item.get('sku')
            if sku:
                offer_result = client.get_offer_by_sku(sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offers.append(offer_result['offer'])
        
        print(f"[OK] Found {len(offers)} offer(s) from inventory items")
    else:
        print(f"[WARNING] Could not fetch inventory items: {items_response.status_code}")
        print("Trying direct offers endpoint...")
        
        # Fallback: try direct offers endpoint
        response = client._make_request('GET', '/sell/inventory/v1/offer', params={'limit': 50})
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
        else:
            print(f"[ERROR] Failed to fetch offers: {response.status_code}")
            print(f"   {response.text[:500]}")
            print()
            print("[TIP] The offers endpoint may have issues in sandbox.")
            print("   Try checking inventory items instead.")
            return
    
    print(f"[OK] Found {len(offers)} offer(s) total")
    print()
    
    # Also try to get inventory item groups
    print("Fetching inventory item groups...")
    try:
        groups_response = client._make_request('GET', '/sell/inventory/v1/inventory_item_group', params={'limit': 100})
        groups = []
        if groups_response.status_code == 200:
            groups_data = groups_response.json()
            groups = groups_data.get('inventoryItemGroups', [])
            print(f"[OK] Found {len(groups)} inventory item group(s)")
        else:
            print(f"[WARNING] Could not fetch groups: {groups_response.status_code}")
    except Exception as e:
        print(f"[WARNING] Error fetching groups: {e}")
    
    print()
    
    # Filter by title or group key
    matching_offers = []
    matching_groups = []
    
    for offer in offers:
        # Try multiple places for title
        offer_title = (
            offer.get('listing', {}).get('title', '') or 
            offer.get('title', '') or
            offer.get('product', {}).get('title', '') or
            'Untitled Listing'
        )
        offer_group_key = offer.get('inventoryItemGroupKey', '')
        listing_id = offer.get('listingId')
        offer_id = offer.get('offerId')
        sku = offer.get('sku', '')
        status = offer.get('status', 'UNKNOWN')
        
        match = False
        if title_search and title_search.lower() in offer_title.lower():
            match = True
        if group_key and offer_group_key == group_key:
            match = True
        if not title_search and not group_key:
            match = True  # Show all if no filter
        
        if match:
            matching_offers.append({
                'title': offer_title,
                'listing_id': listing_id,
                'offer_id': offer_id,
                'sku': sku,
                'group_key': offer_group_key,
                'status': 'Published' if listing_id else 'Draft',
                'api_status': status
            })
    
    # Also check groups
    for group in groups:
        group_key_val = group.get('inventoryItemGroupKey', '')
        group_title = group.get('title', '')
        
        match = False
        if title_search and title_search.lower() in group_title.lower():
            match = True
        if group_key and group_key_val == group_key:
            match = True
        if not title_search and not group_key:
            match = True
        
        if match:
            matching_groups.append({
                'title': group_title,
                'group_key': group_key_val,
                'variants': group.get('variantSKUs', [])
            })
    
    if not matching_offers and not matching_groups:
        print("[ERROR] No matching listings found")
        if title_search:
            print(f"   Searched for: '{title_search}'")
        if group_key:
            print(f"   Group key: '{group_key}'")
        print()
        print("[TIP] Try:")
        print("   1. Check if the listing was actually created")
        print("   2. Try searching without filters to see all listings")
        print("   3. Check the console output for the group key or listing ID")
        print("   4. Run: python find_my_listing.py  (without arguments to see all)")
        print()
        if offers:
            print(f"[INFO] Showing all {len(offers)} offers found (no filter match):")
            for i, offer in enumerate(offers[:10], 1):  # Show first 10
                title = offer.get('listing', {}).get('title', '') or offer.get('title', 'N/A')
                listing_id = offer.get('listingId', 'N/A')
                print(f"   {i}. {title[:60]}... (Listing ID: {listing_id})")
            if len(offers) > 10:
                print(f"   ... and {len(offers) - 10} more")
        return
    
    print(f"✅ Found {len(matching_offers)} matching listing(s):")
    print()
    
    for i, listing in enumerate(matching_offers, 1):
        print(f"[{i}] {listing['title']}")
        print(f"    Status: {listing['status']}")
        print(f"    SKU: {listing['sku']}")
        print(f"    Offer ID: {listing['offer_id']}")
        
        if listing['listing_id']:
            listing_url = f"https://sandbox.ebay.com/itm/{listing['listing_id']}"
            print(f"    Listing ID: {listing['listing_id']}")
            print(f"    🔗 Direct Link: {listing_url}")
        else:
            print(f"    ⚠️  Draft listing (not published yet)")
            print(f"    🔗 To view: Use API or publish first")
        
        if listing['group_key']:
            print(f"    Group Key: {listing['group_key']}")
        
        print()
    
    print("=" * 80)
    print("How to View Your Listing")
    print("=" * 80)
    print()
    
    published = [l for l in matching_offers if l['listing_id']]
    drafts = [l for l in matching_offers if not l['listing_id']]
    
    if published:
        print("[OK] Published Listings (you can view these directly):")
        print()
        for listing in published:
            url1 = f"https://sandbox.ebay.com/itm/{listing['listing_id']}"
            url2 = f"https://www.sandbox.ebay.com/itm/{listing['listing_id']}"
            print(f"   [LISTING] {listing['title']}")
            print(f"   [LINK] Primary: {url1}")
            print(f"   [LINK] Alternative: {url2}")
            print(f"   [ID] Listing ID: {listing['listing_id']}")
            print()
    
    if drafts:
        print("[WARNING] Draft Listings (need to be published first):")
        print()
        for listing in drafts:
            print(f"   [LISTING] {listing['title']}")
            print(f"   [ID] Offer ID: {listing['offer_id']}")
            print(f"   [ID] SKU: {listing['sku']}")
            if listing['group_key']:
                print(f"   [ID] Group Key: {listing['group_key']}")
            print(f"   [INFO] Drafts don't have listing IDs yet")
            print(f"   [TIP] To view draft:")
            print(f"      1. Go to: https://sandbox.ebay.com/sh/account/listings?status=DRAFT")
            print(f"      2. Or publish the listing to get a viewable link")
            print()
    
    if matching_groups:
        print("[INFO] Inventory Item Groups:")
        print()
        for group in matching_groups:
            print(f"   [GROUP] {group['title']}")
            print(f"   [ID] Group Key: {group['group_key']}")
            print(f"   [INFO] Variants: {len(group['variants'])} SKU(s)")
            print()
    
    print("=" * 80)
    print("[TIP] Tips for Viewing Sandbox Listings")
    print("=" * 80)
    print()
    print("1. Direct Listing Links (Published):")
    print("   - Use the direct links above if you have a listing ID")
    print("   - Format: https://sandbox.ebay.com/itm/{listing_id}")
    print()
    print("2. Seller Hub (Drafts):")
    print("   - Go to: https://sandbox.ebay.com/sh/account/listings")
    print("   - Filter by status: DRAFT or ACTIVE")
    print("   - Note: Seller Hub URLs sometimes redirect - use direct links if possible")
    print()
    print("3. Sandbox Site:")
    print("   - Main site: https://sandbox.ebay.com")
    print("   - Sign in with your TESTUSER_ account")
    print("   - Go to 'My eBay' → 'Selling' → 'Active' or 'Drafts'")
    print()
    print("4. If links don't work:")
    print("   - Make sure you're signed in to sandbox (not production)")
    print("   - Try the alternative URL format (www.sandbox.ebay.com)")
    print("   - Check that the listing ID is correct")
    print()

if __name__ == "__main__":
    title_search = None
    group_key = None
    
    if len(sys.argv) > 1:
        # Check if it's a group key (starts with GROUP)
        if sys.argv[1].startswith('GROUP'):
            group_key = sys.argv[1]
        else:
            title_search = sys.argv[1]
    
    if len(sys.argv) > 2:
        group_key = sys.argv[2]
    
    find_listing_by_title(title_search, group_key)
