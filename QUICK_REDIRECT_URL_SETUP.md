# Quick Redirect URL Setup for OAuth

## The Problem

eBay requires a redirect URL to be configured before you can get OAuth tokens, even for manual token generation.

## Easiest Solution: Use a Free Webhook Service

### Option 1: WebhookSpy (Recommended - Permanent URL)

1. **Go to:** https://webhookspy.com/
2. **Click "Create Endpoint"** or similar
3. **Copy your unique HTTPS URL** (e.g., `https://webhookspy.com/your-unique-id`)
4. **Add `/callback` to the end:**
   - Example: `https://webhookspy.com/your-unique-id/callback`

5. **In eBay Developer Console:**
   - Go to: https://developer.ebay.com/my/keys
   - Click **"Production"** tab
   - Click **"User Tokens"** for Production app
   - Scroll to **"Get a Token from eBay via Your Application"**
   - Click **"+ Add eBay Redirect URL"**
   - Fill in:
     - **Display Title:** Production OAuth
     - **Your auth accepted URL1:** `https://webhookspy.com/your-unique-id/callback`
     - **Your auth declined URL:** (can leave blank)
     - **Privacy Policy URL:** (can leave blank)
   - **IMPORTANT:** Check ✅ **"OAuth Enabled"**
   - Click **"Save"**

6. **Now try again:**
   - Go to **"Get a User Token Here"** section
   - Select **"OAuth (new security)"**
   - Click **"Sign in to Production"**
   - Should work now!

### Option 2: Hooklistener (Also Good)

1. **Go to:** https://www.hooklistener.com/webhook-inbox
2. **Get your unique URL**
3. **Add it to Developer Console** as above

### Option 3: ngrok (If You Want Local Setup)

1. **Download ngrok:** https://ngrok.com/download
2. **Run:** `ngrok http 8080`
3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)
4. **Add to Developer Console:**
   - URL: `https://abc123.ngrok.io/callback`
   - Check "OAuth Enabled"
   - Save
5. **Keep ngrok running** while getting tokens

## Important Notes

- **The redirect URL doesn't need to actually work** - eBay just needs it configured
- **You can use any HTTPS URL** - it's just a requirement
- **Once configured, you can get OAuth tokens**
- **The URL can be simple** - you don't need a complex setup

## After Setup

1. Redirect URL is configured ✅
2. Go to "Get a User Token Here" section
3. Select "OAuth (new security)"
4. Click "Sign in to Production"
5. Get your OAuth 2.0 token!

## Quick Steps Summary

1. Get a free HTTPS URL from webhookspy.com
2. Add it in Developer Console → User Tokens → "+ Add eBay Redirect URL"
3. Check "OAuth Enabled"
4. Save
5. Try "Sign in to Production" again

That's it! The redirect URL is just a one-time configuration requirement.
