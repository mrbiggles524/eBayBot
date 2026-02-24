# How to Get Production OAuth 2.0 Token

## Important: You Need Production OAuth 2.0 Token

**NOT:**
- ❌ Sandbox token
- ❌ Auth'n'Auth token
- ❌ Production Auth'n'Auth token

**YES:**
- ✅ Production OAuth 2.0 token

## Step-by-Step Instructions

### Step 1: Go to User Tokens Page

1. Visit: https://developer.ebay.com/my/keys
2. Make sure you're logged in

### Step 2: Select PRODUCTION (Not Sandbox)

1. Look at the top of the page
2. You'll see tabs: **Sandbox** | **Production**
3. **Click "Production"** tab
4. Make sure it's selected (highlighted/active)

### Step 3: Find Your Production App

1. Under the Production tab, find your app:
   - **BOT**
   - App ID: `YourName-BOT-PRD-xxxxxxxxxx`
   - (Notice: **PRD** = Production, not SBX)

### Step 4: Click "User Tokens"

1. Click the **"User Tokens"** link next to your Production App ID

### Step 5: Select OAuth (Not Auth'n'Auth)

1. Look for the section: **"Get a User Token Here"**
2. You'll see two options:
   - **Auth'n'Auth** (old method - ❌ don't use this)
   - **OAuth (new security)** (✅ USE THIS ONE)
3. **Make sure "OAuth (new security)" is selected/checked**

### Step 6: Sign In to Production

1. Click **"Sign in to Production"** button
2. Sign in with your eBay account (manhattanbreaks)
3. Review and accept the consent form
4. After authorization, you'll get a token

### Step 7: Copy the OAuth 2.0 Token

1. The token will be displayed on the page
2. **OAuth 2.0 tokens look like:**
   - Long base64 string
   - Usually starts with letters/numbers (not `v^1.1#`)
   - Example: `v1.1.AaBbCcDdEeFf...` or just a long string

3. **Auth'n'Auth tokens look like:**
   - Start with `v^1.1#i^1#...`
   - ❌ These won't work with Inventory API

### Step 8: Update Token

```bash
python update_token.py "your_oauth2_token_here"
```

## Visual Guide

**What you should see:**

```
Environment: [Sandbox] [Production] ← Click Production
                   
BOT (Production)
App ID: YourName-BOT-PRD-...
[User Tokens] [Notifications]

Get a User Token Here
Get a token for an eBay Production user.

[ ] Auth'n'Auth          ← Don't use this
[✓] OAuth (new security) ← Use this one!

[Sign in to Production]  ← Click this
```

## Common Mistakes

1. **Using Sandbox tab** - Make sure you're on Production tab
2. **Using Auth'n'Auth** - Must use OAuth (new security)
3. **Copying wrong token** - Make sure it's the OAuth 2.0 token, not Auth'n'Auth

## After Getting Token

1. Update: `python update_token.py "your_token"`
2. Test: `python check_keyset_status.py`
3. Should show: `[OK] Keyset appears to be ENABLED!`

## If You Still Get Errors

- Make sure keyset is enabled (no "Non Compliant")
- Make sure exemption is active
- Try the token immediately after getting it (they can expire
