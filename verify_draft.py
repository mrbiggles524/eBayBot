"""Verify if a draft listing was created and where to find it."""
import sys
from ebay_api_client import eBayAPIClient
from ebay_listing import eBayListingManager

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("Verify Draft Listing")
print("=" * 70)
print()

group_key = input("Enter Group Key (from draft creation): ").strip()

if not group_key:
    print("Error: Group key required")
    sys.exit(1)

print()
print("Checking draft listing status...")
print()

client = eBayAPIClient()

# Check if group exists
print("1. Checking inventory item group...")
group_result = client.get_inventory_item_group(group_key)
if group_result.get('success'):
    group_data = group_result.get('data', {})
    print(f"   ✓ Group exists: {group_key}")
    print(f"   Title: {group_data.get('title', 'N/A')}")
    variant_skus = group_data.get('variantSKUs', [])
    print(f"   Variants: {len(variant_skus)} SKUs")
else:
    print(f"   ✗ Group not found: {group_result.get('error')}")
    sys.exit(1)

print()

# Check offers
print("2. Checking offers...")
offer_count = 0
for sku in variant_skus[:5]:  # Check first 5
    offer_result = client.get_offer_by_sku(sku)
    if offer_result.get('success'):
        offer = offer_result.get('offer', {})
        offer_id = offer.get('offerId')
        marketplace_id = offer.get('marketplaceId')
        print(f"   ✓ Offer exists: {sku} (ID: {offer_id})")
        offer_count += 1
    else:
        print(f"   ✗ Offer not found: {sku}")

print(f"\n   Found {offer_count}/{len(variant_skus)} offers")

print()
print("=" * 70)
print("Where to Find Your Draft")
print("=" * 70)
print()
print("Draft listings created via Inventory API may appear in:")
print()
print("1. Seller Hub > Listings > Unsold")
print("   https://www.ebay.com/sh/account/listings?status=UNSOLD")
print()
print("2. Seller Hub > Listings > Active Listings")
print("   https://www.ebay.com/sh/account/listings?status=ACTIVE")
print()
print("3. Seller Hub > Listings > Drafts (less common for Inventory API)")
print("   https://www.ebay.com/sh/account/listings?status=DRAFT")
print()
print("Note: Drafts may take 1-2 minutes to appear in Seller Hub.")
print("      If not visible, wait a few minutes and refresh.")
print()
print(f"Group Key: {group_key}")
print("Use this to search in Seller Hub if needed.")
