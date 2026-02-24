# eBay Listing Management via API

Since variation listing drafts created via API may not appear in eBay Seller Hub, use the API to manage them directly.

## Quick Start

### 1. View Your Listings

```python
from manage_listings_api import ListingManager

manager = ListingManager()

# List known test listings
manager.list_test_listings()

# View details of a specific group
manager.display_group_info('GROUPSAHF8A3F381768715399')

# Get offer details by SKU
offer = manager.get_offer_by_sku('CARD_DIFF_APPROACH_TEST_1_0')
```

### 2. Update Listings

```python
# Update price
manager.update_offer_price('CARD_DIFF_APPROACH_TEST_1_0', 2.50)

# Update quantity
manager.update_offer_quantity('CARD_DIFF_APPROACH_TEST_1_0', 5)

# Update group title
manager.update_group_title('GROUPSAHF8A3F381768715399', 'New Title')
```

### 3. Delete Listings

```python
# Delete a group (and all its offers)
manager.delete_group('GROUPSAHF8A3F381768715399')
```

## Available Methods

### `list_test_listings()`
Lists all known test listings with their status.

### `display_group_info(group_key)`
Shows detailed information about a variation listing group:
- Title
- Variant SKUs
- Variation specifications
- Offer details (price, quantity, status)

### `get_offer_by_sku(sku)`
Gets offer details for a specific SKU:
- Offer ID
- Listing status
- Price
- Quantity
- Policies

### `update_offer_price(sku, new_price)`
Updates the price of an offer.

### `update_offer_quantity(sku, new_quantity)`
Updates the quantity of an offer.

### `update_group_title(group_key, new_title)`
Updates the title of a variation listing group.

### `delete_group(group_key)`
Deletes a group and all associated offers.

## Finding Your Listings

eBay API doesn't provide a "list all groups" endpoint. You need to:

1. **Track group keys** when creating listings (save them in your database/logs)
2. **Query by SKU** if you know the SKU pattern
3. **Use the test listings list** for known test listings

## Example Workflow

```python
from manage_listings_api import ListingManager

manager = ListingManager()

# 1. List your listings
manager.list_test_listings()

# 2. View details of one
manager.display_group_info('GROUPSAHF8A3F381768715399')

# 3. Update it
manager.update_offer_price('CARD_DIFF_APPROACH_TEST_1_0', 2.50)
manager.update_offer_quantity('CARD_DIFF_APPROACH_TEST_1_0', 5)

# 4. Verify changes
manager.display_group_info('GROUPSAHF8A3F381768715399')
```

## Important Notes

1. **Drafts may not appear in Seller Hub** - This is an eBay UI limitation
2. **Listings exist via API** - They are created and can be managed via API
3. **Publishing fails** - Due to Error 25016 (eBay API bug)
4. **Use API for management** - Until eBay fixes the issues

## Tracking Your Listings

To keep track of your listings, consider:

1. **Save group keys and SKUs** when creating listings
2. **Use a database** to store listing metadata
3. **Log creation** in a file or database
4. **Use consistent SKU patterns** to identify your listings

Example tracking:
```python
# When creating a listing, save the info:
listing_info = {
    "group_key": "GROUPSAHF8A3F381768715399",
    "sku": "CARD_DIFF_APPROACH_TEST_1_0",
    "title": "Different Approach Test",
    "created_at": "2026-01-18",
    "status": "UNPUBLISHED"
}

# Save to file or database
import json
with open('my_listings.json', 'a') as f:
    f.write(json.dumps(listing_info) + '\n')
```

## Common Operations

### Check if a listing exists
```python
offer = manager.get_offer_by_sku('YOUR_SKU')
if offer:
    print(f"Status: {offer.get('listingStatus')}")
else:
    print("Listing not found")
```

### Update multiple listings
```python
listings = [
    ('CARD_DIFF_APPROACH_TEST_1_0', 2.50),
    ('CARD_SET_NORMAL_FLOW_TEST_CAR_1_0', 3.00),
]

for sku, price in listings:
    manager.update_offer_price(sku, price)
```

### Bulk delete test listings
```python
test_groups = [
    'GROUPSAHF8A3F381768715399',
    'GROUPSET1768715280',
    'GROUPSET1768714571',
]

for group_key in test_groups:
    manager.delete_group(group_key)
```
