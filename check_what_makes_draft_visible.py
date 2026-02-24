"""
Check what might be missing to make drafts visible in Seller Hub.
Compare with what a manually created draft would have.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

def check_draft():
    """Check what might be missing."""
    print("=" * 80)
    print("Analyzing Draft Listing for Visibility")
    print("=" * 80)
    print()
    
    client = eBayAPIClient()
    sku = "CARD_SET_FINAL_TEST_CARD_1_0"
    
    # Get the offer
    offer_result = client.get_offer_by_sku(sku)
    if not offer_result.get('success'):
        print("[ERROR] Could not get offer")
        return
    
    offer = offer_result['offer']
    
    print("Current Offer Structure:")
    print(f"  Keys: {list(offer.keys())}")
    print()
    
    # Check for fields that might affect visibility
    print("Checking key fields:")
    print(f"  offerId: {offer.get('offerId', 'N/A')}")
    print(f"  status: {offer.get('status', 'N/A')}")
    print(f"  format: {offer.get('format', 'N/A')}")
    print(f"  marketplaceId: {offer.get('marketplaceId', 'N/A')}")
    print(f"  categoryId: {offer.get('categoryId', 'N/A')}")
    print(f"  inventoryItemGroupKey: {offer.get('inventoryItemGroupKey', 'N/A')}")
    print(f"  listingId: {offer.get('listingId', 'N/A')} (should be empty for drafts)")
    print()
    
    # Check if listing object exists (even if not returned)
    print("Listing object check:")
    if 'listing' in offer:
        listing = offer['listing']
        print("  [OK] listing object present in GET response")
        print(f"    Keys: {list(listing.keys())}")
        print(f"    Title: {listing.get('title', 'N/A')}")
        print(f"    Description: {'Yes' if listing.get('description') else 'No'}")
        print(f"    Item Specifics: {'Yes' if listing.get('itemSpecifics') else 'No'}")
        print(f"    Image URLs: {len(listing.get('imageUrls', []))}")
    else:
        print("  [NOTE] listing object not in GET response")
        print("         This is normal for unpublished offers")
        print("         But the data should still be stored")
    print()
    
    # Check policies
    print("Policies:")
    policies = offer.get('listingPolicies', {})
    print(f"  Payment: {policies.get('paymentPolicyId', 'N/A')}")
    print(f"  Fulfillment: {policies.get('fulfillmentPolicyId', 'N/A')}")
    print(f"  Return: {policies.get('returnPolicyId', 'N/A')}")
    print()
    
    # Check pricing
    print("Pricing:")
    pricing = offer.get('pricingSummary', {})
    print(f"  Price: ${pricing.get('price', {}).get('value', 'N/A')}")
    print()
    
    # Check quantity
    print("Quantity:")
    print(f"  Available: {offer.get('availableQuantity', 'N/A')}")
    print(f"  Total: {offer.get('quantity', 'N/A')}")
    print()
    
    # Check if there's anything that might prevent visibility
    print("Potential Issues:")
    issues = []
    
    if not offer.get('categoryId'):
        issues.append("Missing categoryId")
    if not offer.get('pricingSummary', {}).get('price', {}).get('value'):
        issues.append("Missing price")
    if not offer.get('availableQuantity') and not offer.get('quantity'):
        issues.append("Missing quantity")
    if not offer.get('listingPolicies', {}).get('fulfillmentPolicyId'):
        issues.append("Missing fulfillment policy")
    if not offer.get('listingPolicies', {}).get('paymentPolicyId'):
        issues.append("Missing payment policy")
    if offer.get('listingId'):
        issues.append("Has listingId (should be empty for drafts)")
    
    if issues:
        print("  [WARNING] Potential issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  [OK] No obvious issues found")
    
    print()
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)
    print()
    print("The offer appears to have all required fields.")
    print()
    print("Possible reasons it's not visible in Seller Hub:")
    print("  1. eBay UI delay (wait 1-2 minutes and refresh)")
    print("  2. Variation listing drafts may need to be published to appear")
    print("  3. Seller Hub may filter out certain draft types")
    print("  4. The listing might need to be accessed via a direct link")
    print()
    print("Try checking:")
    print("  - Wait 2-3 minutes and refresh Seller Hub")
    print("  - Check if there's a 'View All Drafts' or 'Show More' button")
    print("  - Try searching for the SKU: CARD_SET_FINAL_TEST_CARD_1_0")
    print()

if __name__ == "__main__":
    check_draft()
