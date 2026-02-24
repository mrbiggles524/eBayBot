"""
Publish ONE test listing to see if it appears in Seller Hub.
This will make it LIVE in production.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def publish_one():
    """Publish one test listing."""
    print("=" * 80)
    print("Publishing ONE Test Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    print("[WARNING] This will publish the listing LIVE in production!")
    print("          It will be visible to buyers.")
    print()
    
    # Use the test listing we created
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    group_key = "GROUPTESTSET1768712745"
    
    print(f"SKU: {sku}")
    print(f"Group Key: {group_key}")
    print()
    
    # First, verify the group exists
    print("Verifying group exists...")
    try:
        response = client._make_request('GET', f'/sell/inventory/v1/inventory_item_group/{group_key}')
        
        if response.status_code == 200:
            group_data = response.json()
            title = group_data.get('title', 'N/A')
            print(f"[OK] Group found: {title}")
            print()
        else:
            print(f"[ERROR] Group not found: {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return
    
    # Publish the group
    print("Publishing variation group...")
    print()
    print("This will make the listing LIVE and visible to buyers.")
    print()
    
    try:
        result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
        
        if result.get('success'):
            listing_id = result.get('listing_id')
            print()
            print("=" * 80)
            print("[SUCCESS] Listing Published!")
            print("=" * 80)
            print()
            print(f"Listing ID: {listing_id}")
            print(f"Title: Test Listing - Please Delete")
            print()
            print("View your listing:")
            print(f"  https://www.ebay.com/itm/{listing_id}")
            print()
            print("Check Seller Hub:")
            print("  - Go to: https://www.ebay.com/sh/landing")
            print("  - Navigate to: Listings -> Active")
            print("  - You should see 'Test Listing - Please Delete'")
            print()
            print("[IMPORTANT] This listing is now LIVE and visible to buyers!")
            print("           Delete it from Seller Hub when done testing.")
            print()
        else:
            error = result.get('error', 'Unknown error')
            print(f"[ERROR] Failed to publish: {error}")
            print()
            print("Full error details:")
            print(result)
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    publish_one()
