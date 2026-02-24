# OAuth Login Timeout - Debugging Guide

## Common Causes

1. **Redirect URI Mismatch** - The redirect URI in eBay doesn't match what the code is using
2. **Port 8080 Blocked** - Firewall or antivirus blocking port 8080
3. **Browser Not Redirecting** - Browser security settings preventing redirect
4. **Wrong Redirect URI Format** - Using https:// instead of http:// for localhost

## Quick Fix: Use Manual Token (Easiest)

Since you already have a token, you can skip OAuth for now:

1. Go to **Step 2 → Manual Token Entry** tab
2. Paste your token from eBay Developer Console
3. Save it
4. Continue with Step 3

Your token should work for creating listings!

## Debug OAuth Timeout

### Step 1: Verify Redirect URI Matches

**In eBay Developer Console:**
- Check what redirect URI you entered
- Should be: `http://localhost:8080/callback` (NOT https://)

**In your `.env` file:**
- Check `OAUTH_REDIRECT_URI=http://localhost:8080/callback`
- Must match EXACTLY what's in eBay (including http:// vs https://)

### Step 2: Check Port 8080

**Windows:**
```powershell
netstat -ano | findstr :8080
```

If something is using port 8080, close it or change the port.

**Test if port is accessible:**
```powershell
Test-NetConnection -ComputerName localhost -Port 8080
```

### Step 3: Check Firewall

**Windows Firewall:**
1. Open Windows Defender Firewall
2. Check if port 8080 is blocked
3. Temporarily disable firewall to test (then re-enable!)

### Step 4: Manual Browser Test

1. Click "Login with OAuth" in the UI
2. Copy the authorization URL from the page
3. Open it manually in your browser
4. Complete the authorization
5. **Watch the URL bar** - after you authorize, does it redirect to `http://localhost:8080/callback?code=...`?

If it redirects but the app doesn't receive it:
- Port 8080 might be blocked
- The callback server might not be running

If it doesn't redirect at all:
- Redirect URI mismatch
- Check eBay Developer Console settings

### Step 5: Check Terminal Output

When you click "Login with OAuth", check the terminal/console where Streamlit is running. You should see:
```
Starting eBay OAuth login...
Waiting for authorization callback on http://localhost:8080/callback...
```

If you see errors about port 8080, that's the issue.

## Alternative: Use ngrok (If localhost doesn't work)

If localhost keeps timing out, use ngrok to create a public HTTPS URL:

1. Install ngrok: https://ngrok.com/download
2. Run: `ngrok http 8080`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)
4. Update eBay redirect URI to: `https://abc123.ngrok-free.app/callback`
5. Update `.env`: `OAUTH_REDIRECT_URI=https://abc123.ngrok-free.app/callback`
6. Try OAuth login again

See `OAUTH_NGROK_SETUP.md` for detailed instructions.

## Quick Test

**Try this first:**
1. Use Manual Token Entry (you already have a token!)
2. It should work immediately
3. You can set up OAuth later if you want automatic renewal
