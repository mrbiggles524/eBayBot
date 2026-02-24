# CSV Import Format Guide

The eBay bot supports importing card data from CSV files. This is the most flexible way to list cards with custom pricing, quantities, and conditions per card.

## Required Columns

- `name` or `card_name` - The name of the card (required)
- `number` or `card_number` or `collector_number` - The card number in the set (required)

## Optional Columns

- `set_name` or `set` - Name of the card set
- `rarity` - Card rarity (Common, Uncommon, Rare, etc.)
- `price` - Price for this specific card (overrides --price argument)
- `quantity` - Quantity available for this card (overrides --quantity argument)
- `condition` - Condition of this card (overrides --condition argument)
- `image_url` or `image` - URL to card image
- `weight` - Weight in pounds (default: 0.1)

## Example CSV

```csv
name,number,set_name,rarity,price,quantity,condition,image_url
Lightning Bolt,1,Magic: The Gathering - Core Set 2021,Common,0.99,1,Near Mint,https://example.com/lightning_bolt.jpg
Counterspell,2,Magic: The Gathering - Core Set 2021,Uncommon,1.49,2,Near Mint,https://example.com/counterspell.jpg
Black Lotus,3,Magic: The Gathering - Core Set 2021,Rare,999.99,1,Near Mint,https://example.com/black_lotus.jpg
```

## Usage

```bash
# Import from CSV
python ebay_bot.py --csv cards.csv

# Import with custom title
python ebay_bot.py --csv cards.csv --title "My Card Collection"

# Import and use default price for cards without price column
python ebay_bot.py --csv cards.csv --price 0.99
```

## Notes

- Column names are case-insensitive and spaces are ignored
- If a card has a `price` column value, it will use that; otherwise it uses the `--price` argument
- Same logic applies to `quantity` and `condition` columns
- Any additional columns will be preserved in the card data dictionary
- CSV can use comma (`,`) or other delimiters (auto-detected)
