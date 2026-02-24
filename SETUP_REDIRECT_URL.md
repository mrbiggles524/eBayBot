# How to Set Up Redirect URL for OAuth

## What You Need to Do

You need to add a Redirect URL so OAuth can work. The bot uses `http://localhost:8080/callback`.

## Step-by-Step Instructions

### Step 1: Add Redirect URL

1. On the page you're seeing, find **"Add eBay Redirect URL"** button
2. Click **"Add eBay Redirect URL"** or **"Click here to add one"**

### Step 2: Enter Redirect URL Details

You'll need to enter:

**RuName (eBay Redirect URL name):**
- This is a unique name for your redirect URL
- Example: `eBayBot-Local-Callback` or `MyBot-Callback`
- Make it descriptive but simple

**Redirect URL:**
- Enter: `http://localhost:8080/callback`
- This is what the bot uses for OAuth callbacks

**Display Title (Optional):**
- Example: "eBay Card Listing Bot"
- This shows on the consent page

### Step 3: Save

1. Click **"Save"** or **"Add"**
2. The redirect URL should now be listed

## Important Notes

- **Localhost is OK**: eBay allows `localhost` for development/testing
- **Port 8080**: Make sure port 8080 matches what the bot uses
- **HTTP vs HTTPS**: For localhost, HTTP is fine. For production, you'd need HTTPS

## After Setting Up Redirect URL

Once you've added the redirect URL:

1. **Get Your User Token**:
   - Click **"Get a Token from eBay via Your Browser"**
   - Sign in and authorize
   - Copy the User Token

2. **Use Manual Token Entry**:
   - Go to Setup UI Step 2
   - Click "Manual Token Entry" tab
   - Paste your token
   - Save

## Alternative: Use Manual Token (No Redirect URL Needed)

If you don't want to set up the redirect URL right now:

1. You can still get a User Token manually
2. Use the "Manual Token Entry" method in the Setup UI
3. This bypasses the OAuth flow entirely

## Troubleshooting

**"Invalid redirect URL" error:**
- Make sure you entered exactly: `http://localhost:8080/callback`
- Check for typos
- Make sure there are no extra spaces

**"Redirect URL already exists":**
- That's fine, you can use the existing one
- Or create a new one with a different RuName

**Can't find "Add Redirect URL" button:**
- Look for "Click here to add one" link
- Or check if there's a "+" button
- It might be in a different section

## What the Redirect URL Does

When you use OAuth:
1. Bot opens eBay authorization page
2. You sign in and authorize
3. eBay redirects back to `http://localhost:8080/callback`
4. Bot receives the authorization code
5. Bot exchanges code for access token

This is why you need the redirect URL set up for OAuth to work.
