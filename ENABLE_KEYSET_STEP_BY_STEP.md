# Step-by-Step: Enable Production Keyset

## You're on the Right Page! ✅

You're looking at the **Marketplace Account Deletion** page in eBay Developer Console. This is exactly where you need to be.

## Two Options

### Option 1: Opt Out (EASIEST - If You Don't Store eBay Data)

**If your bot doesn't store eBay user data permanently**, you can opt out:

1. **Find the Toggle**
   - Look for **"Not persisting eBay data"** toggle/switch
   - It should be on the same page you're viewing
   - Turn it **ON**

2. **Confirm the Pop-up**
   - A pop-up will appear asking you to confirm
   - Click **"Confirm"**

3. **Select Exemption Reason**
   - You'll see radio buttons with exemption reasons
   - Select the one that applies:
     - "I don't store eBay user data"
     - "I only use eBay data temporarily"
     - Or similar option
   - You can add additional notes if needed

4. **Submit**
   - Click **"Submit"** button
   - Your keyset should be enabled automatically!

**This is the fastest way if you're not storing user data.**

---

### Option 2: Subscribe to Notifications (If You Store eBay Data)

**If your bot stores eBay user data**, you need to set up notifications:

#### Step 1: Enter Alert Email

1. **Find the Email Field**
   - Look for a field labeled **"Alert email"** or **"Email address"**
   - It should be near the top of the form
   - This email is ONLY used to alert you if your endpoint fails
   - Enter your email address

2. **Save the Email**
   - Click the **"Save"** button next to the email field
   - This must be saved BEFORE you can set the endpoint

#### Step 2: Set Notification Endpoint URL

1. **Find the Endpoint URL Field**
   - Look for **"Notification Endpoint URL"** field
   - This must be an **HTTPS** URL (not HTTP)
   - It must be a URL you own/control

2. **Options for Endpoint:**
   
   **Option A: Use a Simple Webhook Service (Easiest)**
   - Use a service like:
     - https://webhook.site (free, temporary for testing)
     - https://requestbin.com (free, temporary)
     - Or any HTTPS endpoint you control
   
   **Option B: Set Up Your Own Server**
   - You need a server that can:
     - Accept HTTPS POST requests
     - Respond to GET requests (for challenge code)
     - Return HTTP 200 OK responses

3. **Enter the URL**
   - Format: `https://your-domain.com/ebay-notifications`
   - Or use a webhook service URL

#### Step 3: Set Verification Token

1. **Find Verification Token Field**
   - Look for **"Verification token"** field
   - Must be **32-80 characters**
   - Allowed characters: letters, numbers, underscore (_), hyphen (-)
   - Example: `my-verification-token-12345-abcdef`

2. **Generate a Token**
   - You can use any random string
   - Example: `ebay-bot-verification-2025-abc123xyz`
   - Make it unique and secure

#### Step 4: Save and Verify

1. **Click Save**
   - After entering endpoint URL and verification token
   - Click the **"Save"** button
   - eBay will immediately send a challenge code to your endpoint

2. **Handle the Challenge**
   - Your endpoint must respond to the challenge
   - See code examples below

3. **Test Notification**
   - Once saved, click **"Send Test Notification"** button
   - Verify your endpoint receives it
   - Your keyset should be enabled!

---

## If You Can't Find the Email Field

The email field might be:
- **Above** the endpoint URL section
- In a **separate section** labeled "Alert Settings"
- **Hidden** until you scroll down
- **Required** before you can set the endpoint

**Try this:**
1. Scroll up and down the page
2. Look for any input fields
3. Check if there's a "Save" button that's disabled (means you need to fill email first)
4. Look for tooltips or help icons (?) that might explain the layout

---

## Quick Code for Endpoint (If Needed)

If you need to set up an endpoint, here's a simple Python Flask example:

```python
from flask import Flask, request, jsonify
import hashlib

app = Flask(__name__)

VERIFICATION_TOKEN = "your-verification-token-here"  # Same as you entered
ENDPOINT_URL = "https://your-domain.com/ebay-notifications"  # Same as you entered

@app.route('/ebay-notifications', methods=['GET', 'POST'])
def ebay_notifications():
    if request.method == 'GET':
        # Handle challenge code
        challenge_code = request.args.get('challenge_code')
        if challenge_code:
            # Hash: challengeCode + verificationToken + endpoint
            m = hashlib.sha256()
            m.update(challenge_code.encode())
            m.update(VERIFICATION_TOKEN.encode())
            m.update(ENDPOINT_URL.encode())
            response_hash = m.hexdigest()
            return jsonify({"challengeResponse": response_hash}), 200
        return "OK", 200
    
    elif request.method == 'POST':
        # Handle actual notification
        notification = request.json
        # Process the notification (delete user data, etc.)
        print(f"Received notification: {notification}")
        return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context='adhoc')  # HTTPS required
```

---

## Recommended: Use Opt-Out (Option 1)

**For your use case (creating listings, not storing user data):**

1. **Toggle "Not persisting eBay data" to ON**
2. **Select exemption reason**
3. **Submit**

This is much simpler and should enable your keyset immediately!

---

## After Enabling

1. **Verify Keyset is Enabled:**
   - Go back to **Application Keys** page
   - Your Production keyset should NOT say "disabled"
   - You should see your App ID, Dev ID, Cert ID

2. **Test It:**
   ```bash
   python check_keyset_status.py
   ```

3. **Start Using Production:**
   - Your keyset is now enabled!
   - You can create production drafts
   - Run: `python -m streamlit run start.py`

---

## Still Can't Find It?

**Try:**
1. Refresh the page
2. Check if you're on the **Production** keyset (not Sandbox)
3. Look for any collapsed/expandable sections
4. Check browser console for JavaScript errors
5. Try a different browser

**Or contact eBay Developer Support** - they can help you navigate the page.
