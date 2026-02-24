"""
Fix the test offer by adding missing listing details.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def fix_offer():
    """Fix the test offer."""
    print("=" * 80)
    print("Fixing Test Offer - Adding Listing Details")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    sku = "CARD_TEST_SET_TEST_CARD_1_0"
    
    print(f"SKU: {sku}")
    print()
    
    # Get current offer
    print("Fetching current offer...")
    try:
        response = client._make_request('GET', f'/sell/inventory/v1/offer?sku={sku}')
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to get offer: {response.status_code}")
            return
        
        data = response.json()
        offers = data.get('offers', [])
        
        if not offers:
            print("[ERROR] No offer found")
            return
        
        offer = offers[0]
        offer_id = offer.get('offerId')
        
        print(f"[OK] Found offer: {offer_id}")
        print()
        
        # Update offer with listing details
        print("Updating offer with listing details...")
        
        update_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "categoryId": "261328",
            "listing": {
                "title": "Test Listing - Please Delete",
                "description": "This is a test listing. Please delete after testing.",
                "listingPolicies": {
                    "fulfillmentPolicyId": "6213866000",
                    "paymentPolicyId": "6213868000",
                    "returnPolicyId": "243552423019"
                },
                "itemSpecifics": {
                    "Type": ["Sports Trading Card"],
                    "Card Size": ["Standard"],
                    "Country of Origin": ["United States"],
                    "Language": ["English"],
                    "Original/Licensed Reprint": ["Original"],
                    "Card Name": ["Test Card"],
                    "Card Number": ["1"]
                }
            },
            "listingPolicies": {
                "fulfillmentPolicyId": "6213866000",
                "paymentPolicyId": "6213868000",
                "returnPolicyId": "243552423019"
            },
            "pricingSummary": {
                "price": {
                    "value": "1.0",
                    "currency": "USD"
                }
            },
            "quantity": 1,
            "availableQuantity": 1,
            "listingDuration": "GTC",
            "merchantLocationKey": "046afc77-1256-4755-9dae-ab4ebe56c8cc"
        }
        
        print("Updating offer...")
        update_response = client._make_request('PUT', f'/sell/inventory/v1/offer/{offer_id}', data=update_data)
        
        if update_response.status_code in [200, 204]:
            print("[SUCCESS] Offer updated!")
            print()
            print("The draft should now appear in Seller Hub.")
            print()
            print("Check:")
            print("  1. Refresh Seller Hub drafts page")
            print("  2. Look for 'Test Listing - Please Delete'")
            print("  3. Or search by SKU: CARD_TEST_SET_TEST_CARD_1_0")
        else:
            print(f"[ERROR] Failed to update offer: {update_response.status_code}")
            print(f"Response: {update_response.text}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_offer()
