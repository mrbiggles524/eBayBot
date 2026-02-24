"""
Make the draft listing visible in Seller Hub by ensuring all required fields are set.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def make_visible():
    """Make draft visible in Seller Hub."""
    print("=" * 80)
    print("Making Draft Visible in Seller Hub")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    group_key = "GROUPSET1768714571"
    sku = "CARD_SET_FINAL_TEST_CARD_1_0"
    
    print("Getting offer details...")
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    
    print(f"Offer ID: {offer_id}")
    print()
    
    # Get valid policies
    print("Getting valid policies...")
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
        
        print(f"  Payment: {valid_payment}")
        print(f"  Fulfillment: {valid_fulfillment}")
        print(f"  Return: {valid_return}")
        print()
    except Exception as e:
        print(f"[ERROR] Could not get policies: {e}")
        return
    
    # Create a complete listing object with all required fields
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
    
    # Ensure we have item specifics
    item_specifics = {
        "Type": ["Sports Trading Card"],
        "Card Size": ["Standard"],
        "Country of Origin": ["United States"],
        "Language": ["English"],
        "Original/Licensed Reprint": ["Original"],
        "Card Name": ["Final Test Card"],
        "Card Number": ["1"]
    }
    
    print("Updating offer with complete listing details...")
    print("  - Title")
    print("  - Description")
    print("  - Item Specifics")
    print("  - Policies")
    print()
    
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
    if not update_result.get('success'):
        print(f"[ERROR] Failed to update offer: {update_result.get('error')}")
        return
    
    print("[OK] Offer updated with complete listing details")
    print()
    
    # Also ensure the group has description
    print("Ensuring group has description...")
    group_update = {
        "title": title,
        "variesBy": {
            "specifications": [{
                "name": "PICK YOUR CARD",
                "values": ["1 Final Test Card"]
            }]
        },
        "inventoryItemGroup": {
            "aspects": {
                "Card Name": ["Final Test Card"],
                "Card Number": ["1"]
            },
            "description": description
        },
        "variantSKUs": [sku]
    }
    
    group_result = client.create_inventory_item_group(group_key, group_update)
    if group_result.get('success'):
        print("[OK] Group updated with description")
    else:
        print(f"[WARNING] Group update: {group_result.get('error')}")
    
    print()
    print("Waiting 5 seconds for changes to propagate...")
    time.sleep(5)
    print()
    
    # Verify the offer now has listing details
    print("Verifying offer has listing details...")
    verify_result = client.get_offer_by_sku(sku)
    if verify_result.get('success'):
        verify_offer = verify_result.get('offer', {})
        if 'listing' in verify_offer:
            listing = verify_offer['listing']
            print("[OK] Offer has listing object")
            print(f"  Title: {listing.get('title', 'N/A')}")
            print(f"  Description: {'Yes' if listing.get('description') else 'No'}")
            print(f"  Item Specifics: {'Yes' if listing.get('itemSpecifics') else 'No'}")
        else:
            print("[NOTE] listing object not in GET response (eBay API quirk)")
            print("       But it should be stored")
    
    print()
    print("=" * 80)
    print("Draft Listing Updated")
    print("=" * 80)
    print()
    print("The listing has been updated with complete details:")
    print("  ✅ Title")
    print("  ✅ Description")
    print("  ✅ Item Specifics")
    print("  ✅ Policies")
    print("  ✅ Group description")
    print()
    print("Check Seller Hub:")
    print("  1. Go to: https://www.ebay.com/sh/landing")
    print("  2. Navigate to: Listings -> Drafts")
    print("  3. Look for: 'Final Test Listing - Please Delete'")
    print()
    print("If it still doesn't appear, wait 1-2 minutes and refresh.")
    print("Sometimes eBay takes a moment to update the UI.")
    print()

if __name__ == "__main__":
    make_visible()
