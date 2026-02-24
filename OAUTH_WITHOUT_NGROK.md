# OAuth Setup Without ngrok

## The Problem

ngrok is flagged by antivirus, but eBay requires HTTPS for OAuth redirect URLs.

## Solution Options

### Option 1: Use Existing Redirect URL (httpbin.org)

You already have `https://httpbin.org/anything` configured in your Developer Console. However, this won't work directly because:
- httpbin.org doesn't run your callback handler
- You need a server that can receive the OAuth callback and extract the code

### Option 2: Use Manual Token Entry (Easiest)

Instead of OAuth flow, use the manual token from eBay Developer Console:

1. **Go to eBay Developer Console**
   - Visit: https://developer.ebay.com/my/keys
   - Click on your Sandbox app

2. **Get User Token**
   - Scroll to "Get a User Token Here" section
   - Click "Sign in to Sandbox for OAuth"
   - Sign in and grant permissions
   - Copy the token that appears

3. **Use Token in Streamlit UI**
   - Go to Step 2 in your Streamlit app
   - Use the "Manual Token Entry" tab
   - Paste the token
   - Click "Save Token"

**Note:** Manual tokens from the Developer Console should have the required scopes if you select them during generation.

### Option 3: Use Cloud Service for HTTPS Endpoint

If you need OAuth flow, you could use:
- **Cloudflare Tunnel** (free, similar to ngrok)
- **localtunnel** (npm package, free)
- **serveo.net** (SSH-based, no install needed)
- **localhost.run** (SSH-based)

### Option 4: Use Production OAuth (If You Have Domain)

If you have a domain with HTTPS, you can:
1. Set up a simple callback endpoint on your server
2. Register that URL in Developer Console
3. Use that for OAuth

## Recommended: Manual Token Entry

For sandbox testing, **Option 2 (Manual Token)** is the simplest:
- No antivirus issues
- No tunneling needed
- Works immediately
- Tokens last 18 months (Auth 'n' Auth) or can be refreshed

The only downside is you need to manually get a new token if it expires, but for testing this is usually fine.

## Quick Steps for Manual Token

1. Go to: https://developer.ebay.com/my/keys
2. Find your Sandbox app
3. Click "Sign in to Sandbox for OAuth" 
4. Sign in with your test user
5. Grant permissions
6. Copy the token
7. Paste in Streamlit UI → Step 2 → Manual Token Entry

This bypasses the redirect URI issue entirely!
