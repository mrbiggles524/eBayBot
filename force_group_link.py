"""
Wait and then update the group to force eBay to link the offer.
"""
from ebay_api_client import eBayAPIClient
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def force_link():
    """Force eBay to link offer to group."""
    client = eBayAPIClient()
    
    group_key = "GROUPSET1768714571"
    sku = "CARD_SET_FINAL_TEST_CARD_1_0"
    
    print("Waiting 10 seconds for eBay to process...")
    time.sleep(10)
    
    print("Updating group to force link recognition...")
    
    # Get group first
    group_result = client.get_inventory_item_group(group_key)
    if not group_result.get('success'):
        print("[ERROR] Could not get group")
        return
    
    group_data = group_result.get('data', {})
    
    # Update group with the same data to force refresh
    group_update = {
        "title": group_data.get('title', 'Final Test Listing - Please Delete'),
        "variesBy": group_data.get('variesBy', {}),
        "inventoryItemGroup": {
            "aspects": {
                "Card Name": ["Final Test Card"],
                "Card Number": ["1"]
            },
            "description": "Final Test Listing - Please Delete\n\nSelect your card from the variations below. Each card is listed as a separate variation option.\n\nAll cards are in Near Mint or better condition unless otherwise noted."
        },
        "variantSKUs": [sku]  # Ensure SKU is in list
    }
    
    update_result = client.create_inventory_item_group(group_key, group_update)
    if update_result.get('success'):
        print("[OK] Group updated")
    else:
        print(f"[WARNING] Group update: {update_result.get('error')}")
    
    print()
    print("Waiting 5 more seconds...")
    time.sleep(5)
    
    # Check offer again
    print("Checking offer...")
    offer_result = client.get_offer_by_sku(sku)
    if offer_result.get('success'):
        offer = offer_result.get('offer', {})
        group_key_in_offer = offer.get('inventoryItemGroupKey')
        print(f"  Offer ID: {offer.get('offerId', 'N/A')}")
        print(f"  Status: {offer.get('status', 'N/A')}")
        print(f"  inventoryItemGroupKey: {group_key_in_offer if group_key_in_offer else 'Still missing'}")
        
        if group_key_in_offer == group_key:
            print()
            print("[SUCCESS] Offer is now linked to group!")
            print("The draft should appear in Seller Hub.")
        else:
            print()
            print("[NOTE] Group key still not set automatically by eBay")
            print("This might be an eBay API limitation.")
            print("The listing exists and can be managed via API.")
    
    print()
    print("Final check - please check Seller Hub:")
    print("  https://www.ebay.com/sh/landing -> Listings -> Drafts")
    print()
    print("If it's still not there, the listing exists via API:")
    print(f"  Group Key: {group_key}")
    print(f"  SKU: {sku}")
    print(f"  Offer ID: {offer.get('offerId', 'N/A')}")
    print()

if __name__ == "__main__":
    force_link()
