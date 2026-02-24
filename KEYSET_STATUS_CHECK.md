# Production Keyset Status Check

## Current Status: **DISABLED** ⚠️

Based on the API test, your **Production keyset appears to be DISABLED**.

### What This Means

When you see the error:
```
"error":"invalid_client","error_description":"client authentication failed"
```

This typically means:
- ✅ Your credentials (App ID, Dev ID, Cert ID) are correct
- ❌ Your **Production keyset is disabled** in eBay Developer Console
- ❌ eBay won't authenticate your app for production API calls

### Why eBay Disables Production Keysets

eBay requires all production apps to comply with:
1. **Marketplace Account Deletion Notification Process**
   - You must be notified when marketplace accounts are deleted
   - You must be notified when accounts are closed

This is a compliance requirement for all production apps.

## How to Enable Your Production Keyset

### Option 1: Set Up Notifications (Recommended - Fastest)

**Steps:**

1. **Go to eBay Developer Console**
   - Visit: https://developer.ebay.com/
   - Log in with your eBay developer account

2. **Navigate to Your Production App**
   - Click **"My Account"** or **"Developer Account"**
   - Go to **"Application Keys"** or **"Keys & Credentials"**
   - Find your **Production** keyset (NOT the Sandbox one)
   - The Production keyset will NOT have "SBX" in the App ID

3. **Set Up Notifications**
   - Click on your Production keyset
   - Look for **"Alerts & Notifications"** or **"Notifications"** tab/section
   - Find **"Marketplace Account Deletion"** or **"Account Closure"** section
   - Choose one of these options:
     - **Email Notification**: Enter your email address
       - This is the simplest option
       - You'll receive emails when accounts are deleted/closed
     - **Webhook Endpoint**: Enter an HTTPS URL
       - More advanced, requires a server that can receive POST requests
       - Format: `https://yourdomain.com/ebay-notifications`

4. **Save Settings**
   - Click **"Save"** or **"Update"**
   - Your keyset should be enabled **automatically** (usually within minutes)

5. **Verify It's Enabled**
   - Go back to **Application Keys**
   - Check your Production keyset
   - It should **NOT** say "Your Keyset is currently disabled"
   - You should see your App ID, Dev ID, and Cert ID clearly displayed

### Option 2: Apply for an Exemption

If you don't need these notifications, you can request an exemption:

1. **Find Exemption Link**
   - In eBay Developer Console
   - Look for **"Apply for an exemption"** or **"Request exemption"** link
   - Usually near the keyset status message

2. **Fill Out Form**
   - Explain why you don't need account deletion notifications
   - Provide business justification
   - Submit the request

3. **Wait for Approval**
   - eBay will review your request
   - This can take several days to weeks
   - You'll receive an email when approved/denied

**Note:** Exemptions are not always granted. Setting up notifications is usually faster and more reliable.

## How to Verify Keyset is Enabled

### Method 1: Check Developer Console

1. Go to https://developer.ebay.com/
2. Navigate to: **Application Keys**
3. Find your **Production** keyset
4. **Look for:**
   - ✅ **ENABLED**: Keyset shows App ID, Dev ID, Cert ID
   - ❌ **DISABLED**: Message says "Your Keyset is currently disabled"

### Method 2: Run This Script

```bash
python check_keyset_status.py
```

**If Enabled:**
- You'll see: `[OK] Keyset appears to be ENABLED!`
- API calls will succeed

**If Disabled:**
- You'll see: `[WARNING] Keyset Status: UNKNOWN or DISABLED`
- You'll get authentication errors

## What to Do Now

### For Testing (Recommended):
1. **Use Sandbox Environment**
   - Sandbox keyset is already enabled
   - Perfect for testing
   - No real listings (safe to experiment)
   - Same functionality as production

2. **Switch Back to Sandbox:**
   ```bash
   # Edit .env file and change:
   EBAY_ENVIRONMENT=sandbox
   ```

### For Production (After Keyset is Enabled):
1. **Enable Production Keyset** (follow steps above)
2. **Verify it's enabled** (check Developer Console)
3. **Get Production OAuth Token:**
   ```bash
   python -m streamlit run start.py
   # Go to Step 2: Login
   # Make sure environment is set to "production"
   ```
4. **Test with this script:**
   ```bash
   python check_keyset_status.py
   ```
5. **Create production drafts:**
   ```bash
   python -m streamlit run start.py
   # Go to Step 5: Create Listings
   ```

## Common Questions

### Q: Why is my Sandbox keyset enabled but Production is disabled?
**A:** Sandbox keysets are automatically enabled for testing. Production keysets require compliance with notification requirements.

### Q: How long does it take to enable?
**A:** Usually **within minutes** after setting up notifications. Sometimes up to 24 hours.

### Q: Can I use Production without enabling the keyset?
**A:** No. You must enable the keyset to make production API calls.

### Q: Will setting up email notifications spam me?
**A:** No. You'll only receive emails when marketplace accounts are actually deleted or closed (rare events).

### Q: What if I can't find the notifications section?
**A:** 
- Make sure you're looking at the **Production** keyset (not Sandbox)
- Try different browsers
- Contact eBay Developer Support

## Need Help?

- **eBay Developer Documentation**: https://developer.ebay.com/
- **eBay Developer Support**: Contact through Developer Console
- **Check Keyset Status**: Run `python check_keyset_status.py`
