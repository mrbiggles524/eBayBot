"""
Delete and recreate the offer AFTER the group exists so eBay properly links them.
This might make the draft visible in Seller Hub.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def recreate_offer():
    """Recreate offer after group exists."""
    print("=" * 80)
    print("Recreating Offer After Group Exists")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    
    group_key = "GROUPSET1768714571"
    sku = "CARD_SET_FINAL_TEST_CARD_1_0"
    offer_id = "965455487016"
    
    # Get current offer data
    print("Step 1: Getting current offer data...")
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    
    # Get valid policies
    print("Step 2: Getting valid policies...")
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
    
    # Delete the offer
    print()
    print("Step 3: Deleting existing offer...")
    delete_result = client._make_request('DELETE', f'/sell/inventory/v1/offer/{offer_id}')
    if delete_result.status_code in [200, 204]:
        print("[OK] Offer deleted")
        time.sleep(3)  # Wait for deletion to propagate
    else:
        print(f"[WARNING] Could not delete offer: {delete_result.status_code}")
        print("Continuing anyway...")
    
    print()
    print("Step 4: Creating new offer (group already exists)...")
    
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
    
    # Create new offer
    offer_data = {
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
    
    create_result = client.create_offer(offer_data)
    if not create_result.get('success'):
        print(f"[ERROR] Failed to create offer: {create_result.get('error')}")
        return
    
    new_offer_id = create_result.get('data', {}).get('offerId') or create_result.get('offerId')
    print(f"[OK] New offer created: {new_offer_id}")
    print()
    
    print("Step 5: Waiting 5 seconds for offer to be linked to group...")
    time.sleep(5)
    
    # Check if the new offer has the group key
    print()
    print("Step 6: Checking if offer is linked to group...")
    check_result = client.get_offer_by_sku(sku)
    if check_result.get('success'):
        check_offer = check_result.get('offer', {})
        check_group_key = check_offer.get('inventoryItemGroupKey')
        print(f"  Offer ID: {check_offer.get('offerId', 'N/A')}")
        print(f"  Status: {check_offer.get('status', 'N/A')}")
        print(f"  inventoryItemGroupKey: {check_group_key if check_group_key else 'N/A'}")
        
        if check_group_key == group_key:
            print("  [SUCCESS] Offer is now properly linked to group!")
            print("  The draft should now appear in Seller Hub.")
        elif check_group_key:
            print(f"  [WARNING] Group key is {check_group_key} (expected {group_key})")
        else:
            print("  [WARNING] Group key still missing")
            print("  eBay may need more time to link them")
            print("  Wait 1-2 minutes and check again")
    
    print()
    print("=" * 80)
    print("Offer Recreated")
    print("=" * 80)
    print()
    print("Check Seller Hub:")
    print("  1. Go to: https://www.ebay.com/sh/landing")
    print("  2. Navigate to: Listings -> Drafts")
    print("  3. Look for: 'Final Test Listing - Please Delete'")
    print()
    print("If it doesn't appear immediately, wait 1-2 minutes and refresh.")
    print()

if __name__ == "__main__":
    recreate_offer()
