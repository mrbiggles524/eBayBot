# eBay Card Listing Bot

A Python bot for creating eBay listings with multiple card variations from the same set. This bot can fetch card checklists from various sources (TCGPlayer, Scryfall) and create variation listings on eBay.

## Features

- **Simple Web UI**: Easy-to-use setup wizard for non-technical users (works for any eBay user)
- **Universal Setup**: One-time setup per user - each person can configure their own eBay account
- **Multiple Card Variations**: List multiple cards from the same set as variations in a single eBay listing
- **Card Checklist Fetching**: Automatically fetch card checklists from TCGPlayer or Scryfall APIs
- **Flexible Configuration**: Support for different card data sources and eBay environments
- **Filter Support**: Filter cards by name or number before listing
- **Set Search**: Search for card sets before listing
- **Auto-Setup**: Automatically fetch all required settings from any eBay account

## Setup

### Quick Start (Recommended - Web UI)

For users who prefer a simple graphical interface:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the setup UI
python -m streamlit run start.py
```

Or on Windows, double-click `run_setup_ui.bat` (which runs `start.py`)

This will open a web browser with a simple setup wizard that guides you through:
1. Entering your eBay API credentials
2. Logging in with OAuth
3. Auto-configuring from your account
4. Verifying everything is set up correctly

### Manual Setup (Command Line)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure eBay API

1. Get your eBay API credentials from the [eBay Developers Program](https://developer.ebay.com/)
2. Copy `env_example.txt` to `.env`
3. Fill in your eBay API credentials:
   - `EBAY_APP_ID`
   - `EBAY_DEV_ID`
   - `EBAY_CERT_ID`

### 3. Login with OAuth (Recommended)

The bot supports OAuth 2.0 login, which is more secure than static tokens:

```bash
python ebay_bot.py --login
```

This will:
1. Open your browser to eBay's authorization page
2. Ask you to authorize the application
3. Save your access token automatically

**Note:** OAuth is enabled by default (`USE_OAUTH=true`). If you prefer to use static tokens, set `USE_OAUTH=false` in your `.env` file and provide `EBAY_SANDBOX_TOKEN` or `EBAY_PRODUCTION_TOKEN`.

### 4. Configure Card Data Source

The bot supports multiple card data sources:

- **TCGPlayer**: Requires `TCGPLAYER_API_KEY` in `.env`
- **Scryfall**: No API key needed (for Magic: The Gathering cards)
- **Custom**: Extend `card_checklist.py` for other sources

Set `CARD_DATA_SOURCE` in `.env` to your preferred source.

### 5. Auto-Setup (Recommended)

After logging in, automatically fetch all required configuration from your eBay account:

```bash
python ebay_bot.py --setup
```

This will:
- Fetch your user information
- Get all available fulfillment, payment, and return policies
- Find your merchant locations
- Automatically configure your `.env` file with recommended settings

**Manual Policy Configuration (Alternative):**

If you prefer to set policies manually, you can configure them in `.env`:

- `FULFILLMENT_POLICY_ID` - Your fulfillment policy ID
- `PAYMENT_POLICY_ID` - Your payment policy ID
- `RETURN_POLICY_ID` - Your return policy ID
- `MERCHANT_LOCATION_KEY` - Your merchant location key

These can be created via the eBay API or Seller Hub. The `--setup` command will automatically select the best policies from your account.

## Usage

### Authentication & Setup

**First-time setup - Auto-configure everything:**
```bash
# Login first
python ebay_bot.py --login

# Then auto-setup (fetches all policies, locations, etc. from your account)
python ebay_bot.py --setup
```

**Manual login:**
```bash
python ebay_bot.py --login
```

**Refresh token (if expired):**
```bash
python ebay_bot.py --refresh-token
```

**Verify setup:**
```bash
python ebay_bot.py --verify
```

**Logout:**
```bash
python ebay_bot.py --logout
```

### Basic Usage

List all cards from a set:

```bash
python ebay_bot.py "Magic: The Gathering - Core Set 2021"
```

### CSV Import

Import cards from a CSV file:

```bash
python ebay_bot.py --csv cards.csv
```

CSV Format:
- Required columns: `name`, `number`
- Optional columns: `set_name`, `rarity`, `price`, `quantity`, `condition`, `image_url`, `weight`
- See `cards_example.csv` for a template

Example CSV:
```csv
name,number,set_name,rarity,price,quantity,condition
Lightning Bolt,1,Core Set 2021,Common,0.99,1,Near Mint
Counterspell,2,Core Set 2021,Uncommon,1.49,1,Near Mint
```

### Advanced Usage

```bash
# Custom title and price
python ebay_bot.py "Core Set 2021" --title "MTG Core Set 2021 Complete" --price 1.99

