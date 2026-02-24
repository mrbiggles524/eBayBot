# How to Enter Your eBay API Credentials

## Your Credentials (Sandbox)

Based on your eBay Developer account, here's what you need to enter:

### Mapping Your Credentials

| eBay Developer Portal | Setup UI Field | Your Value |
|----------------------|---------------|------------|
| **App ID (Client ID)** | App ID (Client ID) | *(from eBay Developer Portal → Application Keys)* |
| **Dev ID** | Dev ID | *(from eBay Developer Portal → Application Keys)* |
| **Cert ID (Client Secret)** | Cert ID (Client Secret) | *(from eBay Developer Portal → Application Keys)* |

## Step-by-Step Instructions

### 1. Run the Setup UI

```bash
python -m streamlit run start.py
```

Or double-click `run_setup_ui.bat`

### 2. Enter Your Credentials

In **Step 1: API Credentials**, enter:

- **App ID (Client ID)**: *(copy from eBay Developer Portal → My Account → Application Keys)*
- **Dev ID**: *(copy from eBay Developer Portal)*
- **Cert ID (Client Secret)**: *(copy from eBay Developer Portal)*
- **Environment**: Select **Sandbox** (since these are sandbox credentials)

### 3. Important Notes

⚠️ **Security Warning**: 
- These are your **Sandbox** credentials (for testing)
- Never share these credentials publicly
- The `.env` file contains these - don't commit it to git (it's in `.gitignore`)

✅ **For Production Later**:
- When you're ready for real listings, you'll need to create a **Production** keyset
- The Production App ID will be different
- The Dev ID will be the same
- You'll get a new Cert ID for production

### 4. After Entering Credentials

1. Click "Save Credentials"
2. Proceed to Step 2: Login
3. Click "Login with OAuth" - this will use your credentials to authenticate
4. Complete Steps 3 and 4

## What Happens Next

After entering your credentials:
- They're saved to `.env` file
- Used for OAuth authentication
- Used to access eBay APIs
- All API calls will use these credentials

## Troubleshooting

**"Invalid credentials" error:**
- Double-check you copied the entire App ID and Cert ID
- Make sure there are no extra spaces
- Verify you selected "Sandbox" environment

**"Token generation failed":**
- Make sure your credentials are correct
- Check that you're using Sandbox credentials with Sandbox environment
- Try refreshing and re-entering

## Next Steps

Once credentials are saved:
1. ✅ Step 1: Credentials (you're here)
2. ⏭️ Step 2: Login with OAuth
3. ⏭️ Step 3: Auto-Configure
4. ⏭️ Step 4: Verify

Then you'll be ready to create listings!
