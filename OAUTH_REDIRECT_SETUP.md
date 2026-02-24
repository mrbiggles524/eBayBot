# How to Fix OAuth "invalid_request" Error

## The Problem
You're getting: `{"error_id":"invalid_request","error_description":"Input request parameters are invalid."}`

This means the **redirect URI is not registered** in your eBay Developer Console.

## Solution: Register the Redirect URI

### For Sandbox Environment:

1. **Go to eBay Developer Console**
   - Visit: https://developer.ebay.com/
   - Sign in with your eBay account

2. **Navigate to Your App**
   - Click on "Application Keys" in the left menu
   - Find your **Sandbox** keyset (the one with "SBX" in the App ID)

3. **Add Redirect URI**
   - Look for "OAuth Redirect URIs" or "Redirect URIs" section
   - Click "Add" or "Edit"
   - Add this EXACT URI: `http://localhost:8080/callback`
   - **Important:** 
     - Use `http://` (NOT `https://`)
     - Use `localhost` (NOT `127.0.0.1`)
     - Include `/callback` at the end
     - No trailing slash
   - Click "Save"

4. **Try OAuth Login Again**
   - Go back to Step 2 in the setup UI
   - Click "Login with OAuth"
   - It should work now!

### For Production Environment:

Use: `https://yourdomain.com/callback` (you'll need a real domain with HTTPS)

**For testing, stick with Sandbox and use `http://localhost:8080/callback`**

## Alternative: Manual Token with Scopes

If OAuth still doesn't work, you can get a User Token manually, but you need to make sure it has the right scopes:

1. Go to eBay Developer Console
2. Click on your App ID → "User Tokens"
3. Generate a new User Token
4. **Important:** When generating, make sure to select these scopes:
   - `sell.inventory`
   - `sell.account`
   - `sell.fulfillment`
5. Copy the token and paste it in Step 2 (Manual Entry)

**Note:** Some manual token generation methods don't let you select scopes. In that case, OAuth is the only way to get a token with the right permissions.
