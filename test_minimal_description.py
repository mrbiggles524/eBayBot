"""
Test with the absolute minimal valid description to see if that works.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import time

sys.stdout.reconfigure(encoding='utf-8')

def test_minimal_description(group_key):
    """Test with minimal description."""
    print("=" * 80)
    print(f"TESTING MINIMAL DESCRIPTION FOR: {group_key}")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    # Get group
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print(f"❌ Group not found")
        return
    
    group_data = group_result.get('data', {})
    title = group_data.get('title', 'Variation Listing')
    variant_skus = group_data.get('variantSKUs', [])
    
    # MINIMAL description - just enough to be valid (50+ chars)
    # No special characters, no HTML, just plain text
    minimal_desc = f"{title}. Select your card from the variations below. Each card is listed as a separate variation option. All cards are in Near Mint or better condition. Ships in penny sleeve and top loader via PWE with eBay tracking. This is a variation listing where you can select from multiple card options."
    
    # Ensure it's exactly 50+ characters
    while len(minimal_desc.strip()) < 50:
        minimal_desc += " Additional information about the listing."
    
    print(f"Minimal description (length: {len(minimal_desc)}):")
    print(f"  {minimal_desc}")
    print()
    
    # Get aspects
    aspects = {}
    if variant_skus:
        offer_result = client.get_offer_by_sku(variant_skus[0])
        if offer_result.get('success'):
            offer = offer_result.get('offer', {})
            listing = offer.get('listing', {})
            item_specifics = listing.get('itemSpecifics', {})
            if item_specifics:
                for key, value in item_specifics.items():
                    if isinstance(value, list) and len(value) > 0:
                        aspects[key] = value
    
    # Update group with minimal description
    print("Updating group with minimal description...")
    update_data = {
        "title": title,
        "variesBy": group_data.get('variesBy', {}),
        "inventoryItemGroup": {
            "aspects": aspects,
            "description": minimal_desc
        },
        "variantSKUs": variant_skus
    }
    
    result = client.create_inventory_item_group(group_key, update_data)
    if not result.get('success'):
        print(f"❌ Update failed: {result.get('error')}")
        return
    
    print("✅ Group updated")
    print()
    print("Waiting 20 seconds...")
    time.sleep(20)
    
    # Try publishing
    print("Publishing...")
    publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    
    if publish_result.get('success'):
        print("✅ SUCCESS! Published with minimal description!")
    else:
        error = publish_result.get('error', 'Unknown')
        print(f"❌ FAILED: {error}")
        print()
        print("Even minimal description failed. This suggests:")
        print("  1. eBay API bug")
        print("  2. Description location issue")
        print("  3. Need to check eBay API documentation for exact requirements")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_minimal_description.py <group_key>")
        sys.exit(1)
    
    test_minimal_description(sys.argv[1])
