"""
Show detailed information about listings and provide direct links.
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

def show_listing_details():
    """Show detailed listing information with direct links."""
    print("=" * 80)
    print("Your Sandbox Listings - Detailed View")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get inventory items
    print("Fetching inventory items...")
    items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
    
    if items_response.status_code != 200:
        print(f"[ERROR] Failed to fetch inventory items: {items_response.status_code}")
        return
    
    items_data = items_response.json()
    inventory_items = items_data.get('inventoryItems', [])
    print(f"[OK] Found {len(inventory_items)} inventory item(s)")
    print()
    
    # Get offers for each item with full details
    print("Fetching detailed offer information...")
    print()
    
    offers_with_details = []
    
    for item in inventory_items:
        sku = item.get('sku')
        if sku:
            # Get full offer details
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success') and offer_result.get('offer'):
                offer = offer_result['offer']
                
                # Get title from multiple possible locations
                title = (
                    offer.get('listing', {}).get('title', '') or
                    offer.get('title', '') or
                    offer.get('product', {}).get('title', '') or
                    'Untitled Listing'
                )
                
                listing_id = offer.get('listingId')
                offer_id = offer.get('offerId')
                group_key = offer.get('inventoryItemGroupKey', '')
                status = offer.get('status', 'UNKNOWN')
                
                # Get pricing info
                pricing = offer.get('pricingSummary', {})
                price = pricing.get('price', {}).get('value', 'N/A') if pricing else 'N/A'
                
                # Get quantity
                quantity = offer.get('availableQuantity', offer.get('quantity', 'N/A'))
                
                offers_with_details.append({
                    'title': title,
                    'sku': sku,
                    'offer_id': offer_id,
                    'listing_id': listing_id,
                    'group_key': group_key,
                    'status': status,
                    'price': price,
                    'quantity': quantity
                })
    
    print(f"[OK] Found {len(offers_with_details)} offer(s) with details")
    print()
    print("=" * 80)
    print("LISTING DETAILS")
    print("=" * 80)
    print()
    
    # Group by status
    published = [o for o in offers_with_details if o['listing_id']]
    drafts = [o for o in offers_with_details if not o['listing_id']]
    
    if published:
        print(f"[PUBLISHED] {len(published)} Published Listing(s):")
        print()
        for i, offer in enumerate(published, 1):
            print(f"{i}. {offer['title']}")
            print(f"   SKU: {offer['sku']}")
            print(f"   Listing ID: {offer['listing_id']}")
            print(f"   Offer ID: {offer['offer_id']}")
            print(f"   Price: ${offer['price']}")
            print(f"   Quantity: {offer['quantity']}")
            print(f"   Status: {offer['status']}")
            if offer['group_key']:
                print(f"   Group Key: {offer['group_key']}")
            print(f"   [LINK] https://sandbox.ebay.com/itm/{offer['listing_id']}")
            print()
    
    if drafts:
        print(f"[DRAFTS] {len(drafts)} Draft Listing(s) (Not Published Yet):")
        print()
        for i, offer in enumerate(drafts, 1):
            print(f"{i}. {offer['title']}")
            print(f"   SKU: {offer['sku']}")
            print(f"   Offer ID: {offer['offer_id']}")
            print(f"   Price: ${offer['price']}")
            print(f"   Quantity: {offer['quantity']}")
            print(f"   Status: {offer['status']}")
            if offer['group_key']:
                print(f"   Group Key: {offer['group_key']}")
            print(f"   [NOTE] Draft - no listing ID yet. Publish to get a viewable link.")
            print()
    
    print("=" * 80)
    print("HOW TO VIEW YOUR LISTINGS")
    print("=" * 80)
    print()
    
    if published:
        print("[PUBLISHED] PUBLISHED LISTINGS (Click these links):")
        print()
        for offer in published:
            url = f"https://sandbox.ebay.com/itm/{offer['listing_id']}"
            print(f"   {offer['title']}")
            print(f"   {url}")
            print()
    
    if drafts:
        print("[DRAFT] DRAFT LISTINGS (Need to be published first):")
        print()
        print("   Option 1: Publish from Seller Hub")
        print("   Go to: https://sandbox.ebay.com/sh/account/listings?status=DRAFT")
        print("   (Note: Seller Hub URLs sometimes redirect - if it doesn't work, try Option 2)")
        print()
        print("   Option 2: Publish via API")
        print("   Use the Streamlit UI to publish your listings")
        print("   Or use the publish_offer_by_inventory_item_group API")
        print()
        print("   Option 3: View via API")
        print("   Run: python -c \"from ebay_api_client import eBayAPIClient; client = eBayAPIClient(); offer = client.get_offer_by_sku('YOUR_SKU'); print(offer)\"")
        print()
    
    print("=" * 80)

if __name__ == "__main__":
    show_listing_details()
