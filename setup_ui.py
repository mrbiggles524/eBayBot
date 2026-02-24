"""Simple web UI for eBay Bot setup using Streamlit."""
import streamlit as st
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    st.set_page_config(
        page_title="eBay Card Listing Bot - Setup",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 eBay Card Listing Bot - Setup Wizard")
    st.markdown("Welcome! This wizard will help you set up your eBay bot in just a few steps.")
    
    # Sidebar for navigation
    st.sidebar.title("📋 Setup Steps")
    st.sidebar.markdown("---")
    
    steps = [
        ("1. API Credentials", "Enter your eBay API keys"),
        ("2. Login", "Authenticate with eBay"),
        ("3. Auto-Configure", "Fetch your account settings"),
        ("4. Verify", "Confirm everything is ready"),
        ("5. Create Listings", "List cards from checklist")
    ]
    
    step_names = [step[0] for step in steps]
    current_step_name = st.sidebar.radio(
        "Current Step",
        step_names,
        index=0,
        label_visibility="collapsed"
    )
    
    # Show step descriptions
    st.sidebar.markdown("---")
    for i, (name, desc) in enumerate(steps):
        if name == current_step_name:
            st.sidebar.markdown(f"**{name}** ✓")
            st.sidebar.caption(desc)
        else:
            st.sidebar.markdown(f"{name}")
            st.sidebar.caption(desc)
    
    current_step = current_step_name
    
    # Step 1: API Credentials
    if current_step == "1. API Credentials":
        step1_api_credentials()
    
    # Step 2: Login
    elif current_step == "2. Login":
        step2_login()
    
    # Step 3: Auto-Configure
    elif current_step == "3. Auto-Configure":
        step3_autoconfigure()
    
    # Step 4: Verify
    elif current_step == "4. Verify":
        step4_verify()
    
    # Step 5: Create Listings
    elif current_step == "5. Create Listings":
        step5_create_listings()

def step1_api_credentials():
    st.header("Step 1: Configure eBay API Credentials")
    st.info("""
    You'll need to get these from the [eBay Developers Program](https://developer.ebay.com/).
    
    1. Go to https://developer.ebay.com/
    2. Sign in with your eBay account
    3. Navigate to "Application Keys" in your developer account
    4. Copy your **App ID (Client ID)**, **Dev ID**, and **Cert ID (Client Secret)**
    5. Make sure you're using the correct environment (Sandbox for testing, Production for real listings)
    """)
    
    with st.expander("📋 Where to find your credentials"):
        st.markdown("""
        In your eBay Developer account:
        - Go to **Application Keys** section
        - Find your keyset (Sandbox or Production)
        - Copy these three values:
          - **App ID (Client ID)**: Starts with your name (e.g., `YourName-BOT-SBX-...`)
          - **Dev ID**: A UUID format (e.g., `56df3e2d-2e78-4a61-b0a3-...`)
          - **Cert ID (Client Secret)**: Starts with `SBX-` for Sandbox or `PROD-` for Production
        """)
    
    # Check if .env exists and load existing values
    env_vars = {}  # Initialize empty dict
    env_exists = os.path.exists('.env')
    
    if env_exists:
        st.success("✓ .env file found!")
        
        # Try to load existing values
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        except Exception as e:
            st.warning(f"⚠ Could not read .env file: {e}")
    else:
        st.warning("⚠ No .env file found. We'll create one for you.")
    
    with st.form("api_credentials_form"):
        st.subheader("Enter Your eBay API Credentials")
        
        app_id = st.text_input(
            "App ID (Client ID)",
            value=env_vars.get('EBAY_APP_ID', ''),
            help="Your eBay Application ID",
            type="default"
        )
        
        dev_id = st.text_input(
            "Dev ID",
            value=env_vars.get('EBAY_DEV_ID', ''),
            help="Your eBay Developer ID"
        )
        
        cert_id = st.text_input(
            "Cert ID (Client Secret)",
            value=env_vars.get('EBAY_CERT_ID', ''),
            help="Your eBay Certificate ID",
            type="password"
        )
        
        environment = st.selectbox(
            "Environment",
            ["sandbox", "production"],
            index=0 if env_vars.get('EBAY_ENVIRONMENT', 'sandbox') == 'sandbox' else 1,
            help="Use 'sandbox' for testing, 'production' for real listings"
        )
        
        # Warning if production is selected
        if environment == "production":
            st.warning("""
            ⚠️ **Production Environment Selected**
            
            **Important:** Make sure your Production keyset is enabled in eBay Developer Console.
            
            If you see "Your Keyset is currently disabled" in eBay Developer Console, you need to:
            1. Comply with marketplace deletion/account closure notification process, OR
            2. Apply for an exemption
            
            **For now, use Sandbox** to test the bot. Switch to Production after your keyset is enabled.
            """)
        
        submitted = st.form_submit_button("Save Credentials", type="primary")
        
        if submitted:
            if not all([app_id, dev_id, cert_id]):
                st.error("❌ Please fill in all required fields!")
            else:
                save_env_file({
                    'EBAY_APP_ID': app_id,
                    'EBAY_DEV_ID': dev_id,
                    'EBAY_CERT_ID': cert_id,
                    'EBAY_ENVIRONMENT': environment,
                    'USE_OAUTH': 'true'
                })
                st.success("✅ Credentials saved successfully!")
                st.balloons()
                st.info("👉 Continue to Step 2: Login")

def step2_login():
    st.header("Step 2: Login to eBay")
    
    # Check if credentials are set
    if not check_credentials():
        st.error("❌ Please complete Step 1 first (API Credentials)")
        return
    
    # Tabs for different login methods
    tab1, tab2 = st.tabs(["🔐 OAuth Login (Automatic)", "📝 Manual Token Entry (Alternative)"])
    
    with tab1:
        st.info("""
        This will open your browser to authorize the application.
        After you authorize, the token will be saved automatically.
        
        **Note:** If eBay's OAuth server is down (500 error), use the "Manual Token Entry" tab instead.
        """)
        
        col1, col2 = st.columns(2)
    
    with col1:
        login_button = st.button("🔐 Login with OAuth", type="primary", use_container_width=True)
        
        if login_button:
            try:
                from ebay_oauth import eBayOAuth
                oauth = eBayOAuth()
                
                # Use httpbin.org redirect URI (HTTPS, already configured)
                oauth.redirect_uri = "https://httpbin.org/anything"
                
                # Use explicit scopes for Inventory API
                scopes = [
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.account",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
                ]
                
                # Show authorization URL with explicit scopes
                auth_url = oauth.get_authorization_url(scopes=scopes)
                
                st.info("""
                **Follow these steps:**
                1. A browser window should open automatically
                2. If not, click the link below to open it manually
                3. Sign in with: **TESTUSER_manbot**
                4. **CHECK ALL PERMISSION BOXES** (especially "View and manage your inventory and offers")
                5. Authorize the application
                6. You'll be redirected to httpbin.org
                7. Copy the 'code' value from the JSON response
                8. Paste it in the field below
                """)
                
                st.markdown(f"[🔗 Click here to open authorization page]({auth_url})")
                
                # Manual code entry since httpbin doesn't redirect back to app
                st.markdown("---")
                st.subheader("After Authorization:")
                st.info("You'll be redirected to httpbin.org. Look for the 'code' value in the JSON response under 'args' -> 'code'")
                
                auth_code = st.text_input(
                    "Authorization Code (from httpbin.org)",
                    placeholder="Paste the code value here",
                    help="Get this from httpbin.org JSON response, in the 'args' -> 'code' field"
                )
                
                if st.button("🔐 Exchange Code for Token", type="primary", use_container_width=True):
                    if not auth_code:
                        st.error("Please enter the authorization code from httpbin.org")
                    else:
                        with st.spinner("Exchanging code for token..."):
                            try:
                                result = oauth.exchange_code_for_token(auth_code)
                                
                                if result.get('success'):
                                    st.success("✅ Login successful!")
                                    st.balloons()
                                    st.info("Token saved. You can now proceed to Step 3.")
                                    # Force refresh to update login status
                                    st.rerun()
                                else:
                                    error_msg = result.get('error', 'Unknown error')
                                    error_str = str(error_msg)
                                    
                                    st.error(f"❌ Login failed: {error_str}")
                                    
                                    if isinstance(error_msg, dict):
                                        error_id = error_msg.get('error_id', '')
                                        error_desc = error_msg.get('error_description', '')
                                        if error_id == 'invalid_request':
                                            st.warning("""
                                            **Redirect URI Mismatch**
                                            
                                            Make sure the redirect URI is registered in Developer Console:
                                            1. Go to: https://developer.ebay.com/my/keys
                                            2. Click 'User Tokens' for your Sandbox app
                                            3. Add redirect URL: https://httpbin.org/anything
                                            4. Check 'OAuth Enabled'
                                            5. Save
                                            """)
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                st.exception(e)
                        
                        # Check for timeout
                        if 'timeout' in error_str.lower() or 'No authorization code' in error_str:
                            st.error("❌ Login timed out or was cancelled")
                            st.warning("""
                            **The authorization process timed out.**
                            
                            **What happened:**
                            - The browser may not have opened
                            - You may not have completed the authorization
                            - The callback server may have timed out
                            
                            **What to do:**
                            1. Make sure port 8080 is not blocked by your firewall
                            2. Click "Login with OAuth" again
                            3. Complete the authorization in your browser within 5 minutes
                            4. Make sure you're redirected back to the app
                            """)
                        # Check for specific eBay server errors
                        elif 'temporarily_unavailable' in error_str or '500' in error_str:
                            st.error("❌ eBay authorization server is temporarily unavailable")
                            st.warning("""
                            **This is a temporary issue with eBay's servers, not your setup.**
                            
                            Please try again in a few minutes. eBay's OAuth service may be experiencing high load.
                            
                            **What to do:**
                            1. Wait 2-3 minutes
                            2. Click "Login with OAuth" again
                            3. If it persists, check eBay's status page
                            """)
                        elif 'invalid_client' in error_str or 'unauthorized' in error_str:
                            st.error("❌ Authentication failed")
                            st.warning("""
                            **Your API credentials may be incorrect.**
                            
                            Please verify:
                            - Your App ID, Dev ID, and Cert ID are correct
                            - You selected the correct environment (Sandbox/Production)
                            - Your credentials match the environment you selected
                            """)
                        else:
                            st.error(f"❌ Login failed: {error_msg}")
                            st.info("If this persists, try refreshing the token or check your credentials in Step 1.")
            except Exception as e:
                error_str = str(e)
                if 'temporarily_unavailable' in error_str or '500' in error_str:
                    st.error("❌ eBay authorization server is temporarily unavailable")
                    st.warning("Please try again in a few minutes. This is a temporary eBay server issue.")
                elif 'Address already in use' in error_str or 'port' in error_str.lower():
                    st.error("❌ Port 8080 is already in use")
                    st.warning("""
                    **Another application is using port 8080.**
                    
                    **Solutions:**
                    1. Close any other applications using port 8080
                    2. Restart your computer
                    3. Or manually copy the authorization URL and complete the process
                    """)
                else:
                    st.error(f"❌ Error during login: {str(e)}")
                    st.exception(e)
    
    with col2:
        if st.button("🔄 Refresh Token", use_container_width=True):
            with st.spinner("Refreshing token..."):
                try:
                    from ebay_oauth import eBayOAuth
                    oauth = eBayOAuth()
                    result = oauth.refresh_token()
                    
                    if result.get('success'):
                        st.success("✅ Token refreshed!")
                    else:
                        st.error(f"❌ Refresh failed: {result.get('error')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.header("Manual Token Entry")
        st.warning("""
        **Use this method if OAuth is not working (eBay server errors).**
        
        **This is the EASIEST method** - no redirect URL setup needed!
        
        You can get your User Token directly from eBay's Developer Console.
        """)
        
        st.info("""
        💡 **Tip:** You don't need to set up redirect URLs for this method!
        
        Just click "Get a Token from eBay via Your Browser" in the Developer Console,
        sign in, copy the token, and paste it here. That's it!
        """)
        
        with st.expander("📖 How to get your User Token from eBay Developer Console"):
            st.markdown("""
            **Steps to get your User Token:**
            
            1. Go to https://developer.ebay.com/
            2. Sign in with your eBay account
            3. Go to **Application Keys** section
            4. Find your application (the one with your App ID: `YourName-BOT-PRD-...` or `YourName-BOT-SBX-...`)
            5. Click **"User Tokens"** next to your App ID
            6. **IMPORTANT:** First, add a Redirect URL:
               - Click **"Add eBay Redirect URL"** or **"Click here to add one"**
               - **RuName**: Enter any name (e.g., `eBayBot-Callback`)
               - **Redirect URL**: Enter `http://localhost:8080/callback`
               - Click **"Save"**
            7. Click **"Get a Token from eBay via Your Browser"**
            8. Sign in and authorize the application
            9. Copy the **User Token** (it's a very long string - copy the entire thing)
            10. Paste it below
            
            **For Sandbox:**
            - Use the Sandbox User Token (from Sandbox environment)
            - Make sure your environment is set to "sandbox" in Step 1
            
            **For Production:**
            - Use the Production User Token (from Production environment)  
            - Make sure your environment is set to "production" in Step 1
            
            **Token Format:**
            - Usually starts with `v^1.1#` or `eyJhbGciOiJ...`
            - It's a very long string - make sure you copy it all
            
            **See `SETUP_REDIRECT_URL.md` for detailed redirect URL setup instructions.**
            """)
        
        with st.form("manual_token_form"):
            st.subheader("Enter Your User Token")
            
            user_token = st.text_input(
                "User Token",
                help="Paste your User Token from eBay Developer Console",
                type="password"
            )
            
            token_expires = st.number_input(
                "Token Expires In (seconds)",
                min_value=0,
                value=7200,
                help="How long until the token expires (default: 7200 = 2 hours)"
            )
            
            submitted = st.form_submit_button("💾 Save Token", type="primary")
            
            if submitted:
                if not user_token:
                    st.error("❌ Please enter your User Token")
                else:
                    try:
                        from ebay_oauth import eBayOAuth
                        oauth = eBayOAuth()
                        
                        # Save token manually
                        import time
                        token_data = {
                            "access_token": user_token,
                            "token_type": "Bearer",
                            "expires_in": token_expires,
                            "expires_at": time.time() + token_expires
                        }
                        oauth.save_token(token_data)
                        
                        st.success("✅ Token saved successfully!")
                        st.balloons()
                        st.info("Token saved. You can now proceed to Step 3.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error saving token: {str(e)}")
    
    # Check login status
    st.markdown("---")
    st.subheader("Login Status")
    try:
        from ebay_oauth import eBayOAuth
        oauth = eBayOAuth()
        token = oauth.get_access_token()
        if token:
            st.success("✅ You are logged in!")
            st.info("👉 Continue to Step 3: Auto-Configure")
        else:
            st.warning("⚠ Not logged in. Use one of the login methods above.")
    except:
        st.warning("⚠ Not logged in. Use one of the login methods above.")

def step3_autoconfigure():
    st.header("Step 3: Auto-Configure from eBay Account")
    st.info("""
    This will automatically fetch all required settings from your eBay account:
    - Fulfillment policies
    - Payment policies
    - Return policies
    - Merchant locations
    
    **Click the button below to fetch and configure everything automatically.**
    """)
    
    # Check if logged in
    current_username = None
    logged_in = False
    try:
        from ebay_oauth import eBayOAuth
        oauth = eBayOAuth()
        token = oauth.get_access_token()
        if token:
            logged_in = True
            # Try to get current username
            try:
                from ebay_setup import eBayAutoSetup
                setup = eBayAutoSetup()
                user_info = setup.get_current_user()
                if user_info.get('success'):
                    current_username = user_info.get('data', {}).get('username', '')
            except:
                pass
    except:
        pass
    
    if not logged_in:
        st.error("❌ Please complete Step 2 (Login) first!")
        st.info("Go back to Step 2 and save your User Token.")
        return
    
    # Show current logged-in user
    if current_username:
        st.success(f"👤 Logged in as: **{current_username}**")
    else:
        st.success("✅ You are logged in!")
    
    st.markdown("---")
    
    user_id = st.text_input(
        "eBay User ID (Optional)",
        help="Leave empty to use your current logged-in user, or enter a different eBay username",
        placeholder="your_ebay_username",
        value=""  # Empty by default - will use logged-in user
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🚀 Auto-Configure Now", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                from ebay_setup import eBayAutoSetup
                setup = eBayAutoSetup()
                
                status_text.info("🔄 Fetching user information...")
                progress_bar.progress(10)
                
                result = setup.setup_from_user_id(user_id if user_id else None)
                
                progress_bar.progress(100)
                
                if result.get('success'):
                    st.success("✅ Auto-configuration complete!")
                    st.balloons()
                    
                    setup_info = result.get('setup_info', {})
                    
                    # Show what was found
                    st.subheader("📋 Configuration Found:")
                    
                    policies = setup_info.get('policies', {})
                    locations = setup_info.get('locations', {})
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write("**Policies:**")
                        fulfillment_count = len(policies.get('fulfillment', []))
                        payment_count = len(policies.get('payment', []))
                        return_count = len(policies.get('return', []))
                        st.write(f"- Fulfillment: {fulfillment_count} found")
                        st.write(f"- Payment: {payment_count} found")
                        st.write(f"- Return: {return_count} found")
                    
                    with col_b:
                        st.write("**Locations:**")
                        location_count = locations.get('count', 0)
                        st.write(f"- Merchant Locations: {location_count} found")
                    
                    # Show recommendations
                    st.subheader("✅ Configuration Applied:")
                    recommendations = setup_info.get('recommendations', [])
                    if recommendations:
                        for rec in recommendations:
                            if not rec.startswith('#'):
                                st.code(rec, language=None)
                    else:
                        st.warning("⚠ No policies or locations found. You may need to create them in eBay Seller Hub first.")
                    
                    if setup_info.get('config_saved', {}).get('success'):
                        st.success("✅ Configuration saved to .env file")
                        st.info("👉 Continue to Step 4: Verify")
                        # Auto-refresh to show updated status
                        st.rerun()
                    else:
                        st.warning("⚠ Configuration fetched but not saved. Check the error above.")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    st.error(f"❌ Setup failed: {error_msg}")
                    
                    # Provide helpful guidance
                    if 'policies' in str(error_msg).lower() or 'policy' in str(error_msg).lower():
                        st.warning("""
                        **No policies found in your eBay account.**
                        
                        You may need to create policies first:
                        1. Go to eBay Seller Hub
                        2. Navigate to Account → Business Policies
                        3. Create at least one Fulfillment, Payment, and Return policy
                        4. Then run Auto-Configure again
                        """)
            except Exception as e:
                st.error(f"❌ Error during setup: {str(e)}")
                st.exception(e)
    
    with col2:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    # Show current status
    st.markdown("---")
    st.subheader("Current Status")
    try:
        from config import Config
        config = Config()
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**Policies:**")
            st.write(f"Fulfillment: {'✅ Set' if config.FULFILLMENT_POLICY_ID else '❌ Not set'}")
            st.write(f"Payment: {'✅ Set' if config.PAYMENT_POLICY_ID else '❌ Not set'}")
            st.write(f"Return: {'✅ Set' if config.RETURN_POLICY_ID else '❌ Not set'}")
        
        with col_b:
            st.write("**Location:**")
            st.write(f"Merchant Location: {'✅ Set' if config.MERCHANT_LOCATION_KEY else '❌ Not set'}")
    except:
        pass

def step4_verify():
    st.header("Step 4: Verify Setup")
    st.info("Verify that everything is configured correctly.")
    
    # Quick status check first
    st.subheader("Quick Status Check")
    try:
        from config import Config
        config = Config()
        
        status_items = []
        status_items.append(("API Credentials", bool(config.EBAY_APP_ID and config.EBAY_DEV_ID and config.EBAY_CERT_ID)))
        status_items.append(("Authentication", bool(config.ebay_token)))
        status_items.append(("Fulfillment Policy", bool(config.FULFILLMENT_POLICY_ID)))
        status_items.append(("Payment Policy", bool(config.PAYMENT_POLICY_ID)))
        status_items.append(("Return Policy", bool(config.RETURN_POLICY_ID)))
        status_items.append(("Merchant Location", bool(config.MERCHANT_LOCATION_KEY)))
        
        all_good = all(item[1] for item in status_items)
        
        for name, status in status_items:
            if status:
                st.success(f"✅ {name}")
            else:
                st.error(f"❌ {name}")
        
        if not all_good:
            st.warning("""
            ⚠️ **Some configuration is missing!**
            
            **What to do:**
            1. Go back to **Step 3: Auto-Configure**
            2. Click **"🚀 Auto-Configure Now"** button
            3. This will fetch policies and locations from your eBay account
            4. Come back to Step 4 and verify again
            
            **If Auto-Configure doesn't find policies:**
            - You may need to create them in eBay Seller Hub first
            - Go to: eBay Seller Hub → Account → Business Policies
            - Create at least one Fulfillment, Payment, and Return policy
            - Then run Auto-Configure again
            """)
    except Exception as e:
        st.warning(f"Could not check status: {str(e)}")
    
    st.markdown("---")
    
    if st.button("🔍 Full Verification", type="primary", use_container_width=True):
        with st.spinner("Checking configuration..."):
            try:
                from ebay_setup import eBayAutoSetup
                setup = eBayAutoSetup()
                result = setup.verify_setup()
                
                if result.get('success'):
                    st.success("✅ " + result.get('message', 'All checks passed!'))
                    st.balloons()
                    
                    st.subheader("🎉 Setup Complete!")
                    st.success("""
                    Your eBay bot is now configured and ready to use!
                    
                    **Next Steps:**
                    1. Create a CSV file with your cards (see `cards_example.csv`)
                    2. Run the bot:
                       ```bash
                       python ebay_bot.py --csv your_cards.csv
                       ```
                    
                    **Or test with a card set:**
                    ```bash
                    python ebay_bot.py "Set Name"
                    ```
                    """)
                else:
                    st.error("❌ Setup verification found issues:")
                    for issue in result.get('issues', []):
                        st.error(f"  - {issue}")
                    
                    st.warning("""
                    **To fix these issues:**
                    
                    1. **Missing Policies/Location:**
                       - Go to **Step 3: Auto-Configure**
                       - Click **"🚀 Auto-Configure Now"**
                       - This will fetch them from your eBay account
                    
                    2. **If no policies found:**
                       - Create policies in eBay Seller Hub
                       - Account → Business Policies
                       - Create Fulfillment, Payment, and Return policies
                       - Then run Auto-Configure again
                    
                    3. **Missing Token:**
                       - Go to **Step 2: Login**
                       - Use Manual Token Entry
                       - Get token from eBay Developer Console
                    """)
                    
                    if result.get('warnings'):
                        st.warning("⚠ Warnings:")
                        for warning in result.get('warnings', []):
                            st.warning(f"  - {warning}")
            except Exception as e:
                st.error(f"❌ Error during verification: {str(e)}")
                st.exception(e)
    
    # Show current configuration
    st.subheader("Current Configuration")
    try:
        from config import Config
        config = Config()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Credentials:**")
            st.write(f"App ID: {'✅ Set' if config.EBAY_APP_ID else '❌ Not set'}")
            st.write(f"Dev ID: {'✅ Set' if config.EBAY_DEV_ID else '❌ Not set'}")
            st.write(f"Cert ID: {'✅ Set' if config.EBAY_CERT_ID else '❌ Not set'}")
            st.write(f"Environment: {config.EBAY_ENVIRONMENT}")
        
        with col2:
            st.write("**Policies:**")
            st.write(f"Fulfillment: {'✅ Set' if config.FULFILLMENT_POLICY_ID else '❌ Not set'}")
            st.write(f"Payment: {'✅ Set' if config.PAYMENT_POLICY_ID else '❌ Not set'}")
            st.write(f"Return: {'✅ Set' if config.RETURN_POLICY_ID else '❌ Not set'}")
            st.write(f"Location: {'✅ Set' if config.MERCHANT_LOCATION_KEY else '❌ Not set'}")
        
        # Check token
        try:
            from ebay_oauth import eBayOAuth
            oauth = eBayOAuth()
            token = oauth.get_access_token()
            st.write(f"**Authentication:** {'✅ Logged in' if token else '❌ Not logged in'}")
        except:
            st.write("**Authentication:** ❌ Not logged in")
            
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")

def save_env_file(vars_dict):
    """Save environment variables to .env file."""
    env_file = '.env'
    env_example = 'env_example.txt'
    
    # Read existing .env if it exists
    existing_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=', 1)[0]
                    value = line.split('=', 1)[1] if '=' in line else ''
                    existing_vars[key] = value
    
    # Update with new values
    existing_vars.update(vars_dict)
    
    # Read template
    template_lines = []
    if os.path.exists(env_example):
        with open(env_example, 'r') as f:
            template_lines = f.readlines()
    
    # Write .env file
    with open(env_file, 'w') as f:
        # Write template with updated values
        for line in template_lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                key = line_stripped.split('=', 1)[0]
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
                else:
                    f.write(line)
            else:
                f.write(line)
        
        # Add any new variables
        written_keys = set()
        for line in template_lines:
            if '=' in line and not line.strip().startswith('#'):
                written_keys.add(line.split('=', 1)[0])
        
        for key, value in existing_vars.items():
            if key not in written_keys:
                f.write(f"{key}={value}\n")

def check_credentials():
    """Check if API credentials are set."""
    try:
        from config import Config
        config = Config()
        return bool(config.EBAY_APP_ID and config.EBAY_DEV_ID and config.EBAY_CERT_ID)
    except:
        return False

def step5_create_listings():
    """Step 5: Create listings from Beckett checklist."""
    st.header("Step 5: Create Listings from Beckett Checklist")
    st.info("""
    Enter a Beckett checklist URL to fetch all cards from a set, then specify quantities for each card you want to list.
    """)
    
    # Check if setup is complete
    try:
        from config import Config
        config = Config()
        if not (config.EBAY_APP_ID and config.EBAY_DEV_ID and config.EBAY_CERT_ID):
            st.error("❌ Please complete Steps 1-4 first!")
            st.info("You need to configure your API credentials, login, and set up policies before creating listings.")
            return
        if not config.ebay_token:
            st.error("❌ Please complete Step 2 (Login) first!")
            return
        if not (config.FULFILLMENT_POLICY_ID and config.PAYMENT_POLICY_ID and config.RETURN_POLICY_ID):
            st.error("❌ Please complete Step 3 (Auto-Configure) first!")
            st.info("You need to set up your policies before creating listings.")
            return
    except Exception as e:
        st.error(f"❌ Configuration error: {str(e)}")
        return
    
    st.success("✅ Setup complete! Ready to create listings.")
    st.markdown("---")
    
    # Step 1: Enter Listing Name/Description FIRST
    st.subheader("Step 1: Enter Listing Name/Description")
    st.info("Enter the main listing name/description. This will be the title of your eBay listing.")
    
    listing_title = st.text_input(
        "Listing Title/Name",
        value=st.session_state.get('listing_title', ''),
        placeholder="e.g., 2025-26 Topps Chrome Basketball Cards",
        help="This will be the main title of your eBay variation listing"
    )
    
    listing_description = st.text_area(
        "Listing Description (Optional)",
        value=st.session_state.get('listing_description', ''),
        placeholder="Enter a description for your listing...",
        help="Optional: Add a description that will appear in your eBay listing"
    )
    
    # Save to session state
    if listing_title:
        st.session_state['listing_title'] = listing_title
    if listing_description:
        st.session_state['listing_description'] = listing_description
    
    st.markdown("---")
    
    # Step 2: Select Checklist Type and Enter Beckett URL
    st.subheader("Step 2: Select Checklist Type and Enter Beckett URL")
    
    checklist_type = st.radio(
        "What type of cards do you want to list?",
        ["Base Cards", "Insert Cards", "Parallel Cards", "Numbered Cards / Autographs"],
        help="Select the type of checklist you want to fetch from Beckett"
    )
    
    # Map display names to internal types
    type_mapping = {
        "Base Cards": "base",
        "Insert Cards": "inserts",
        "Parallel Cards": "parallels",
        "Numbered Cards / Autographs": "numbered"
    }
    
    st.info("💡 **Supported Sources:**\n- Beckett.com (primary)\n- Cardsmiths Breaks (backup - automatically used if Beckett fails)")
    
    checklist_url = st.text_input(
        "Checklist URL (Beckett or Cardsmiths Breaks)",
        value=st.session_state.get('beckett_url', ''),
        placeholder="https://www.beckett.com/news/2025-26-topps-chrome-basketball-cards/ or https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/",
        help="Paste the full URL to a Beckett or Cardsmiths Breaks checklist page"
    )
    
    if st.button("🔍 Fetch Checklist", type="primary"):
        if not checklist_url:
            st.error("Please enter a checklist URL")
        elif not listing_title:
            st.error("Please enter a listing title first!")
        else:
            source_name = "Cardsmiths Breaks" if "cardsmithsbreaks.com" in checklist_url else "Beckett"
            with st.spinner(f"Fetching {checklist_type.lower()} from {source_name}..."):
                try:
                    from card_checklist import CardChecklistFetcher
                    fetcher = CardChecklistFetcher(source='beckett')
                    selected_type = type_mapping[checklist_type]
                    cards = fetcher.fetch_from_beckett_url(checklist_url, checklist_type=selected_type)
                    
                    if cards:
                        st.session_state['beckett_cards'] = cards
                        st.session_state['beckett_url'] = checklist_url
                        st.session_state['checklist_type'] = checklist_type
                        st.success(f"✅ Found {len(cards)} {checklist_type.lower()} from {source_name}!")
                        st.rerun()
                    else:
                        st.error(f"❌ No {checklist_type.lower()} found. Please check the URL and try again.")
                        
                        # Check if it's a server timeout issue
                        import sys
                        from io import StringIO
                        old_stdout = sys.stdout
                        sys.stdout = StringIO()
                        try:
                            # Try to fetch again to see the error
                            test_fetcher = CardChecklistFetcher(source='beckett')
                            test_fetcher.fetch_from_beckett_url(checklist_url, checklist_type=selected_type)
                        except:
                            pass
                        finally:
                            output = sys.stdout.getvalue()
                            sys.stdout = old_stdout
                        
                        if '504' in output or 'Gateway Timeout' in output or 'timeout' in output.lower():
                            st.error("**Server Issue Detected**")
                            st.warning(f"""
                            **The {source_name} server is timing out (504 Gateway Timeout).**
                            
                            This is a **server-side issue**, not a problem with the parser.
                            
                            **What to do:**
                            1. **Try Cardsmiths Breaks instead** - Use this URL:
                               `https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/`
                            2. Wait 5-10 minutes and try again
                            3. Check if the site is accessible in your browser
                            
                            The parser will automatically try Cardsmiths as a backup if Beckett fails.
                            """)
                        else:
                            st.warning("""
                            **Troubleshooting:**
                            - Make sure the URL is correct and accessible
                            - Try Cardsmiths Breaks as an alternative: https://cardsmithsbreaks.com/full-checklist/2025-26-topps-chrome-basketball-hobby/
                            - The page might have a different structure than expected
                            - Try a different checklist type (Insert Cards, Parallel Cards, etc.)
                            - You can also manually create a CSV file with your cards
                            """)
                        
                        # Alternative: Manual entry option
                        st.info("💡 **Alternative: Manual Entry**")
                        if st.button("📝 Enter Cards Manually", use_container_width=True):
                            st.session_state['manual_entry_mode'] = True
                            st.rerun()
                except Exception as e:
                    st.error(f"❌ Error fetching checklist: {str(e)}")
                    st.exception(e)
    
    # Step 3: Display cards and allow quantity input
    if 'beckett_cards' in st.session_state and st.session_state['beckett_cards']:
        st.markdown("---")
        st.subheader("Step 3: Enter Quantities for Each Card")
        
        cards = st.session_state['beckett_cards']
        st.info(f"Found {len(cards)} cards. **Enter the quantity you have for each card. Cards with quantity = 0 will NOT be listed.**")
        
        # Initialize quantities and prices in session state if not exists
        if 'card_quantities' not in st.session_state:
            st.session_state['card_quantities'] = {}
        if 'card_prices' not in st.session_state:
            st.session_state['card_prices'] = {}
        
        # Display cards in a table format with quantity and price inputs
        with st.form("quantity_form"):
            st.markdown("### Card Checklist with Quantities and Prices")
            st.caption("💡 **Tip:** If quantity > 1 and no price is set, price will default to $1.00")
            
            # Create columns for better layout
            col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 2, 2])
            
            with col1:
                st.markdown("**#**")
            with col2:
                st.markdown("**Player Name**")
            with col3:
                st.markdown("**Team**")
            with col4:
                st.markdown("**Quantity**")
            with col5:
                st.markdown("**Price ($)**")
            
            # Display all cards (already filtered by type from fetch)
            checklist_type_display = st.session_state.get('checklist_type', 'cards')
            
            for i, card in enumerate(cards):
                card_key = f"{card.get('number', i)}_{card.get('name', '')}"
                default_qty = st.session_state['card_quantities'].get(card_key, 0)
                
                if checklist_type_display == "Insert Cards":
                    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])
                    with col1:
                        st.write(card.get('number', ''))
                    with col2:
                        st.write(card.get('name', 'Unknown'))
                    with col3:
                        st.write(card.get('team', card.get('insert_name', '')))
                    with col4:
                        qty = st.number_input(
                            "Qty",
                            min_value=0,
                            value=int(default_qty),
                            key=f"qty_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed"
                        )
                        st.session_state['card_quantities'][card_key] = qty
                    with col5:
                        default_price = st.session_state['card_prices'].get(card_key, None)
                        price = st.number_input(
                            "Price",
                            min_value=0.0,
                            value=float(default_price) if default_price is not None else 0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"price_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed",
                            placeholder="Auto"
                        )
                        st.session_state['card_prices'][card_key] = price if price and price > 0 else None
                elif checklist_type_display == "Parallel Cards":
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 2])
                    with col1:
                        st.write(card.get('number', i+1))
                    with col2:
                        st.write(card.get('name', 'Unknown'))
                    with col3:
                        st.write(card.get('team', ''))
                    with col4:
                        parallel_info = card.get('parallel_type', '')
                        if card.get('numbering'):
                            parallel_info += f" /{card.get('numbering')}"
                        st.write(parallel_info)
                    with col5:
                        qty = st.number_input(
                            "Qty",
                            min_value=0,
                            value=int(default_qty),
                            key=f"qty_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed"
                        )
                        st.session_state['card_quantities'][card_key] = qty
                    with col6:
                        default_price = st.session_state['card_prices'].get(card_key, None)
                        price = st.number_input(
                            "Price",
                            min_value=0.0,
                            value=float(default_price) if default_price is not None else 0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"price_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed",
                            placeholder="Auto"
                        )
                        st.session_state['card_prices'][card_key] = price if price and price > 0 else None
                elif checklist_type_display == "Numbered Cards / Autographs":
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 2, 2, 2, 2])
                    with col1:
                        st.write(card.get('number', ''))
                    with col2:
                        st.write(card.get('name', 'Unknown'))
                    with col3:
                        st.write(card.get('team', ''))
                    with col4:
                        card_type = card.get('card_type', '')
                        if card.get('numbering'):
                            card_type = f"/{card.get('numbering')}"
                        st.write(card_type)
                    with col5:
                        qty = st.number_input(
                            "Qty",
                            min_value=0,
                            value=int(default_qty),
                            key=f"qty_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed"
                        )
                        st.session_state['card_quantities'][card_key] = qty
                    with col6:
                        default_price = st.session_state['card_prices'].get(card_key, None)
                        price = st.number_input(
                            "Price",
                            min_value=0.0,
                            value=float(default_price) if default_price is not None else 0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"price_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed",
                            placeholder="Auto"
                        )
                        st.session_state['card_prices'][card_key] = price if price and price > 0 else None
                else:  # Base Cards
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 2, 2])
                    with col1:
                        st.write(card.get('number', i+1))
                    with col2:
                        st.write(card.get('name', 'Unknown'))
                    with col3:
                        st.write(card.get('team', ''))
                    with col4:
                        qty = st.number_input(
                            "Qty",
                            min_value=0,
                            value=int(default_qty),
                            key=f"qty_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed"
                        )
                        st.session_state['card_quantities'][card_key] = qty
                    with col5:
                        default_price = st.session_state['card_prices'].get(card_key, None)
                        price = st.number_input(
                            "Price",
                            min_value=0.0,
                            value=float(default_price) if default_price is not None else 0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"price_{card.get('number', i)}_{card.get('name', '')}",
                            label_visibility="collapsed",
                            placeholder="Auto"
                        )
                        st.session_state['card_prices'][card_key] = price if price and price > 0 else None
            
            submitted = st.form_submit_button("💾 Save Quantities", type="primary", use_container_width=True)
            
            if submitted:
                st.success("✅ Quantities saved!")
                st.rerun()
        
        # Step 4: Review and create listing
        st.markdown("---")
        st.subheader("Step 4: Review and Create Listing")
        
        # Count cards with quantity > 0 (ONLY these will be listed)
        # Apply pricing logic: if quantity > 1 and no price set, default to $1
        cards_with_qty = []
        for i, card in enumerate(cards):
            card_key = f"{card.get('number', i)}_{card.get('name', '')}"
            qty = st.session_state['card_quantities'].get(card_key, 0)
            if qty > 0:  # Only include cards with quantity > 0
                card_copy = card.copy()
                card_copy['quantity'] = qty
                
                # Get price from session state
                price = st.session_state['card_prices'].get(card_key, None)
                
                # Pricing logic: if quantity > 1 and no price set, default to $1
                if price is None or price == 0:
                    if qty > 1:
                        price = 1.00
                    else:
                        price = None  # Will use base_price from settings
                
                card_copy['price'] = price
                cards_with_qty.append(card_copy)
        
        if cards_with_qty:
            st.success(f"✅ {len(cards_with_qty)} cards will be listed (cards with quantity = 0 are ignored)")
            
            # Show preview of cards that will be listed
            with st.expander("📋 Preview: Cards to be Listed", expanded=False):
                preview_data = []
                for card in cards_with_qty:
                    price_display = f"${card.get('price', 0):.2f}" if card.get('price') else "Base Price"
                    preview_data.append({
                        "#": card.get('number', ''),
                        "Player": card.get('name', 'Unknown'),
                        "Team": card.get('team', card.get('insert_name', '')),
                        "Quantity": card.get('quantity', 0),
                        "Price": price_display
                    })
                import pandas as pd
                df = pd.DataFrame(preview_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Listing settings
            with st.expander("⚙️ Listing Settings", expanded=True):
                # Use the title from Step 1, but allow editing
                final_title = st.text_input(
                    "Listing Title",
                    value=st.session_state.get('listing_title', f"Card Set - {len(cards_with_qty)} Cards"),
                    help="Title for your eBay listing (1-80 characters)",
                    max_chars=80
                )
                
                # Validate title length
                if final_title and len(final_title) > 80:
                    st.warning(f"⚠️ Title is {len(final_title)} characters. It will be truncated to 80 characters.")
                    final_title = final_title[:80]
                elif not final_title or len(final_title.strip()) < 1:
                    st.error("❌ Please enter a listing title (1-80 characters)")
                    final_title = f"Card Set - {len(cards_with_qty)} Cards"
                
                # Use description from Step 1, but allow editing
                final_description = st.text_area(
                    "Listing Description",
                    value=st.session_state.get('listing_description', f"Variation listing with {len(cards_with_qty)} cards from the set. Each card listed separately as a variation."),
                    help="Description for your eBay listing"
                )
                
                base_price = st.number_input(
                    "Base Price per Card ($)",
                    min_value=0.01,
                    value=1.00,
                    step=0.01,
                    help="Default price for cards (you can set individual prices later)"
                )
                
                condition = st.selectbox(
                    "Card Condition",
                    ["New", "Like New", "Very Good", "Good", "Acceptable"],
                    index=1  # Default to "Like New"
                )
                
                publish_immediately = st.checkbox(
                    "Publish Listing Immediately",
                    value=False,  # Default to draft so user can add pictures
                    help="If unchecked, the listing will be created as a draft. You can add pictures and publish it later from eBay Seller Hub."
                )
                st.info("💡 **Tip:** Create as draft first to add pictures, then publish from eBay Seller Hub.")
            
            if st.button("🚀 Create eBay Listing", type="primary", use_container_width=True):
                with st.spinner("Creating listing on eBay..."):
                    try:
                        from ebay_bot import eBayCardBot
                        bot = eBayCardBot()
                        
                        # Prepare cards for listing with prices
                        listing_cards = []
                        for card in cards_with_qty:
                            card_price = card.get('price')
                            # If no price set, use base_price
                            if card_price is None or card_price == 0:
                                card_price = base_price
                            
                            listing_cards.append({
                                'name': card.get('name', ''),
                                'number': card.get('number', ''),
                                'quantity': card.get('quantity', 1),
                                'team': card.get('team', ''),
                                'price': card_price,  # Per-card price
                                'set_name': st.session_state.get('beckett_url', 'Card Set')
                            })
                        
                        # Build pricing dictionary for per-card pricing
                        pricing_dict = {}
                        for card in listing_cards:
                            card_price = card.get('price', base_price)
                            card_name = card.get('name', '')
                            card_number = card.get('number', '')
                            if card_name:
                                pricing_dict[card_name] = float(card_price)
                            if card_number:
                                pricing_dict[card_number] = float(card_price)
                        
                        # Use pricing dict if we have per-card prices, otherwise use base_price
                        final_price = pricing_dict if pricing_dict else base_price
                        
                        # IMPORTANT: Pass cards directly to create_variation_listing
                        # instead of using list_cards_from_set which tries to fetch cards
                        from ebay_listing import eBayListingManager
                        listing_manager = eBayListingManager()
                        category_id = listing_manager.get_category_id("Trading Cards")
                        
                        st.info(f"Creating listing with {len(listing_cards)} cards...")
                        
                        # Ensure title is valid before creating listing
                        if not final_title or len(final_title.strip()) < 1:
                            final_title = f"Card Set - {len(listing_cards)} Cards"
                        elif len(final_title) > 80:
                            final_title = final_title[:80].strip()
                            if not final_title:  # If truncation left it empty
                                final_title = f"Card Set - {len(listing_cards)} Cards"
                        
                        # Ensure description is properly formatted
                        # CRITICAL: Preserve the full description - don't let it get truncated
                        if final_description and final_description.strip():
                            # Use the description as provided (even if it seems short, it might have been edited)
                            listing_description = final_description.strip()
                            print(f"[DEBUG] Using description from UI (length: {len(listing_description)})")
                            
                            # If it's too short, append the Topps Chrome text
                            if len(listing_description.strip()) < 50:
                                if "Topps Chrome" in final_title or "Chrome" in final_title:
                                    listing_description = f"""{listing_description}

If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                                else:
                                    listing_description = f"""{listing_description}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                        else:
                            # Use default based on title
                            if "Topps Chrome" in final_title or "Chrome" in final_title:
                                listing_description = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                            else:
                                listing_description = f"Variation listing with {len(listing_cards)} cards. Each card listed separately as a variation."
                        
                        print(f"[DEBUG] Final description length before passing to listing manager: {len(listing_description)}")
                        print(f"[DEBUG] Description preview: {listing_description[:100]}...")
                        
                        # Create listing - ONLY cards with quantity > 0
                        result = listing_manager.create_variation_listing(
                            cards=listing_cards,  # Pass cards directly
                            title=final_title.strip(),  # Ensure it's trimmed
                            description=listing_description,  # Use properly formatted description
                            category_id=category_id,
                            price=final_price,  # Can be float or dict of per-card prices
                            quantity=1,  # Per-card quantity is in the card data
                            condition=condition,
                            publish=publish_immediately
                        )
                        
                        if result.get('success'):
                            if publish_immediately:
                                st.success("🎉 Listing created and published successfully!")
                                st.balloons()
                            else:
                                st.success("🎉 Listing created as draft successfully!")
                                st.info("💡 **Next Steps:**\n1. Go to eBay Seller Hub\n2. Find your draft listing\n3. Add pictures\n4. Publish when ready")
                            
                            if result.get('offerId'):
                                st.info(f"Offer ID: {result['offerId']}")
                            if result.get('listingId'):
                                listing_id = result['listingId']
                                st.info(f"Listing ID: {listing_id}")
                                listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
                                st.markdown(f"🔗 [View Listing on Sandbox]({listing_url})")
                            elif result.get('listing_id'):
                                listing_id = result['listing_id']
                                st.info(f"Listing ID: {listing_id}")
                                listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
                                st.markdown(f"🔗 [View Listing on Sandbox]({listing_url})")
                            if result.get('groupKey'):
                                st.info(f"Group Key: {result['groupKey']}")
                            if result.get('listing_url'):
                                st.markdown(f"[View Listing on eBay]({result['listing_url']})")
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            st.error(f"❌ Failed to create listing: {error_msg}")
                            
                            # Show enhanced debug info for Error 25007
                            if '25007' in str(error_msg) or (result.get('debug_info') and result.get('debug_info').get('offers_checked')):
                                with st.expander("🔍 Detailed Debugging - Error 25007", expanded=True):
                                    debug_info = result.get('debug_info', {})
                                    
                                    # Show policies checked
                                    policies_checked = debug_info.get('policies_checked', [])
                                    if policies_checked:
                                        st.subheader("📋 Policies Checked")
                                        for policy in policies_checked:
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.write(f"**Policy ID:** {policy.get('policy_id')}")
                                                st.write(f"**Name:** {policy.get('policy_name')}")
                                            with col2:
                                                st.write(f"**Has Shipping Options:** {policy.get('has_shipping_options')}")
                                                st.write(f"**Options Count:** {policy.get('shipping_options_count')}")
                                            
                                            # Show detailed service information
                                            services_detail = policy.get('services_detail', [])
                                            if services_detail:
                                                st.write("**Services Detail:**")
                                                for svc in services_detail:
                                                    svc_text = f"- {svc.get('code')} ({svc.get('carrier')})"
                                                    if svc.get('cost') != 'N/A':
                                                        svc_text += f" - ${svc.get('cost')}"
                                                    buyer_pays = svc.get('buyer_pays')
                                                    if buyer_pays is not None:
                                                        svc_text += f" - Buyer Pays: {buyer_pays}"
                                                        if buyer_pays is False:
                                                            st.warning(f"{svc_text} ⚠️ (SELLER PAYS - This may be the issue!)")
                                                        else:
                                                            st.write(svc_text)
                                                    else:
                                                        st.write(svc_text)
                                            else:
                                                services = policy.get('services', [])
                                                if services:
                                                    st.write(f"**Services:** {', '.join(services)}")
                                            
                                            # Show buyer responsible issues
                                            buyer_issues = policy.get('buyer_responsible_issues', [])
                                            if buyer_issues:
                                                st.warning(f"⚠️ {len(buyer_issues)} service(s) have buyerResponsibleForShipping=False")
                                                for issue in buyer_issues:
                                                    st.write(f"  - {issue}")
                                            
                                            warning = policy.get('warning')
                                            if warning:
                                                st.warning(f"⚠️ {warning}")
                                            
                                            st.divider()
                                    
                                    # Show offers checked
                                    offers_checked = debug_info.get('offers_checked', [])
                                    if offers_checked:
                                        st.subheader("📦 Offers Checked")
                                        for offer in offers_checked:
                                            st.write(f"**SKU:** {offer.get('sku', 'N/A')}")
                                            st.write(f"**Offer ID:** {offer.get('offer_id', 'N/A')}")
                                            st.write(f"**Policy ID in Offer:** {offer.get('policy_id', 'NOT SET')}")
                                            st.write(f"**Policy Name:** {offer.get('policy_name', 'N/A')}")
                                            
                                            policy_valid = offer.get('policy_valid', False)
                                            if policy_valid:
                                                st.success(f"✅ Policy Valid: {policy_valid}")
                                            else:
                                                st.error(f"❌ Policy Valid: {policy_valid}")
                                            
                                            st.write(f"**Shipping Options:** {offer.get('shipping_options_count', 0)}")
                                            services = offer.get('services', [])
                                            if services:
                                                st.write(f"**Services:** {', '.join(services)}")
                                            
                                            issues = offer.get('issues', [])
                                            if issues:
                                                st.warning("**Issues Found:**")
                                                for issue in issues:
                                                    st.write(f"  - {issue}")
                                            st.divider()
                                    
                                    # Show issues found
                                    issues_found = debug_info.get('issues_found', [])
                                    if issues_found:
                                        st.subheader("⚠️ Issues Found")
                                        for issue in issues_found:
                                            st.warning(f"- {issue}")
                                    
                                    # Show raw response if available
                                    if result.get('raw_response'):
                                        with st.expander("Raw API Response", expanded=False):
                                            st.code(result.get('raw_response'), language='json')
                            
                            # Show basic debug info for other errors
                            elif result.get('debug_info'):
                                with st.expander("🔍 Debug Information (Click to see details)", expanded=False):
                                    st.json(result.get('debug_info', {}))
                            
                            # Check for 401/token errors
                            if '401' in str(error_msg) or 'Invalid access token' in str(error_msg) or 'Unauthorized' in str(error_msg):
                                st.error("🔴 **Your access token is invalid or expired!**")
                                st.warning("""
                                **Token Authentication Failed**
                                
                                Your token has expired or is invalid. Please refresh it:
                                
                                1. **Go to Step 2 (Login)**
                                2. **Click "🔄 Refresh Token"** button
                                3. **Or get a new token** from eBay Developer Console
                                4. **Then try creating the listing again**
                                """)
                            
                            # Check for 403/access denied errors
                            if '403' in str(error_msg) or 'Access denied' in str(error_msg) or '1100' in str(error_msg):
                                st.error("🔴 **Access Denied - Token Missing Required Permissions!**")
                                st.warning("""
                                **Permission Error (Error ID: 1100)**
                                
                                Your token doesn't have permission to use the Inventory API. This usually means:
                                
                                1. **Token is missing required scopes** - You need `sell.inventory` scope
                                2. **Token is for wrong environment** - Make sure Sandbox token is for Sandbox, Production for Production
                                3. **Manual token doesn't have permissions** - Manual tokens from Developer Console may not have all scopes
                                
                                **Solutions:**
                                
                                **Option 1: Use OAuth Login (Recommended)**
                                1. Go to **Step 2 (Login)**
                                2. Click **"Login with OAuth"** button
                                3. This will request all required permissions automatically
                                4. Then try creating the listing again
                                
                                **Option 2: Get Token with Right Scopes**
                                1. Go to eBay Developer Console
                                2. Make sure you select scopes: `sell.inventory`, `sell.account`, `sell.fulfillment`
                                3. Get a new User Token
                                4. Paste it in Step 2 (Manual Entry)
                                5. Then try again
                                """)
                            
                            # Show detailed errors if available
                            if result.get('errors'):
                                with st.expander("🔍 Detailed Error Information", expanded=True):
                                    for i, err in enumerate(result.get('errors', [])[:10], 1):
                                        st.text(f"{i}. {err}")
                                    if len(result.get('errors', [])) > 10:
                                        st.text(f"... and {len(result.get('errors', [])) - 10} more errors")
                            
                    except Exception as e:
                        st.error(f"❌ Error creating listing: {str(e)}")
                        st.exception(e)
        else:
            st.warning("⚠️ No cards selected. Please enter quantities for at least one card.")

if __name__ == "__main__":
    main()
