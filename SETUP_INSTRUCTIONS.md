# Setup Instructions

## Quick Setup Guide

### Step 1: Get Your eBay API Credentials

1. Go to https://developer.ebay.com/
2. Sign in with your eBay account
3. Navigate to "My Account" → "Developer Account"
4. Create a new application or use an existing one
5. Copy these three values:
   - **App ID** (also called Client ID)
   - **Dev ID** (Developer ID)
   - **Cert ID** (also called Client Secret)

### Step 2: Run the Setup UI

**Windows:**
- Double-click `run_setup_ui.bat`
- Or open Command Prompt and type: `python -m streamlit run start.py`

**Mac/Linux:**
- Open Terminal and type: `python -m streamlit run start.py`

### Step 3: Follow the Setup Wizard

The web interface will open at `http://localhost:8501`

#### Step 1: API Credentials
- Enter your **App ID**, **Dev ID**, and **Cert ID** from Step 1
- Choose **Sandbox** for testing (recommended first) or **Production** for real listings
- Click "Save Credentials"

#### Step 2: Login
- Click "🔐 Login with OAuth"
- Your browser will open to eBay's authorization page
- Sign in with your eBay account
- Authorize the application
- The token will be saved automatically
- Your username will appear in the sidebar once logged in

#### Step 3: Auto-Configure
- Optionally enter your eBay username (or leave empty to use your logged-in account)
- Click "🚀 Auto-Configure"
- The bot will fetch all required settings from your eBay account:
  - Fulfillment policies
  - Payment policies
  - Return policies
  - Merchant locations
- Configuration will be saved automatically

#### Step 4: Verify
- Click "🔍 Verify Configuration"
- Make sure all checks pass (green checkmarks)
- You're ready to use the bot!

### Step 4: Create Your First Listing

1. Create a CSV file with your cards (see `cards_example.csv` for format)
2. Run:
   ```bash
   python ebay_bot.py --csv your_cards.csv
   ```

## Your eBay Username

Your eBay username will be automatically detected when you log in, or you can enter it manually in Step 3.

This will be used when:
- Auto-configuring from your account
- Fetching your policies and settings
- Creating listings on your behalf

## Troubleshooting

**"Login failed"**
- Make sure you're signed in to the correct eBay account
- Check that your API credentials are correct
- Try refreshing the token

**"Auto-configure failed"**
- Make sure you completed Step 2 (Login) first
- Verify you have policies set up in your eBay account
- Check that you have seller privileges

**"No policies found"**
- You may need to create policies in your eBay Seller Hub first
- Go to: eBay Seller Hub → Account → Business Policies
- Create at least one Fulfillment, Payment, and Return policy

## Next Steps

Once setup is complete, you can:
- List cards from CSV files
- List cards from API sources (TCGPlayer, Scryfall)
- Create variation listings with multiple cards
- Use per-card pricing from CSV

For more information, see `README.md` or `QUICK_START.md`
