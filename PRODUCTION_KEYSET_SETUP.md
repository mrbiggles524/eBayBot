# Production Keyset Setup Guide

## Current Status

Your Production keyset is **currently disabled**. You need to enable it before you can use Production environment.

## What You Need to Do

eBay requires you to either:

### Option 1: Comply with Marketplace Deletion/Account Closure Notification Process

This means setting up notifications to be informed when:
- A marketplace account is deleted
- An account is closed

**Steps:**
1. Go to **Alerts & Notifications** in your eBay Developer Console
2. Set up **Marketplace Account Deletion** notifications
3. Configure the notification endpoint or email
4. Save the settings
5. Your keyset should be enabled automatically

### Option 2: Apply for an Exemption

If you don't need these notifications, you can apply for an exemption:

1. Look for **"Apply for an exemption"** link in the Developer Console
2. Fill out the exemption request form
3. Explain why you don't need these notifications
4. Wait for eBay's approval

## For Now: Use Sandbox

**Recommendation:** Use **Sandbox** environment for now to test your bot.

**Why:**
- ✅ Sandbox keyset is already enabled
- ✅ Perfect for testing
- ✅ No real listings (safe to experiment)
- ✅ Same functionality as Production

**When to Switch to Production:**
- After you've tested everything in Sandbox
- After your Production keyset is enabled
- When you're ready to create real listings

## How to Enable Production Keyset

### Step 1: Set Up Notifications (Recommended)

1. Go to https://developer.ebay.com/
2. Navigate to **Application Keys** → Your Production App
3. Click **"Alerts & Notifications"** or **"Notifications"**
4. Find **"Marketplace Account Deletion"** section
5. Choose one:
   - **Email notification**: Enter your email address
   - **Webhook endpoint**: Enter an HTTPS URL that can receive notifications
6. Click **"Save"**
7. Your keyset should be enabled

### Step 2: Verify Keyset is Enabled

1. Go back to **Application Keys**
2. Check your Production keyset
3. It should no longer say "Your Keyset is currently disabled"
4. You should see your App ID, Dev ID, and Cert ID

## Using the Bot

### For Testing (Now):
- Use **Sandbox** environment
- Get Sandbox User Token
- Test all functionality

### For Production (Later):
- Enable Production keyset (follow steps above)
- Switch environment to "production" in Step 1
- Get Production User Token
- Create real listings

## OAuth Scopes

Your app has been granted these scopes (which is good!):
- ✅ `sell.inventory` - Manage inventory and offers
- ✅ `sell.account` - Manage account settings
- ✅ `sell.fulfillment` - Manage order fulfillments
- ✅ And many more...

These are all the scopes you need for the card listing bot.

## Next Steps

1. **For now**: Use Sandbox environment
2. **Set up notifications** in eBay Developer Console (when ready)
3. **Enable Production keyset** (follow steps above)
4. **Switch to Production** when ready for real listings

## Need Help?

- Check eBay Developer Documentation
- Contact eBay Developer Support
- Use Sandbox for testing in the meantime
