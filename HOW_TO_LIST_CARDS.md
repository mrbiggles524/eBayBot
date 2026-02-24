# How to List a Card Set on eBay

## Quick Start

1. **Edit `list_card_set.py`** - Add your cards to the `CARD_DATA` list
2. **Run the script** - `python list_card_set.py`
3. **Confirm** - Type `YES` when prompted to publish

## Step-by-Step Guide

### Step 1: Prepare Your Card Data

Edit `list_card_set.py` and update these sections:

```python
# Set information
SET_NAME = "2024-25 Topps Chrome Basketball"
SET_DESCRIPTION = """<p><strong>Your Set Title</strong></p>
<p>Your description here...</p>"""

# Card data
CARD_DATA = [
    {"name": "LeBron James", "number": "1", "price": 5.00},
    {"name": "Stephen Curry", "number": "2", "price": 4.00},
    # Add more cards...
]
```

### Step 2: Card Data Format

Each card needs:
- `name` - Player name (required)
- `number` - Card number (required)
- `price` - Price in USD (optional, defaults to DEFAULT_PRICE)
- `image_url` - Image URL (optional, defaults to DEFAULT_IMAGE_URL)

Example:
```python
CARD_DATA = [
    {"name": "LeBron James", "number": "1", "price": 5.00},
    {"name": "Stephen Curry", "number": "2", "price": 4.00, "image_url": "https://your-image.jpg"},
]
```

### Step 3: Run the Script

```bash
python list_card_set.py
```

The script will:
1. Show you the cards to be listed
2. Create inventory items for each card
3. Create a variation group
4. Create offers with your prices
5. Ask for confirmation before publishing
6. Publish the listing

### Step 4: Confirm Publication

When prompted, type `YES` to publish the listing live on eBay.

## Important Notes

### Images
- Each card should have an image
- Use eBay-hosted images (upload via Seller Hub) or external URLs
- If no image is provided, a placeholder is used

### Prices
- Set individual prices per card, or use DEFAULT_PRICE for all
- Prices are in USD

### Categories
- Default category is 261328 (Sports Trading Cards)
- Change CATEGORY_ID if listing other types of cards

### Required Fields
The script automatically handles:
- Card Condition (Near Mint or Better)
- All required item specifics
- Shipping policies
- Return policies

## Managing Listings

### View Your Listings
- Go to: https://www.ebay.com/sh/lst/active
- Or use the web UI: http://localhost:5000

### Edit Prices/Quantity
Use the web UI at http://localhost:5000 to:
- View listing details
- Update prices
- Update quantities
- Delete listings

### End a Listing
1. Go to eBay Seller Hub
2. Find the listing
3. Click "End listing"

## Troubleshooting

### "Missing required policies"
Set up your business policies in eBay Seller Hub:
- Payment policy
- Shipping/fulfillment policy
- Return policy

### "Image required"
Add image URLs to your card data or update DEFAULT_IMAGE_URL

### "Card Condition required"
The script handles this automatically with conditionDescriptors

## Example: Listing a Full Set

```python
SET_NAME = "2024-25 Topps Chrome Basketball Base Set"

CARD_DATA = [
    {"name": "LeBron James", "number": "1", "price": 5.00},
    {"name": "Stephen Curry", "number": "2", "price": 4.00},
    {"name": "Kevin Durant", "number": "3", "price": 3.50},
    {"name": "Giannis Antetokounmpo", "number": "4", "price": 3.00},
    {"name": "Luka Doncic", "number": "5", "price": 4.50},
    {"name": "Jayson Tatum", "number": "6", "price": 2.50},
    {"name": "Anthony Edwards", "number": "7", "price": 3.00},
    {"name": "Victor Wembanyama", "number": "8", "price": 8.00},
    {"name": "Ja Morant", "number": "9", "price": 2.00},
    {"name": "Nikola Jokic", "number": "10", "price": 3.50},
    # ... add all cards in the set
]

DEFAULT_PRICE = 1.00  # For commons not listed above
```

## Files Reference

- `list_card_set.py` - Main script to list a card set
- `listing_manager_ui.py` - Web UI for managing listings
- `ebay_api_client.py` - eBay API client
- `ebay_listing.py` - Core listing functions
