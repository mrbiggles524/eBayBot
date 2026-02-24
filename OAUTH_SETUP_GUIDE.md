# eBay OAuth Setup Guide

## The Problem
eBay requires **HTTPS** redirect URIs and does **NOT** allow `http://localhost`. This is why you're getting `400 invalid_request` errors.

## Solution Options

### Option 1: Use Direct Sign-In (EASIEST - Recommended)

**No redirect URI setup needed!**

1. Go to: https://developer.ebay.com/my/keys
2. Click **"User Tokens"** for your Sandbox app
3. Click **"Sign in to Sandbox for OAuth"** button
4. Sign in with `TESTUSER_manbot`
5. After authorization, **copy the token** shown on the page
6. Add it to your `.env` file as `EBAY_SANDBOX_TOKEN=...`

This bypasses the redirect URI requirement entirely!

### Option 2: Use ngrok for HTTPS Tunnel

If you need programmatic OAuth flow:

1. **Install ngrok**: https://ngrok.com/download
2. **Run setup script**: `python setup_ngrok_oauth.py`
3. **Update Developer Console** with the ngrok HTTPS URL
4. **Run OAuth flow**: `python get_oauth_token.py`

## Solution: Configure OAuth Redirect URI (if using ngrok)

### Step 1: Go to User Tokens Page
1. Visit: https://developer.ebay.com/my/keys
2. Sign in with your eBay Developer account
3. Make sure you're in **Sandbox** mode (not Production)
4. Click on **"User Tokens"** link next to your App ID

### Step 2: Configure OAuth Redirect URL
1. Scroll down to **"Get a Token from eBay via Your Application"** section
2. Look for your existing redirect URL entries
3. Find one that has **"OAuth Enabled"** checked (or create a new one)
4. Click **"Edit"** or **"+ Add eBay Redirect URL"**

### Step 3: Set the Redirect URI
1. **Display Title**: Enter a name (e.g., "Local Development")
2. **Your auth accepted URL**: Set to:
   ```
   http://localhost:8080/callback
   ```
3. **Your auth declined URL**: Can leave blank or set to same URL
4. **Privacy Policy URL**: Can leave blank for testing
5. **IMPORTANT**: Make sure **"OAuth Enabled"** checkbox is ✅ CHECKED
6. Click **"Save"**

### Step 4: Use the RuName (if needed)
- After saving, eBay generates a **RuName** (Redirect URL Name)
- For OAuth 2.0, you typically use the direct redirect URI (`http://localhost:8080/callback`)
- But make sure it's registered in one of your OAuth-enabled redirect URL entries

### Step 4: Try Again
1. Run: `python get_oauth_token.py`
2. Follow the prompts
3. When you paste the redirect URL, make sure it matches what you registered

## Alternative: Use eBay's Default Redirect

If you can't register a custom redirect URI, you can try using eBay's default redirect page. However, you'll need to manually extract the code from the URL.

## Troubleshooting

### Error: "invalid_request"
- **Cause**: Redirect URI mismatch
- **Fix**: Make sure the redirect URI in Developer Console matches EXACTLY what's in your `.env` file

### Error: "authorization_code_expired"
- **Cause**: Authorization codes expire quickly (usually within 10 minutes)
- **Fix**: Get a new authorization code by visiting the auth URL again

### Error: "redirect_uri_mismatch"
- **Cause**: The redirect URI used in authorization doesn't match the one in token exchange
- **Fix**: Make sure both use the same URI, and it's registered in Developer Console

## Quick Test

After registering the redirect URI, test it:

```bash
python get_oauth_token.py
```

The script will:
1. Show you the authorization URL
2. Open it in your browser
3. After you authorize, paste the redirect URL
4. Exchange the code for a token

If it still fails, check:
- Is the redirect URI registered in Developer Console?
- Does it match EXACTLY (case-sensitive, no extra spaces)?
- Did you authorize within the last few minutes?
