"""
Publish one draft listing to get a direct link.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json

def publish_one_listing():
    """Publish one draft listing and get the direct link."""
    print("=" * 80)
    print("Publishing One Listing to Get Direct Link")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get inventory items
    print("Finding draft listings...")
    items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 10})
    
    if items_response.status_code != 200:
        print(f"[ERROR] Failed to fetch inventory items: {items_response.status_code}")
        return
    
    items_data = items_response.json()
    inventory_items = items_data.get('inventoryItems', [])
    
    if not inventory_items:
        print("[ERROR] No inventory items found")
        return
    
    # Find an offer that's part of a group (variation listing)
    print("Looking for variation listing (group)...")
    group_key = None
    test_sku = None
    group_skus = []
    
    # Check all items to find groups
    for item in inventory_items:
        sku = item.get('sku')
        if sku:
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success') and offer_result.get('offer'):
                offer = offer_result['offer']
                found_group_key = offer.get('inventoryItemGroupKey', '')
                if found_group_key:
                    if found_group_key not in [g['key'] for g in group_skus]:
                        group_skus.append({'key': found_group_key, 'sku': sku})
    
    if group_skus:
        # Use the first group found
        group_key = group_skus[0]['key']
        test_sku = group_skus[0]['sku']
        print(f"Found variation listing!")
        print(f"Group Key: {group_key}")
        print(f"Sample SKU: {test_sku}")
        print(f"Total groups found: {len(group_skus)}")
    
    if not group_key:
        # Fallback to first item
        first_sku = inventory_items[0].get('sku')
        print(f"No group found, using first listing: SKU {first_sku}")
        test_sku = first_sku
        
        offer_result = client.get_offer_by_sku(first_sku)
        if not offer_result.get('success') or not offer_result.get('offer'):
            print(f"[ERROR] Could not get offer for SKU {first_sku}")
            return
        
        offer = offer_result['offer']
        offer_id = offer.get('offerId')
        print(f"Offer ID: {offer_id}")
    else:
        offer_id = None
        print()
    
    # Try to publish
    if group_key:
        print(f"Publishing variation listing (group key: {group_key})...")
        publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    else:
        print(f"Publishing single offer (offer ID: {offer_id})...")
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
            print("OPEN THIS LINK IN YOUR BROWSER:")
            print("=" * 80)
            print(listing_url)
            print()
            print("=" * 80)
            
            # Try to open in browser (Windows)
            import webbrowser
            try:
                webbrowser.open(listing_url)
                print("[OK] Attempted to open link in your default browser")
            except Exception as e:
                print(f"[NOTE] Could not auto-open browser: {e}")
                print("Please copy and paste the link above into your browser")
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
        print("This might be because:")
        print("1. The listing is missing required information (description, policies, etc.)")
        print("2. There's a validation error")
        print("3. The listing needs to be in a group (for variation listings)")
        print()
        print("Try publishing from the Streamlit UI instead, which has better error handling.")

if __name__ == "__main__":
    publish_one_listing()