# Use CSV with custom options
python ebay_bot.py --csv cards.csv --title "My Card Collection" --category "Trading Cards"

# Filter specific cards
python ebay_bot.py "Core Set 2021" --filter "Lightning Bolt" "Counterspell"

# Set quantity and condition
python ebay_bot.py "Core Set 2021" --quantity 2 --condition "Near Mint"

# Create listing without publishing (draft)
python ebay_bot.py "Core Set 2021" --no-publish

# Search for sets
python ebay_bot.py "Core Set" --search
```

### Command Line Arguments

**Authentication & Setup:**
- `--login`: Login using OAuth (opens browser)
- `--logout`: Remove saved OAuth token
- `--refresh-token`: Refresh OAuth access token
- `--setup`: Auto-setup from eBay account (fetches policies, locations, etc.)
- `--user-id USER_ID`: eBay user ID for setup (optional, uses current user if not provided)
- `--verify`: Verify current setup configuration

**Listing:**
- `set_name`: Name of the card set to list (required if not using --csv)
- `--csv`, `--csv-file`: Path to CSV file with card data (alternative to set_name)
- `--title`: Custom listing title
- `--description`: Custom listing description (HTML supported)
- `--price`: Price per card (default: 0.99, or use price column in CSV)
- `--quantity`: Quantity per card variation (default: 1, or use quantity column in CSV)
- `--condition`: Card condition (default: from config, or use condition column in CSV)
- `--category`: eBay category (default: "Trading Cards")
- `--filter`: Filter cards by name/number (can specify multiple)
- `--search`: Search for sets instead of creating listing
- `--no-publish`: Create listing but do not publish (creates draft)

## Project Structure

```
eBayBot/
├── ebay_bot.py          # Main bot entry point
├── ebay_listing.py      # eBay API integration for listings
├── card_checklist.py    # Card checklist fetching from various sources
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## eBay API Requirements

This bot uses the eBay Inventory API to create variation listings. You'll need:

1. **eBay Developer Account**: Sign up at https://developer.ebay.com/
2. **OAuth Token**: Generate tokens for sandbox and production
3. **Policies**: Set up fulfillment, payment, and return policies
4. **Location Key**: Configure your merchant location

## Card Data Sources

### CSV Import (Recommended)
- Most flexible option
- Supports per-card pricing, quantities, and conditions
- No API keys required
- See `cards_example.csv` for format

### TCGPlayer
- Supports multiple card games
- Requires API key
- Good for general trading cards

### Scryfall
- Specifically for Magic: The Gathering
- No API key required
- Comprehensive card data

### Custom Sources
Extend `CardChecklistFetcher` class to add support for:
- Databases
- Other APIs
- Web scraping

## Notes

- **OAuth Login**: OAuth is the recommended authentication method. Tokens are automatically refreshed when expired.
- **Sandbox Testing**: Always test in sandbox mode first (`EBAY_ENVIRONMENT=sandbox`)
- **Rate Limits**: Be aware of eBay API rate limits (bot includes automatic retry logic)
- **Variation Limits**: eBay has limits on the number of variations per listing (typically 250)
- **Image URLs**: Ensure card images are publicly accessible URLs
- **Category IDs**: Update category mappings in `ebay_listing.py` as needed
- **Per-Card Pricing**: Use CSV import with a `price` column for different prices per card
- **Policy Management**: The bot automatically fetches policies if not configured, but you can set them in `.env` for better control
- **Token Storage**: OAuth tokens are stored in `.ebay_token.json` (automatically created, should be in `.gitignore`)

## Troubleshooting

### "Missing required configuration" error
- Ensure all required fields are set in `.env`
- Check that your `.env` file is in the project root

### "No cards found for set"
- Verify the set name matches exactly
- Try using `--search` to find the correct set name
- Check that your card data source API is working

### Listing creation fails
- Verify your eBay API credentials
- Check that policies and location keys are set correctly
- Review eBay API error messages for specific issues

## License

This project is provided as-is for educational and personal use.
