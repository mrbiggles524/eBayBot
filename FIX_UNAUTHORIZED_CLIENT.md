# Fix "unauthorized_client" OAuth Error

## The Error

```
{"error_id":"unauthorized_client","error_description":"The OAuth client was not found.","http_status_code":401}
```

## What This Means

eBay can't find your OAuth client configuration. This usually means:

1. **Redirect URI doesn't match** - The redirect URI in your code must match EXACTLY what's registered in Developer Console
2. **App ID is wrong** - The App ID (Client ID) doesn't match your Production keyset
3. **OAuth not enabled** - The redirect URI isn't enabled for OAuth (only Auth'n'Auth)

## How to Fix

### Step 1: Check Redirect URI in Developer Console

1. Go to: https://developer.ebay.com/my/keys
2. Click **"Production"** tab
3. Click **"User Tokens"**
4. Scroll to **"Your eBay Sign-in Settings"**
5. Find your redirect URL entry
6. Check **"Your auth accepted URL1"** - copy it EXACTLY
7. Make sure **"OAuth Enabled"** is CHECKED (not just "Auth'n'Auth")

### Step 2: Update the Script

The redirect URI in `get_production_oauth_token.py` must match EXACTLY what's in Developer Console.

**Current script uses:**
```
https://webhookspy.com/44063bc75f7a4e4893da63668303edd3
```

**Check if your Developer Console has:**
- Same URL (should match)
- Or with trailing slash: `https://webhookspy.com/44063bc75f7a4e4893da63668303edd3/`
- Or with /callback: `https://webhookspy.com/44063bc75f7a4e4893da63668303edd3/callback`

**If different, update line 19 in `get_production_oauth_token.py` to match EXACTLY.**

### Step 3: Verify App ID

1. In Developer Console, check your Production App ID
2. It should be: `YourName-BOT-PRD-xxxxxxxxxx`
3. Check your `.env` file - `EBAY_APP_ID` must match exactly

### Step 4: Make Sure OAuth is Enabled

In Developer Console, for your redirect URL entry:
- ✅ **"OAuth Enabled"** must be CHECKED
- ❌ If only "Auth'n'Auth" is checked, OAuth won't work

## Quick Fix

If your redirect URI in Developer Console is different, edit `get_production_oauth_token.py`:

1. Open the file
2. Find line 19: `redirect_uri = "https://webhookspy.com/44063bc75f7a4e4893da63668303edd3"`
3. Change it to match EXACTLY what's in Developer Console
4. Save and run again

## Alternative: Use Manual Token (Workaround)

If OAuth keeps failing, you can still use the manual token from Developer Console, but you'll get Auth'n'Auth tokens which won't work with Inventory API.

The real solution is to fix the OAuth redirect URI configuration.
