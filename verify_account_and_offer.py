"""
Verify which account the token is for and check offer status.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def verify():
    """Verify account and offer."""
    print("=" * 80)
    print("Verifying Account and Offer Status")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try to get account info
    print("Checking account information...")
    try:
        # Try Account API to get user info
        response = client._make_request('GET', '/sell/account/v1/privilege')
        
        if response.status_code == 200:
            data = response.json()
            print("[OK] Account API accessible")
            print(f"Response: {json.dumps(data, indent=2)}")
            print()
        else:
            print(f"[INFO] Account API returned: {response.status_code}")
            print()
    except Exception as e:
        print(f"[INFO] Could not get account info: {e}")
        print()
    
    # Check the offer
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    print(f"Checking offer for SKU: {sku}")
    print()
    
    try:
        response = client._make_request('GET', f'/sell/inventory/v1/offer?sku={sku}')
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            
            if offers:
                offer = offers[0]
                offer_id = offer.get('offerId')
                status = offer.get('status', 'N/A')
                listing = offer.get('listing', {})
                title = listing.get('title', 'N/A')
                
                print("[OK] Offer found!")
                print()
                print("Offer Details:")
                print(f"  Offer ID: {offer_id}")
                print(f"  Status: {status}")
                print(f"  Title: {title}")
                print()
                
                if status == 'UNPUBLISHED':
                    print("[INFO] Offer status is UNPUBLISHED (draft)")
                    print()
                    print("This should appear in Seller Hub drafts, but:")
                    print("  1. It might take a few minutes to sync")
                    print("  2. The offer might need to be part of a published group")
                    print("  3. Try checking 'Active' or 'Unsold' tabs as well")
                    print()
                elif status == 'PUBLISHED':
                    print("[INFO] Offer is PUBLISHED")
                    print("       Check 'Active' listings, not 'Drafts'")
                    print()
                else:
                    print(f"[INFO] Offer status: {status}")
                    print()
                
                # Check if it's part of a group
                print("Checking if offer is part of a group...")
                try:
                    # Try to get the inventory item to see if it has a group
                    item_response = client._make_request('GET', f'/sell/inventory/v1/inventory_item/{sku}')
                    if item_response.status_code == 200:
                        item_data = item_response.json()
                        group_key = item_data.get('inventoryItemGroupKeys', [])
                        if group_key:
                            print(f"  [OK] Item is part of group(s): {group_key}")
                            print()
                            print("  For variation listings, the GROUP needs to be published,")
                            print("  not just the individual offers.")
                            print()
                            print("  Try publishing the group:")
                            print(f"    python publish_draft.py {sku}")
                            print()
                        else:
                            print("  [INFO] Item is not part of a group")
                            print()
                except Exception as e:
                    print(f"  [INFO] Could not check group: {e}")
                    print()
            else:
                print("[ERROR] No offers found")
        else:
            print(f"[ERROR] Failed to get offer: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("Troubleshooting")
    print("=" * 80)
    print()
    print("If the draft isn't showing in Seller Hub:")
    print()
    print("1. Verify you're logged into the correct eBay account (manhattanbreaks)")
    print("2. Check all tabs: Drafts, Active, Unsold, Scheduled")
    print("3. Try searching by SKU: CARD_TEST_SET_TEST_CARD_1_0")
    print("4. Wait 2-3 minutes for eBay to sync")
    print("5. For variation listings, you may need to publish the GROUP, not just the offer")
    print()

if __name__ == "__main__":
    verify()
