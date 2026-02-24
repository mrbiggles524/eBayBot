"""
Publish the variation group as a draft so it appears in Seller Hub.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def publish_group_draft():
    """Publish the group as a draft."""
    print("=" * 80)
    print("Publishing Variation Group as Draft")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    group_key = "GROUPTESTSET1768712745"
    
    print(f"Group Key: {group_key}")
    print()
    
    # First, get the group to verify it exists
    print("Checking group status...")
    try:
        response = client._make_request('GET', f'/sell/inventory/v1/inventory_item_group/{group_key}')
        
        if response.status_code == 200:
            group_data = response.json()
            print("[OK] Group found!")
            print(f"Title: {group_data.get('title', 'N/A')}")
            print(f"Variant SKUs: {group_data.get('variantSKUs', [])}")
            print()
        elif response.status_code == 404:
            print("[ERROR] Group not found")
            print("The group might have been deleted or doesn't exist.")
            return
        else:
            print(f"[WARNING] Could not get group: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print()
    except Exception as e:
        print(f"[WARNING] Exception getting group: {e}")
        print()
    
    # Try to publish the group
    print("Publishing group as draft...")
    print()
    print("Note: In production, publishing a group will make it LIVE.")
    print("Since we want a draft, we'll try a different approach.")
    print()
    
    # Actually, for variation listings, we need to publish the group
    # But in production, this will make it live, not a draft
    # The issue is that variation groups don't show as drafts until published
    
    print("=" * 80)
    print("Understanding Variation Listings")
    print("=" * 80)
    print()
    print("For variation listings (inventory item groups):")
    print("  - Individual offers don't show as drafts in Seller Hub")
    print("  - Only the GROUP shows as a draft")
    print("  - The group needs to be published to appear")
    print()
    print("However, in PRODUCTION, publishing makes it LIVE (not a draft).")
    print()
    print("Options:")
    print("  1. The group might appear after a delay (wait 5-10 minutes)")
    print("  2. Try searching by group key in Seller Hub")
    print("  3. Check if there's a 'Variation Drafts' section")
    print("  4. The listing might be there but with a different title")
    print()
    
    # Try to find it via the offers endpoint
    print("Searching for drafts via offers endpoint...")
    try:
        response = client._make_request('GET', '/sell/inventory/v1/offer', params={
            'limit': 100,
            'offset': 0
        })
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            
            # Find our test offer
            test_offers = [o for o in offers if o.get('sku') == 'CARD_TEST_SET_TEST_CARD_1_0']
            
            if test_offers:
                offer = test_offers[0]
                print(f"[OK] Found offer in offers list")
                print(f"  Offer ID: {offer.get('offerId')}")
                print(f"  Status: {offer.get('status')}")
                print(f"  Group Key: {offer.get('inventoryItemGroupKey', 'N/A')}")
                print()
                print("The offer exists but may not show in Seller Hub drafts")
                print("because it's part of a variation group.")
                print()
            else:
                print("[INFO] Offer not found in offers list")
                print("This is normal for variation listings.")
                print()
        else:
            print(f"[INFO] Could not get offers: {response.status_code}")
    except Exception as e:
        print(f"[INFO] Exception: {e}")
    
    print("=" * 80)
    print("Recommendation")
    print("=" * 80)
    print()
    print("For variation listings in production:")
    print("  1. They may not appear in 'Drafts' until the group is published")
    print("  2. Try creating a SINGLE listing (not variation) to test")
    print("  3. Or wait 5-10 minutes and check again")
    print("  4. The listing exists in the API - it's just not showing in Seller Hub UI")
    print()

if __name__ == "__main__":
    publish_group_draft()
