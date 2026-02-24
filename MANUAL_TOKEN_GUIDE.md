# Manual Token Entry Guide

## When to Use This Method

Use manual token entry when:
- ✅ eBay's OAuth server is down (500 errors)
- ✅ OAuth login keeps failing
- ✅ You prefer to get tokens from eBay Developer Console
- ✅ You need more control over token management

## How to Get Your User Token

### Step 1: Go to eBay Developer Console

1. Visit https://developer.ebay.com/
2. Sign in with your eBay account
3. Navigate to **"Application Keys"** section

### Step 2: Find Your Application

1. Find your application (the one matching your App ID)
2. You should see your App ID, Dev ID, and Cert ID listed
3. Next to your App ID, click **"User Tokens"**

### Step 3: Generate User Token

1. Click **"Get a Token from eBay via Your Browser"**
2. A new browser window will open
3. Sign in with your eBay account
4. Authorize the application
5. You'll see your **User Token** displayed
6. Copy the entire token (it's a long string)

### Step 4: Enter Token in Setup UI

1. In the Setup UI, go to **Step 2: Login**
2. Click the **"Manual Token Entry"** tab
3. Paste your User Token
4. Set expiration time (default: 7200 seconds = 2 hours)
5. Click **"Save Token"**

## Token Types

### Sandbox Token
- Use for testing
- Get from Sandbox User Tokens section
- Starts with different format than production

### Production Token
- Use for real listings
- Get from Production User Tokens section
- Make sure environment is set to "production"

## Token Expiration

- **Default:** 7200 seconds (2 hours)
- **Maximum:** Usually 18 months for User Tokens
- **Refresh:** Get a new token when it expires

## Advantages of Manual Tokens

✅ Works even when OAuth is down
✅ More reliable
✅ Can set custom expiration
✅ Direct from eBay Developer Console
✅ No callback server needed

## Troubleshooting

**"Invalid token" error:**
- Make sure you copied the entire token
- Check that token matches your environment (Sandbox/Production)
- Verify token hasn't expired

**"Token expired" error:**
- Get a new token from eBay Developer Console
- Enter it again in the Manual Token Entry tab

**"Wrong environment" error:**
- Make sure your token matches your environment setting
- Sandbox token for Sandbox environment
- Production token for Production environment

## Next Steps

After saving your token:
1. ✅ Step 2: Login (you're here)
2. ⏭️ Step 3: Auto-Configure
3. ⏭️ Step 4: Verify

Then you're ready to create listings!
