# Fix Production OAuth "OAuth client was not found" Error

## The Problem

You're getting: `{"error_id":"unauthorized_client","error_description":"The OAuth client was not found."}`

This means the **redirect URI is not registered** in your **Production** keyset in eBay Developer Console.

**Important:** Production requires **HTTPS** redirect URIs (not `http://localhost`).

## Solution Options

### Option 1: Use Manual User Token (EASIEST for Production) ⭐ RECOMMENDED

**No redirect URI setup needed!**

1. **Go to eBay Developer Console**
   - Visit: https://developer.ebay.com/
   - Make sure you're viewing **Production** keyset (not Sandbox)

2. **Get User Token**
   - Click **"User Tokens"** link next to your Production App ID
   - Click **"Get a Token from eBay"** or **"Sign in to eBay for OAuth"**
   - Sign in with your eBay account
   - After authorization, **copy the token** shown on the page

3. **Add Token to .env**
   - Open your `.env` file
   - Add or update:
     ```
     EBAY_PRODUCTION_TOKEN=your_token_here
     ```
   - Save the file

4. **Disable OAuth in Config**
   - In `.env`, set:
     ```
     USE_OAUTH=false
     ```
   - This will use the manual token instead

5. **Test It**
   ```bash
   python check_keyset_status.py
   ```

**This is the easiest method for Production!**

---

### Option 2: Set Up HTTPS Redirect URI (For Programmatic OAuth)

If you need programmatic OAuth flow:

#### Step 1: Get an HTTPS URL

**Option A: Use ngrok (Free)**
1. Download ngrok: https://ngrok.com/download
2. Run: `ngrok http 8080`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

**Option B: Use Your Own Domain**
- If you have a domain with HTTPS, use: `https://yourdomain.com/callback`

#### Step 2: Add Redirect URI to Production Keyset

1. **Go to eBay Developer Console**
   - Visit: https://developer.ebay.com/
   - Navigate to: **Application Keys** → Your **Production** App
   - Click **"User Tokens"** link

2. **Add Redirect URL**
   - Scroll to **"Your eBay Sign-in Settings"** section
   - Click **"+ Add eBay Redirect URL"** or **"Edit"** existing one
   - Fill in:
     - **Display Title**: "Production OAuth"
     - **Your auth accepted URL1**: `https://your-ngrok-url.ngrok.io/callback`
       - (Replace with your actual HTTPS URL)
     - **Your auth declined URL**: Can leave blank
     - **Privacy Policy URL**: Can leave blank
   - **IMPORTANT**: Check ✅ **"OAuth Enabled"** checkbox
   - Click **"Save"**

3. **Update .env File**
   - Open `.env`
   - Update:
     ```
     OAUTH_REDIRECT_URI=https://your-ngrok-url.ngrok.io/callback
     ```
   - Save

4. **Keep ngrok Running**
   - Keep the ngrok terminal open while using OAuth
   - The URL changes if you restart ngrok

5. **Try OAuth Login Again**
   - In Streamlit UI → Step 2
   - Click "Login to eBay"
   - Should work now!

---

## Quick Fix: Use Manual Token (Recommended)

Since you're in Production and just need to get started:

1. **Get Token from Developer Console:**
   - Go to: https://developer.ebay.com/my/keys
   - Click **"User Tokens"** for your Production app
   - Click **"Get a Token from eBay"** or **"Sign in to eBay for OAuth"**
   - Sign in and copy the token

2. **Add to .env:**
   ```
   EBAY_PRODUCTION_TOKEN=paste_your_token_here
   USE_OAUTH=false
   ```

3. **Test:**
   ```bash
   python check_keyset_status.py
   ```

This bypasses the redirect URI requirement entirely!

---

## Why This Happens

- **Sandbox** allows `http://localhost:8080/callback`
- **Production** requires **HTTPS** redirect URIs
- Your Production keyset doesn't have a redirect URI registered yet
- eBay can't find the OAuth client configuration

---

## After Fixing

Once you have a token (manual or OAuth), you can:
- Create production drafts
- View listings in Seller Hub
- Test: `python check_keyset_status.py`
