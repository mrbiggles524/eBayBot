# Fix OAuth Redirect URI - eBay Requires HTTPS

## The Problem

eBay requires **HTTPS** for OAuth redirect URLs. Your code is trying to use `http://localhost:8080/callback`, but eBay won't accept HTTP URLs.

## Solution: Use ngrok for HTTPS Tunnel

### Step 1: Install ngrok (if not already installed)

1. Download from: https://ngrok.com/download
2. Extract and add to PATH, OR
3. Use Chocolatey: `choco install ngrok`

### Step 2: Start ngrok

Run this command in a separate terminal (keep it open):

```bash
ngrok http 8080
```

This will give you an HTTPS URL like: `https://abc123.ngrok.io`

### Step 3: Add Redirect URL to eBay Developer Console

1. Go to: https://developer.ebay.com/my/keys
2. Click on your Sandbox app (the one with "SBX" in the App ID)
3. Scroll down to "Your eBay Sign-in Settings"
4. Find your redirect URL entry (or click "Add eBay Redirect URL")
5. Set **"Your auth accepted URL1"** to:
   ```
   https://YOUR_NGROK_URL.ngrok.io/callback
   ```
   (Replace `YOUR_NGROK_URL` with your actual ngrok URL)
6. Make sure **"OAuth Enabled"** is checked
7. Click **"Save"**

### Step 4: Update Your .env File

Add or update this line in your `.env` file:

```
OAUTH_REDIRECT_URI=https://YOUR_NGROK_URL.ngrok.io/callback
```

### Step 5: Try OAuth Login Again

1. Make sure ngrok is still running
2. Go to Step 2 in your Streamlit UI
3. Click "Login with OAuth"
4. It should work now!

## Alternative: Use Existing Redirect URL

If you already have an HTTPS redirect URL configured in eBay Developer Console, you can use that instead:

1. Check your existing redirect URLs in the Developer Console
2. Update your `.env` file to use that URL:
   ```
   OAUTH_REDIRECT_URI=https://your-existing-url.com/callback
   ```
3. Make sure your OAuth callback handler is accessible at that URL

## Important Notes

- **Keep ngrok running** while using OAuth (the URL changes if you restart ngrok)
- The redirect URL must match **exactly** (including `/callback` at the end)
- eBay requires HTTPS - HTTP URLs will be rejected
- For production, you'll need a real domain with HTTPS

## Quick Setup Script

You can also run:
```bash
python setup_ngrok_oauth.py
```

This will:
1. Check if ngrok is running
2. Start ngrok if needed
3. Get the HTTPS URL
4. Update your .env file
5. Show you what to add in the Developer Console
