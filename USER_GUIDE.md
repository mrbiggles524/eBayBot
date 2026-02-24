# User Guide - Universal Setup

This bot is designed to work for **any eBay user**. Each person can set up their own configuration.

## For First-Time Users

### Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Setup UI**
   ```bash
   python -m streamlit run start.py
   ```
   Or double-click `run_setup_ui.bat` on Windows.

3. **Follow the 4-Step Wizard**
   - Step 1: Enter your eBay API credentials
   - Step 2: Login with your eBay account
   - Step 3: Auto-configure (uses your logged-in account)
   - Step 4: Verify setup

## How It Works

### Each User Has Their Own Configuration

- **`.env` file**: Contains your API credentials and settings
- **`.ebay_token.json`**: Contains your OAuth token (user-specific)
- **Policies**: Automatically fetched from YOUR eBay account

### Sharing the Bot

If you want to share this bot with others:

1. **Don't share your `.env` file** - Each user needs their own
2. **Don't share your `.ebay_token.json`** - Each user needs to log in
3. **Share the code and instructions** - Let each person run their own setup

### Multi-User Setup

If multiple people will use this on the same computer:

**Option 1: Separate Folders (Recommended)**
- Each user has their own copy of the bot in a separate folder
- Each has their own `.env` and `.ebay_token.json`

**Option 2: User-Specific Config Files**
- Rename `.env` to `.env.username` for each user
- Rename `.ebay_token.json` to `.ebay_token.username.json`
- Switch between users by renaming files

## Setup Process (Universal)

The setup wizard works the same for everyone:

1. **Get eBay API Credentials**
   - Go to https://developer.ebay.com/
   - Sign in with YOUR eBay account
   - Create an application
   - Copy App ID, Dev ID, and Cert ID

2. **Login**
   - Click "Login with OAuth"
   - Sign in with YOUR eBay account
   - Authorize the application

3. **Auto-Configure**
   - The bot automatically detects YOUR logged-in username
   - Fetches policies from YOUR account
   - Configures everything for YOUR account

4. **Verify**
   - Checks that everything is set up for YOUR account
   - Ready to create listings on YOUR behalf

## Creating Listings

Once set up, you can create listings:

```bash
# From CSV file
python ebay_bot.py --csv your_cards.csv

# From API source
python ebay_bot.py "Set Name"
```

All listings will be created on **your** eBay account (the one you logged in with).

## Troubleshooting

**"Wrong account"**
- Make sure you logged in with the correct eBay account in Step 2
- Check the username shown in the sidebar
- Logout and login again if needed

**"Policies not found"**
- Make sure you have seller privileges on your eBay account
- Create policies in eBay Seller Hub first
- Then run auto-configure again

**"Token expired"**
- Click "Refresh Token" in Step 2
- Or logout and login again

## Security Notes

- Each user's credentials are stored locally in `.env`
- Each user's OAuth token is stored in `.ebay_token.json`
- These files are in `.gitignore` and should NOT be shared
- Each person should run their own setup with their own credentials
