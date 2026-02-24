# How to Get Your User Token from eBay Developer Console

## Step-by-Step Instructions

### Step 1: Navigate to User Tokens

1. You're currently on the "Alerts & Notifications" page
2. Look for **"User Tokens (eBay Sign-in)"** in the left sidebar or navigation
3. Click on **"User Tokens"** or **"User Tokens (eBay Sign-in)"**

### Step 2: Generate User Token

Once you're on the User Tokens page, you should see:

1. **"Get a Token from eBay via Your Browser"** button
   - Click this button
   - A new browser window/tab will open

2. **Sign in with your eBay account**
   - Use your eBay username and password
   - Complete any 2FA if prompted

3. **Authorize the application**
   - Review the permissions
   - Click "I Agree" or "Authorize"

4. **Copy the User Token**
   - After authorization, you'll see a page with your **User Token**
   - It's a long string of characters
   - **Copy the entire token** (it's usually quite long)

### Step 3: Enter Token in Setup UI

1. Go back to your Setup UI (Streamlit)
2. Go to **Step 2: Login**
3. Click the **"Manual Token Entry"** tab
4. Paste your User Token
5. Set expiration (default: 7200 seconds = 2 hours)
6. Click **"Save Token"**

## What You're Looking For

The User Token will look something like:
```
v^1.1#i^1#r^0#I^3#f^0#p^1#t^Ul4xMF8yOkNBRF8xOjE3MT... (very long string)
```

Or for newer tokens:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9... (JWT format, also very long)
```

## Important Notes

- **Sandbox vs Production**: Make sure you're getting the token for the correct environment
  - Sandbox token for testing
  - Production token for real listings
- **Token Expiration**: User Tokens typically last 18 months, but you can set a shorter expiration in the UI
- **Keep it Secret**: Don't share your token publicly

## If You Can't Find User Tokens

If you don't see "User Tokens" option:

1. Make sure you're looking at the correct application (BOT)
2. Check that you're in the right environment (Sandbox/Production)
3. Try refreshing the page
4. Look for "User Tokens" or "Get User Token" in the menu

## What About Alerts & Notifications?

The "Alerts & Notifications" page you saw is **optional** and not needed for basic setup. It's used for:
- Receiving notifications when items sell
- Getting alerts about orders
- Monitoring account activity

You can set this up later if needed, but it's not required to use the bot.

## Next Steps

After you get your token and save it:
1. ✅ Step 2: Login (you're here)
2. ⏭️ Step 3: Auto-Configure
3. ⏭️ Step 4: Verify

Then you're ready to create listings!
