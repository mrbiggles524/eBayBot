# Setting Up OAuth with ngrok (Automatic Token Renewal)

## Why ngrok?

eBay requires HTTPS URLs for OAuth redirect URIs, but `https://localhost` doesn't work without SSL certificates. **ngrok** creates a secure tunnel that gives you a public HTTPS URL that forwards to your local `localhost:8080`.

## Step 1: Install ngrok

### Windows:
1. Download from: https://ngrok.com/download
2. Extract `ngrok.exe` to a folder (e.g., `C:\ngrok\`)
3. Or use Chocolatey: `choco install ngrok`

### Mac:
```bash
brew install ngrok
```

### Linux:
```bash
# Download and extract
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

## Step 2: Get ngrok Auth Token (Free Account)

1. Sign up at: https://dashboard.ngrok.com/signup (free)
2. Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken
3. Run: `ngrok config add-authtoken YOUR_TOKEN`

## Step 3: Start ngrok Tunnel

**Before starting the Streamlit app**, run:

```bash
ngrok http 8080
```

This will give you output like:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8080
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

## Step 4: Configure eBay Redirect URI

1. Go to eBay Developer Console → Your App → User Tokens
2. Click "Add eBay Redirect URL"
3. Fill in:
   - **RuName:** `ngrok_callback` (or any name)
   - **Display Title:** `OAuth Callback`
   - **OAuth Enabled:** ✓ (checked)
   - **Your auth accepted URL:** `https://abc123.ngrok-free.app/callback`
   - **Your auth declined URL:** `https://abc123.ngrok-free.app/callback`
   - **Privacy policy URL:** `https://` (or leave blank)
4. Click **Save**

## Step 5: Update Bot Configuration

1. Open your `.env` file
2. Add/update:
   ```
   OAUTH_REDIRECT_URI=https://abc123.ngrok-free.app/callback
   ```
   (Replace `abc123.ngrok-free.app` with your actual ngrok URL)

## Step 6: Start the Bot

1. **Keep ngrok running** (the terminal window with `ngrok http 8080`)
2. Start your Streamlit app:
   ```bash
   python -m streamlit run start.py
   ```
3. Go to Step 2 → OAuth Login
4. It should work now!

## Important Notes

⚠️ **ngrok URL Changes**: Free ngrok URLs change each time you restart ngrok (unless you have a paid plan with a static domain). You'll need to:
- Update the redirect URI in eBay Developer Console each time
- Update `OAUTH_REDIRECT_URI` in your `.env` file

💡 **Tip**: For development, you can keep ngrok running in the background. The URL stays the same as long as ngrok is running.

## Alternative: Use Manual Token (No Setup Needed)

If ngrok setup is too complicated, you can:
1. Use the manual token method (no OAuth setup needed)
2. Get a new token every 2 hours (or set longer expiration in Developer Console)
3. The token you got earlier should work for 18 months if it's Auth 'n' Auth format

## Troubleshooting

**"ngrok URL not found" error:**
- Make sure ngrok is running
- Check that the URL in `.env` matches the ngrok URL

**"Redirect URI mismatch" error:**
- Make sure the URL in eBay Developer Console matches exactly (including `/callback`)
- Check that `OAUTH_REDIRECT_URI` in `.env` matches

**ngrok connection refused:**
- Make sure port 8080 is not blocked by firewall
- Check that no other app is using port 8080
