"""Check final listing and try to publish."""
from ebay_api_client import eBayAPIClient
import sys

sys.stdout.reconfigure(encoding='utf-8')

group_key = "GROUPSET1768714571"
client = eBayAPIClient()

print(f"Publishing group: {group_key}")
result = client.publish_offer_by_inventory_item_group(group_key, "EBAY_US")

if result.get('success'):
    listing_id = result.get('listing_id')
    print(f"\n[SUCCESS] Published! Listing ID: {listing_id}")
    print(f"View: https://www.ebay.com/itm/{listing_id}")
else:
    error = result.get('error', 'Unknown')
    print(f"\n[FAILED] {error}")
    print("\nListing saved as draft.")
    print(f"Group Key: {group_key}")
