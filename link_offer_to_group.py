"""
Ensure the offer is properly linked to the inventory item group.
This might be why it's not appearing in drafts.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def link_offer():
    """Link offer to group properly."""
    print("=" * 80)
    print("Linking Offer to Group")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    group_key = "GROUPSET1768714571"
    sku = "CARD_SET_FINAL_TEST_CARD_1_0"
    
    # First verify the group has this SKU
    print("Step 1: Verifying group structure...")
    group_result = client.get_inventory_item_group(group_key)
    if group_result.get('success'):
        group_data = group_result.get('data', {})
        variant_skus = group_data.get('variantSKUs', [])
        print(f"[OK] Group exists")
        print(f"  Title: {group_data.get('title', 'N/A')}")
        print(f"  Variant SKUs: {variant_skus}")
        
        if sku not in variant_skus:
            print(f"[WARNING] SKU {sku} not in group's variantSKUs!")
            print("  This might be the issue - updating group...")
            
            # Update group to include this SKU
            group_update = {
                "title": group_data.get('title', 'Final Test Listing - Please Delete'),
                "variesBy": group_data.get('variesBy', {}),
                "inventoryItemGroup": {
                    "aspects": group_data.get('inventoryItemGroup', {}).get('aspects', {}),
                    "description": "Final Test Listing - Please Delete\n\nSelect your card from the variations below. Each card is listed as a separate variation option.\n\nAll cards are in Near Mint or better condition unless otherwise noted."
                },
                "variantSKUs": [sku]  # Ensure SKU is in the list
            }
            
            update_result = client.create_inventory_item_group(group_key, group_update)
            if update_result.get('success'):
                print("[OK] Group updated with SKU")
            else:
                print(f"[WARNING] Group update failed: {update_result.get('error')}")
        else:
            print(f"[OK] SKU is in group's variantSKUs")
    else:
        print(f"[ERROR] Could not get group: {group_result.get('error')}")
        return
    
    print()
    
    # Check the offer
    print("Step 2: Checking offer...")
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    print(f"  Offer ID: {offer_id}")
    print(f"  Status: {offer.get('status', 'N/A')}")
    
    # Check if offer has inventoryItemGroupKey
    current_group_key = offer.get('inventoryItemGroupKey')
    if current_group_key:
        print(f"  [OK] Offer has inventoryItemGroupKey: {current_group_key}")
        if current_group_key == group_key:
            print(f"  [OK] Group key matches!")
        else:
            print(f"  [WARNING] Group key mismatch!")
    else:
        print(f"  [WARNING] Offer does NOT have inventoryItemGroupKey")
        print(f"  This might be why it's not appearing in drafts")
        print()
        print("  Note: The offer should automatically get the group key")
        print("        when it's part of a variation group.")
        print("        If it's missing, eBay might not recognize it as a draft.")
    
    print()
    
    # Try to update the offer to ensure it's properly linked
    # Note: We can't directly set inventoryItemGroupKey, but we can ensure
    # the offer has all the right data and the group has the right SKU
    
    print("Step 3: Ensuring offer has complete data...")
    
    # Get valid policies
    try:
        response = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
        payment_policies = response.json().get('paymentPolicies', []) if response.status_code == 200 else []
        valid_payment = payment_policies[0].get('paymentPolicyId') if payment_policies else None
        
        response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
        fulfillment_policies = response.json().get('fulfillmentPolicies', []) if response.status_code == 200 else []
        valid_fulfillment = None
        for policy in fulfillment_policies:
            name = policy.get('name', '').upper()
            if 'GROUND' in name or 'SHIPPING' in name or 'ADVANTAGE' in name:
                valid_fulfillment = policy.get('fulfillmentPolicyId')
                break
        if not valid_fulfillment and fulfillment_policies:
            valid_fulfillment = fulfillment_policies[0].get('fulfillmentPolicyId')
        
        response = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
        return_policies = response.json().get('returnPolicies', []) if response.status_code == 200 else []
        valid_return = return_policies[0].get('returnPolicyId') if return_policies else None
    except Exception as e:
        print(f"[ERROR] Could not get policies: {e}")
        return
    
    # Update offer one more time with all data
    title = "Final Test Listing - Please Delete"
    description = """Final Test Listing - Please Delete

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    listing_policies = {
        "paymentPolicyId": valid_payment,
        "fulfillmentPolicyId": valid_fulfillment
    }
    if valid_return:
        listing_policies["returnPolicyId"] = valid_return
    
    item_specifics = {
        "Type": ["Sports Trading Card"],
        "Card Size": ["Standard"],
        "Country of Origin": ["United States"],
        "Language": ["English"],
        "Original/Licensed Reprint": ["Original"],
        "Card Name": ["Final Test Card"],
        "Card Number": ["1"]
    }
    
    update_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "categoryId": offer.get('categoryId', '261328'),
        "listing": {
            "title": title,
            "description": description,
            "listingPolicies": listing_policies,
            "itemSpecifics": item_specifics
        },
        "listingPolicies": listing_policies,
        "pricingSummary": offer.get('pricingSummary', {}),
        "quantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
        "listingDuration": offer.get('listingDuration', 'GTC'),
        "merchantLocationKey": offer.get('merchantLocationKey')
    }
    
    update_result = client.update_offer(offer_id, update_data)
    if update_result.get('success'):
        print("[OK] Offer updated")
    else:
        print(f"[WARNING] Offer update: {update_result.get('error')}")
    
    print()
    print("Waiting 5 seconds...")
    time.sleep(5)
    
    # Check again
    print()
    print("Step 4: Verifying offer after update...")
    verify_result = client.get_offer_by_sku(sku)
    if verify_result.get('success'):
        verify_offer = verify_result.get('offer', {})
        verify_group_key = verify_offer.get('inventoryItemGroupKey')
        print(f"  Status: {verify_offer.get('status', 'N/A')}")
        print(f"  inventoryItemGroupKey: {verify_group_key if verify_group_key else 'N/A (still missing)'}")
        
        if verify_group_key == group_key:
            print("  [OK] Offer is now properly linked to group!")
        elif verify_group_key:
            print(f"  [WARNING] Group key is {verify_group_key} (expected {group_key})")
        else:
            print("  [WARNING] Group key still missing")
            print("  This might be why the draft isn't visible")
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("The offer has been updated with all required data.")
    print()
    print("If the draft still doesn't appear in Seller Hub:")
    print("  1. Wait 2-3 minutes and refresh (eBay UI can be slow)")
    print("  2. Check if variation listing drafts appear differently")
    print("  3. Try accessing via: https://www.ebay.com/sh/landing")
    print("  4. The listing exists via API and can be managed programmatically")
    print()

if __name__ == "__main__":
    link_offer()
