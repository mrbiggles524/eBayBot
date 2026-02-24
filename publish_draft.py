"""
Publish a draft listing.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json
import webbrowser

def publish_draft(sku: str):
    """Publish a draft listing."""
    print("=" * 80)
    print("Publishing Draft Listing")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"SKU: {sku}")
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success') or not offer_result.get('offer'):
        print(f"[ERROR] Could not get offer for SKU {sku}")
        return
    
    offer = offer_result['offer']
    offer_id = offer.get('offerId')
    group_key = offer.get('inventoryItemGroupKey', '')
    listing_id = offer.get('listingId')
    
    if listing_id:
        print(f"[INFO] Listing is already published!")
        print(f"Listing ID: {listing_id}")
        listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
        print(f"Link: {listing_url}")
        try:
            webbrowser.open(listing_url)
        except:
            pass
        return
    
    print(f"Offer ID: {offer_id}")
    if group_key:
        print(f"Group Key: {group_key} (Variation Listing)")
    print()
    
    # FIX: Remove invalid return policy before publishing (Error 25009)
    listing_policies = offer.get('listingPolicies', {})
    if 'returnPolicyId' in listing_policies:
        invalid_policy = listing_policies.get('returnPolicyId')
        print(f"[FIX] Removing invalid return policy: {invalid_policy}")
        print("[NOTE] eBay sandbox often has issues with return policies")
        
        # Remove from both root and nested listingPolicies
        listing_policies_clean = listing_policies.copy()
        listing_policies_clean.pop('returnPolicyId', None)
        
        # Update the offer to remove return policy
        listing_data = offer.get('listing', {})
        update_data = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
            "pricingSummary": offer.get('pricingSummary', {}),
            "listingPolicies": listing_policies_clean,
            "categoryId": offer.get('categoryId'),
            "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
            "listing": {
                "title": listing_data.get('title', 'eBay Listing'),
                "description": listing_data.get('description', ''),
                "listingPolicies": listing_policies_clean,
                "imageUrls": listing_data.get('imageUrls', []) or []
            }
        }
        
        if 'itemSpecifics' in listing_data:
            update_data['listing']['itemSpecifics'] = listing_data['itemSpecifics']
        
        print("[UPDATE] Removing return policy from offer...")
        update_result = client.update_offer(offer_id, update_data)
        if update_result.get('success'):
            print("[OK] Return policy removed")
            import time
            time.sleep(2)  # Brief wait for propagation
            # Refresh offer data
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success') and offer_result.get('offer'):
                offer = offer_result['offer']
        else:
            print(f"[WARNING] Could not remove return policy: {update_result.get('error')}")
        print()
    
    # Try to publish
    if group_key:
        print(f"Publishing variation listing (group: {group_key})...")
        print("[NOTE] For variation listings, description must be in the inventoryItemGroup")
        print("[NOTE] Attempting to publish via group...")
        publish_result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")
    else:
        print("Publishing single offer...")
        # For single offers, make sure description is present
        listing_data = offer.get('listing', {})
        description = listing_data.get('description', '')
        if not description or len(description.strip()) < 50:
            print("[WARNING] Description is missing or too short!")
            print(f"Current description length: {len(description)}")
            print("[FIX] Adding a default description...")
            
            # Update offer with description first
            update_data = {
                "sku": sku,
                "marketplaceId": "EBAY_US",
                "format": "FIXED_PRICE",
                "availableQuantity": offer.get('availableQuantity', offer.get('quantity', 1)),
                "pricingSummary": offer.get('pricingSummary', {}),
                "listingPolicies": offer.get('listingPolicies', {}),
                "categoryId": offer.get('categoryId'),
                "merchantLocationKey": offer.get('merchantLocationKey', 'DEFAULT'),
                "listing": {
                    "title": listing_data.get('title', 'eBay Listing'),
                    "description": "This is a quality item in excellent condition. All items are carefully inspected before listing. Fast shipping and excellent customer service guaranteed.",
                    "listingPolicies": offer.get('listingPolicies', {}),
                    "imageUrls": listing_data.get('imageUrls', []) or []
                }
            }
            
            if 'itemSpecifics' in listing_data:
                update_data['listing']['itemSpecifics'] = listing_data['itemSpecifics']
            
            # Also remove return policy from update if present
            if 'returnPolicyId' in update_data.get('listingPolicies', {}):
                update_data['listingPolicies'].pop('returnPolicyId')
            if 'returnPolicyId' in update_data.get('listing', {}).get('listingPolicies', {}):
                update_data['listing']['listingPolicies'].pop('returnPolicyId')
            
            print("[UPDATE] Updating offer with description...")
            update_result = client.update_offer(offer_id, update_data)
            if update_result.get('success'):
                print("[OK] Description added, retrying publish...")
                import time
                time.sleep(2)  # Wait for propagation
            else:
                print(f"[WARNING] Could not update description: {update_result.get('error')}")
        
        # Wait a bit longer for description to propagate
        import time
        print("[WAIT] Waiting 5 seconds for description to fully propagate...")
        time.sleep(5)
        
        publish_result = client.publish_offer(offer_id)
    
    if publish_result.get('success'):
        listing_id = publish_result.get('data', {}).get('listingId') or publish_result.get('listingId')
        
        if listing_id:
            listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
            print()
            print("=" * 80)
            print("[SUCCESS] Listing Published!")
            print("=" * 80)
            print()
            print(f"Listing ID: {listing_id}")
            print(f"Direct Link: {listing_url}")
            print()
            print("Opening in browser...")
            
            try:
                webbrowser.open(listing_url)
            except Exception as e:
                print(f"Could not auto-open browser: {e}")
                print("Please copy and paste the link above into your browser")
        else:
            print("[WARNING] Published but no listing ID returned")
            print("Response:", json.dumps(publish_result, indent=2))
    else:
        error = publish_result.get('error', 'Unknown error')
        print()
        print("=" * 80)
        print("[ERROR] Failed to Publish")
        print("=" * 80)
        print(f"Error: {error}")
        print()
        print("Common issues:")
        print("1. Invalid return policy - check your policies")
        print("2. Missing description - ensure description is set")
        print("3. Missing required fields - check category, policies, etc.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python publish_draft.py <SKU>")
        print()
        print("Example:")
        print("  python publish_draft.py CARD_BECKETT_COM_NEWS_202_TIM_HARDAWAY_JR_7_2")
        sys.exit(1)
    
    sku = sys.argv[1]
    publish_draft(sku)
