"""Check if a listing is a variation (has group key) or single."""
from ebay_api_client import eBayAPIClient
import sys

sku = sys.argv[1] if len(sys.argv) > 1 else 'CARD_BECKETT_COM_NEWS_202_TIM_HARDAWAY_JR_7_2'

client = eBayAPIClient()
result = client.get_offer_by_sku(sku)

if result.get('success') and result.get('offer'):
    offer = result['offer']
    group_key = offer.get('inventoryItemGroupKey', '')
    
    print(f"SKU: {sku}")
    print(f"Offer ID: {offer.get('offerId')}")
    print(f"Group Key: {group_key if group_key else 'None (Single Listing)'}")
    print()
    
    if group_key:
        print("This is a VARIATION LISTING (group)")
        print("Must publish via: publish_offer_by_inventory_item_group")
        print()
        print(f"To publish, the description must be in the inventoryItemGroup")
        print(f"Group key: {group_key}")
    else:
        print("This is a SINGLE LISTING")
        print("Can publish via: publish_offer")
else:
    print(f"Could not get offer for {sku}")
