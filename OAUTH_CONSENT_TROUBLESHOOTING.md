# OAuth Consent Form Troubleshooting

## Common Issues with "Agree" Button Not Working

### Issue 1: Page Not Fully Loaded
- **Solution**: Wait 5-10 seconds for the page to fully load
- **Check**: Look for a loading spinner or "Please wait" message
- **Try**: Refresh the page (F5) and wait

### Issue 2: JavaScript Disabled or Blocked
- **Solution**: Enable JavaScript in your browser
- **Check**: Look for browser warnings about blocked scripts
- **Try**: Disable ad blockers temporarily

### Issue 3: Button is Below the Fold
- **Solution**: Scroll down on the page
- **Check**: The "Agree and Continue" button might be at the bottom
- **Try**: Use Page Down or scroll to bottom

### Issue 4: Using Wrong Browser/Incognito Issues
- **Solution**: Try a different browser or regular (non-incognito) mode
- **Check**: Some browsers block certain features in incognito
- **Try**: Chrome, Firefox, or Edge in regular mode

### Issue 5: Redirect URI Mismatch
- **Solution**: Make sure you're using the exact redirect URI registered in Developer Console
- **Check**: The URL should match what's in your `.env` or `ebay_oauth.py`
- **Current redirect**: `https://httpbin.org/anything`

### Issue 6: Sandbox Account Issues
- **Solution**: Make sure you're signed in as the correct sandbox user
- **Check**: Username should be `TESTUSER_manbot` (with TESTUSER_ prefix)
- **Try**: Sign out and sign back in

## Step-by-Step Guide

1. **Get the Authorization URL**
   - Run: `python show_oauth_url.py` or use the Streamlit UI Step 2
   - Copy the full URL

2. **Open URL in Browser**
   - Paste the URL in a new tab
   - Make sure you're NOT in incognito mode (for first attempt)

3. **Sign In**
   - Use sandbox credentials: `TESTUSER_manbot`
   - Complete any security checks

4. **View Consent Form**
   - You should see a list of permissions
   - Scroll down to see all permissions
   - Look for "Agree and Continue" button at the bottom

5. **Click Agree**
   - If button doesn't work:
     - Try clicking directly on the text "Agree and Continue"
     - Try double-clicking
     - Try right-click → Inspect → see if there are errors in console

6. **After Agreeing**
   - You'll be redirected to httpbin.org
   - Copy the FULL URL from the address bar
   - It should contain `?code=...`

## Alternative: Manual Token Entry

If the consent form won't work, you can get a token directly from eBay Developer Console:

1. Go to: https://developer.ebay.com/my/keys
2. Select your Sandbox keyset
3. Click "Get a User Token" → "Sign in to Sandbox for OAuth"
4. Complete the consent form there
5. Copy the token that appears
6. Paste it in Step 2 (Manual Entry) of the Streamlit UI

## Still Having Issues?

If none of the above works:
1. Check browser console for errors (F12 → Console tab)
2. Try a different browser
3. Clear cookies for sandbox.ebay.com
4. Contact eBay Developer Support: https://developer.ebay.com/support
