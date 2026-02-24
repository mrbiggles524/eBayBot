# Issue: OAuth Flow Returns Auth'n'Auth Token

## Problem

Even when using the OAuth 2.0 redirect flow, eBay is returning an Auth'n'Auth token (`v^1.1#...`) instead of an OAuth 2.0 token.

## What Happened

1. ✅ OAuth authorization URL worked
2. ✅ User authorized successfully
3. ✅ Redirect to webhookspy worked
4. ❌ But the `code` parameter contains an Auth'n'Auth token, not an OAuth authorization code

## Evidence

The redirect URL shows:
```
code=v^1.1#i^1#I^3#p^3#r^1#f^0#t^...
```

This is an Auth'n'Auth token format, not an OAuth 2.0 authorization code.

## Why This Is a Problem

- **Inventory API requires OAuth 2.0 tokens** (Bearer tokens)
- **Auth'n'Auth tokens won't work** with modern REST APIs
- Even the OAuth redirect flow is returning the wrong token type

## Possible Causes

1. **eBay OAuth Configuration Issue**: The Production keyset might be configured to only return Auth'n'Auth tokens
2. **Redirect URI Configuration**: The redirect URI might be set up for Auth'n'Auth, not OAuth 2.0
3. **eBay Platform Limitation**: eBay might not fully support OAuth 2.0 for this keyset/app

## What to Check

1. **In Developer Console**:
   - Go to: https://developer.ebay.com/my/keys
   - Click "Production" → "User Tokens"
   - Check your redirect URL entry
   - Make sure **"OAuth Enabled"** is checked (not just "Auth'n'Auth")
   - Verify the redirect URI is configured for OAuth 2.0

2. **OAuth Scopes**:
   - Make sure you're requesting the correct OAuth scopes
   - The authorization URL should include: `scope=https://api.ebay.com/oauth/api_scope/sell.inventory...`

## Next Steps

### Option 1: Contact eBay Developer Support

This appears to be an eBay configuration issue. Contact support:

1. Go to: https://developer.ebay.com/
2. Look for "Support" or "Contact Us"
3. Explain:
   - You're trying to use OAuth 2.0 for Inventory API
   - Even the OAuth redirect flow returns Auth'n'Auth tokens
   - You need OAuth 2.0 tokens to use the Inventory API
   - App ID: `YourName-BOT-PRD-xxxxxxxxxx`

### Option 2: Check OAuth Scopes Configuration

Make sure your app has OAuth scopes enabled:
1. In Developer Console, check "OAuth Scopes" for your Production app
2. Verify scopes like `sell.inventory`, `sell.account` are enabled

### Option 3: Try Different OAuth Endpoint

Some users report that using a different OAuth endpoint or flow works. But this seems like an eBay-side configuration issue.

## Summary

Even after going through the proper OAuth 2.0 redirect flow, eBay is returning Auth'n'Auth tokens. This suggests:
- eBay's OAuth configuration for your Production keyset might be incorrect
- Or there's a limitation/issue with how eBay handles OAuth for your app

**Recommendation**: Contact eBay Developer Support to investigate why OAuth 2.0 flow returns Auth'n'Auth tokens.
