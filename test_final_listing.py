"""
Create one final test listing and try to publish it.
"""
from ebay_listing import eBayListingManager
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

def test_final():
    """Create and publish final test listing."""
    print("=" * 80)
    print("Final Test Listing - Create and Publish")
    print("=" * 80)
    print()
    
    config = Config()
    manager = eBayListingManager()
    client = eBayAPIClient()
    
    # Create a simple test listing
    title = "Final Test Listing - Please Delete"
    description = """Final Test Listing - Please Delete

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
    
    cards = [
        {
            "name": "Final Test Card",
            "number": "1"
        }
    ]
    
    print("Step 1: Creating listing...")
    print(f"Title: {title}")
    print(f"Cards: {len(cards)}")
    print()
    
    try:
        result = manager.create_variation_listing(
            cards=cards,
            title=title,
            description=description,
            category_id="261328",  # Trading Cards
            price=1.00,
            quantity=1,
            publish=False  # Create as draft first
        )
        
        if not result.get('success'):
            error = result.get('error', 'Unknown error')
            print(f"[ERROR] Failed to create listing: {error}")
            return
        
        group_key = result.get('group_key')
        skus = result.get('skus', [])
        
        print("=" * 80)
        print("[SUCCESS] Listing Created!")
        print("=" * 80)
        print()
        print(f"Group Key: {group_key}")
        print(f"SKUs: {skus}")
        print()
        
        # Get valid policies
        print("Step 2: Getting valid policies...")
        try:
            response = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
            if response.status_code == 200:
                payment_policies = response.json().get('paymentPolicies', [])
                valid_payment = payment_policies[0].get('paymentPolicyId') if payment_policies else None
            else:
                valid_payment = None
        except:
            valid_payment = None
        
        try:
            response = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
            if response.status_code == 200:
                fulfillment_policies = response.json().get('fulfillmentPolicies', [])
                valid_fulfillment = None
                for policy in fulfillment_policies:
                    name = policy.get('name', '').upper()
                    if 'GROUND' in name or 'SHIPPING' in name or 'ADVANTAGE' in name:
                        valid_fulfillment = policy.get('fulfillmentPolicyId')
                        break
                if not valid_fulfillment and fulfillment_policies:
                    valid_fulfillment = fulfillment_policies[0].get('fulfillmentPolicyId')
            else:
                valid_fulfillment = None
        except:
            valid_fulfillment = None
        
        try:
            response = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
            if response.status_code == 200:
                return_policies = response.json().get('returnPolicies', [])
                valid_return = return_policies[0].get('returnPolicyId') if return_policies else None
            else:
                valid_return = None
        except:
            valid_return = None
        
        if not valid_payment or not valid_fulfillment:
            print("[ERROR] Could not get valid policies")
            return
        
        print(f"  Payment: {valid_payment}")
        print(f"  Fulfillment: {valid_fulfillment}")
        print(f"  Return: {valid_return}")
        print()
        
        # Update offer with valid policies
        if skus:
            sku = skus[0]
            print(f"Step 3: Updating offer {sku} with valid policies...")
            
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result['offer']
                offer_id = offer.get('offerId')
                
                listing_policies = {
                    "paymentPolicyId": valid_payment,
                    "fulfillmentPolicyId": valid_fulfillment
                }
                
                if valid_return:
                    listing_policies["returnPolicyId"] = valid_return
                
                update_data = {
                    "sku": sku,
                    "marketplaceId": "EBAY_US",
                    "format": "FIXED_PRICE",
                    "categoryId": offer.get('categoryId'),
                    "listing": {
                        "title": title,
                        "description": description,
                        "listingPolicies": listing_policies
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
            print("Step 4: Waiting 3 seconds...")
            time.sleep(3)
            print()
            
            print("Step 5: Attempting to publish...")
            publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
            
            if publish_result.get('success'):
                listing_id = publish_result.get('listing_id')
                print()
                print("=" * 80)
                print("[SUCCESS] Listing Published!")
                print("=" * 80)
                print()
                print(f"Listing ID: {listing_id}")
                print()
                print("View your listing:")
                print(f"  https://www.ebay.com/itm/{listing_id}")
                print()
                print("Check Seller Hub -> Listings -> Active")
                print()
            else:
                error = publish_result.get('error', 'Unknown error')
                print()
                print("=" * 80)
                print("[INFO] Publish Failed - Listing Saved as Draft")
                print("=" * 80)
                print()
                print(f"Error: {error}")
                print()
                print("The listing has been created as a draft.")
                print(f"Group Key: {group_key}")
                print(f"SKU: {sku}")
                print()
                print("You can:")
                print("  1. Try publishing from Seller Hub UI")
                print("  2. Check if it appears in Seller Hub -> Drafts")
                print("  3. Wait and try again later")
                print()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final()
