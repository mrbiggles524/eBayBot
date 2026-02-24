"""Simple web UI for eBay Bot setup using Streamlit."""
import streamlit as st
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    st.set_page_config(
        page_title="eBay Card Listing Bot - Setup",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for colorful, modern UI with better contrast
    st.markdown("""
    <style>
    /* Main background - light gradient for better contrast */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Main content area - white background for readability */
    .main .block-container {
        background: #ffffff;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }
    
    /* Header styling - dark text for contrast */
    h1 {
        color: #2c3e50 !important;
        text-shadow: none;
        font-size: 2.5rem !important;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #34495e !important;
    }
    
    /* Sidebar styling - darker for contrast */
    .css-1d391kg {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    .css-1d391kg .css-1lcbmhc {
        color: #ffffff !important;
    }
    
    /* Card-like containers */
    .stContainer {
        background: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 10px 0;
        border: 1px solid #e0e0e0;
    }
    
    /* Success messages - bright green with dark text */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
        border-radius: 10px;
        color: #155724 !important;
    }
    
    /* Error messages - bright red with dark text */
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 5px solid #dc3545;
        border-radius: 10px;
        color: #721c24 !important;
    }
    
    /* Warning messages - bright yellow with dark text */
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 5px solid #ffc107;
        border-radius: 10px;
        color: #856404 !important;
    }
    
    /* Info messages - bright blue with dark text */
    .stInfo {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 5px solid #17a2b8;
        border-radius: 10px;
        color: #0c5460 !important;
    }
    
    /* Buttons - vibrant but readable */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Input fields - clear borders */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #d0d0d0;
        transition: all 0.3s ease;
        background: #ffffff;
        color: #2c3e50;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        background: #ffffff;
    }
    
    /* Text areas */
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #d0d0d0;
        background: #ffffff;
        color: #2c3e50;
    }
    
    /* Select boxes */
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #d0d0d0;
        background: #ffffff;
        color: #2c3e50;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    
    /* Metrics - colorful but readable */
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* All text should be dark for readability */
    p, li, span, div {
        color: #2c3e50 !important;
    }
    
    /* Code blocks */
    code {
        background: #f4f4f4;
        color: #e83e8c;
        padding: 2px 6px;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📦 eBay Card Listing Bot - Setup Wizard")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);'>
        <h3 style='color: #ffffff; margin: 0; font-weight: 700;'>Welcome! 🎉</h3>
        <p style='color: #ffffff; margin: 10px 0 0 0; font-size: 1.1rem;'>This wizard will help you set up your eBay bot in just a few steps.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("📋 Setup Steps")
    st.sidebar.markdown("---")
    
    steps = [
        ("1. API Credentials", "Enter your eBay API keys"),
        ("2. Login", "Authenticate with eBay"),
        ("3. Auto-Configure", "Fetch your account settings"),
        ("4. Verify", "Confirm everything is ready"),
        ("5. Create Listings", "List cards from Beckett checklist"),
        ("6. Publish Drafts", "Publish existing draft listings automatically")
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
    
    # Step 6: Publish Drafts
    elif current_step == "6. Publish Drafts":
        step6_publish_drafts()

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
                
                # Show authorization URL
                auth_url = oauth.get_authorization_url()
                
                st.info("""
                **Follow these steps:**
                1. A browser window should open automatically
                2. If not, click the link below to open it manually
                3. Sign in with your eBay account
                4. Authorize the application
                5. You'll be redirected back automatically
                """)
                
                st.markdown(f"[🔗 Click here to open authorization page]({auth_url})")
                
                # Start login process
                status_placeholder = st.empty()
                with status_placeholder.container():
                    with st.spinner("Waiting for authorization... (This may take up to 5 minutes)"):
                        try:
                            result = oauth.login(open_browser=True)
                        except KeyboardInterrupt:
                            result = {
                                "success": False,
                                "error": "Login cancelled by user."
                            }
                        except Exception as e:
                            result = {
                                "success": False,
                                "error": f"Unexpected error: {str(e)}"
                            }
                    
                    if result.get('success'):
                        st.success("✅ Login successful!")
                        st.balloons()
                        st.info("Token saved. You can now proceed to Step 3.")
                        # Force refresh to update login status
                        st.rerun()
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        error_str = str(error_msg)
                        
                        # Check for invalid_request error
                        if 'invalid_request' in error_str.lower():
                            st.error("❌ **Invalid OAuth Request - Redirect URI Not Registered**")
                            st.warning(f"""
                            **OAuth Configuration Error**
                            
                            The OAuth request was rejected because the redirect URI is not registered.
                            
                            **Current redirect URI:** `{oauth.redirect_uri}`
                            
                            **How to Fix:**
                            
                            1. **Go to eBay Developer Console**
                               - Visit: https://developer.ebay.com/
                               - Sign in with your eBay account
                            
                            2. **Navigate to Your App**
                               - Click "Application Keys" in left menu
                               - Find your **Sandbox** keyset (with "SBX" in App ID)
                            
                            3. **Add Redirect URI**
                               - Look for "OAuth Redirect URIs" or "Redirect URIs" section
                               - Click "Add" or "Edit"
                               - Add EXACTLY: `http://localhost:8080/callback`
                               - **Important:** Use `http://` (NOT `https://`), use `localhost` (NOT `127.0.0.1`)
                               - Click "Save"
                            
                            4. **Try OAuth Login Again**
                               - Come back here and click "Login with OAuth" again
                            
                            **Alternative (Quick Fix):**
                            - Use the **"Manual Token Entry"** tab below
                            - This works without OAuth redirect URI setup
                            - However, manual tokens may not have all required scopes
                            
                            📖 **See `OAUTH_REDIRECT_SETUP.md` for detailed instructions**
                            """)
                        # Check for timeout
                        elif 'timeout' in error_str.lower() or 'No authorization code' in error_str:
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
        
        # Check environment and warn about disabled keysets
        try:
            from config import Config
            config = Config()
            if config.EBAY_ENVIRONMENT == "production":
                st.info("""
                ℹ️ **Production Environment Detected**
                
                Make sure your Production keyset is enabled in eBay Developer Console.
                If it's disabled, you'll need to set up marketplace deletion notifications first.
                
                See `PRODUCTION_KEYSET_SETUP.md` for instructions.
                """)
        except:
            pass
        
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
                        from ebay_api_client import eBayAPIClient
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
                        
                        # Verify token has required scopes
                        with st.spinner("Verifying token permissions..."):
                            api_client = eBayAPIClient()
                            scope_check = api_client.verify_token_scopes()
                            
                            if scope_check.get('has_inventory_scope'):
                                st.success("✅ Token saved and verified! Has all required permissions.")
                                st.balloons()
                                st.info("Token saved. You can now proceed to Step 3.")
                            elif scope_check.get('has_inventory_scope') == False:
                                st.warning("⚠️ **Token saved, but missing required permissions!**")
                                st.error(f"**Issue:** {scope_check.get('error', 'Token missing sell.inventory scope')}")
                                st.warning("""
                                **This token won't work for creating listings.**
                                
                                **Solutions:**
                                1. **Use OAuth Login instead** (recommended) - it automatically gets all required scopes
                                   - First, register redirect URI (see `OAUTH_REDIRECT_SETUP.md`)
                                   - Then use OAuth Login tab
                                2. **Get a new token** from eBay Developer Console
                                   - Make sure to select `sell.inventory` scope when generating
                                
                                The token is saved, but you'll get "Access denied" errors when creating listings.
                                """)
                            else:
                                st.success("✅ Token saved!")
                                st.info("⚠️ Could not verify token permissions. You may need to test by creating a listing.")
                                st.info("Token saved. You can now proceed to Step 3.")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error saving token: {str(e)}")
                        st.exception(e)
    
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
    st.header("Step 3: Configure Policies & Locations")
    
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
    
    # Test token validity
    st.markdown("---")
    token_valid = None
    try:
        from ebay_setup import eBayAutoSetup
        setup = eBayAutoSetup()
        user_info = setup.get_current_user()
        if user_info.get('success'):
            token_valid = True
        else:
            token_valid = False
            if '401' in str(user_info.get('error', '')) or 'Invalid access token' in str(user_info.get('error', '')):
                st.error("🔴 **Warning: Your token appears to be invalid or expired!**")
                st.warning("""
                **The token you're using is not working.**
                
                **What to do:**
                1. Go back to **Step 2: Login**
                2. Get a new User Token from eBay Developer Console
                3. Or use the **Manual Entry** tab below to skip token validation
                """)
    except Exception as e:
        if '401' in str(e) or 'Invalid access token' in str(e):
            token_valid = False
            st.error("🔴 **Warning: Your token appears to be invalid or expired!**")
    
    st.markdown("---")
    
    # Create tabs for Auto-Configure and Manual Entry
    tab1, tab2 = st.tabs(["🚀 Auto-Configure", "✏️ Manual Entry"])
    
    with tab1:
        st.info("""
        This will automatically fetch all required settings from your eBay account:
        - Fulfillment policies
        - Payment policies
        - Return policies
        - Merchant locations
        
        **Click the button below to fetch and configure everything automatically.**
        """)
        
        user_id = st.text_input(
            "eBay User ID (Optional)",
            help="Leave empty to use your current logged-in user, or enter a different eBay username",
            placeholder="your_ebay_username",
            value="",  # Empty by default - will use logged-in user
            key="auto_user_id"
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
                
                progress_bar.progress(30)
                status_text.info("🔄 Fetching policies and locations...")
                progress_bar.progress(60)
                
                progress_bar.progress(100)
                
                # Check if setup succeeded or if policies are already configured
                if result.get('success') or result.get('setup_info', {}).get('policies'):
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
                        if policies.get('errors', {}).get('fulfillment'):
                            error_msg = policies['errors']['fulfillment']
                            st.caption(f"⚠ {error_msg}")
                            if '401' in error_msg or 'Invalid access token' in error_msg:
                                st.error("🔴 **Your token is invalid or expired!**")
                        st.write(f"- Payment: {payment_count} found")
                        if policies.get('errors', {}).get('payment'):
                            error_msg = policies['errors']['payment']
                            st.caption(f"⚠ {error_msg}")
                            if '401' in error_msg or 'Invalid access token' in error_msg:
                                st.error("🔴 **Your token is invalid or expired!**")
                        st.write(f"- Return: {return_count} found")
                        if policies.get('errors', {}).get('return'):
                            error_msg = policies['errors']['return']
                            st.caption(f"⚠ {error_msg}")
                            if '401' in error_msg or 'Invalid access token' in error_msg:
                                st.error("🔴 **Your token is invalid or expired!**")
                    
                    with col_b:
                        st.write("**Locations:**")
                        location_count = locations.get('count', 0)
                        st.write(f"- Merchant Locations: {location_count} found")
                        if locations.get('error'):
                            error_msg = locations['error']
                            st.caption(f"⚠ {error_msg}")
                            if '401' in error_msg or 'Invalid access token' in error_msg:
                                st.error("🔴 **Your token is invalid or expired!**")
                    
                    # Check if all errors are 401
                    all_401 = True
                    for error_type in ['fulfillment', 'payment', 'return']:
                        error = policies.get('errors', {}).get(error_type, '')
                        if error and '401' not in error and 'Invalid access token' not in error:
                            all_401 = False
                    if locations.get('error') and '401' not in locations['error'] and 'Invalid access token' not in locations['error']:
                        all_401 = False
                    
                    if all_401 and (policies.get('errors') or locations.get('error')):
                        st.error("🔴 **Invalid Access Token Detected**")
                        st.warning("""
                        **Your eBay access token is invalid or expired.**
                        
                        **What to do:**
                        1. Go back to **Step 2: Login**
                        2. Get a new User Token from eBay Developer Console:
                           - Go to https://developer.ebay.com/
                           - Navigate to your keyset → **User Tokens**
                           - Generate a new User Token
                           - Copy and paste it in Step 2
                        3. Or use the **Manual Entry** tab below to enter policy IDs directly
                        """)
                    
                    # Show recommendations
                    st.subheader("✅ Configuration Applied:")
                    recommendations = setup_info.get('recommendations', [])
                    if recommendations:
                        for rec in recommendations:
                            if not rec.startswith('#'):
                                st.code(rec, language=None)
                    else:
                        st.warning("⚠ No policies or locations found.")
                        st.info("""
                        **What to do:**
                        
                        1. **If you're using Sandbox**: Policies may not exist yet. You can:
                           - Create policies manually in eBay Seller Hub (Sandbox)
                           - Or manually enter policy IDs in your `.env` file
                        
                        2. **If you're using Production**: 
                           - Go to [eBay Seller Hub](https://www.ebay.com/sh/landing)
                           - Navigate to **Account → Business Policies**
                           - Create at least one Fulfillment, Payment, and Return policy
                           - Then run Auto-Configure again
                        
                        3. **For Merchant Locations**:
                           - Go to **Account → Shipping Preferences**
                           - Set up your default shipping location
                           - Or manually enter `MERCHANT_LOCATION_KEY` in your `.env` file
                        """)
                    
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
                    
                    # Check for 401 errors
                    if '401' in str(error_msg) or 'Invalid access token' in str(error_msg) or 'Unauthorized' in str(error_msg):
                        st.error("🔴 **Your access token is invalid or expired!**")
                        st.warning("""
                        **Token Authentication Failed**
                        
                        Your token is not valid. This could mean:
                        - The token has expired
                        - The token doesn't have the right permissions
                        - The token is for a different environment (Sandbox vs Production)
                        
                        **Solutions:**
                        1. **Get a new token**: Go to Step 2 and get a fresh User Token from eBay Developer Console
                        2. **Use Manual Entry**: Switch to the "Manual Entry" tab below and enter policy IDs directly
                        3. **Check environment**: Make sure your token matches your environment (Sandbox/Production)
                        """)
                    # Provide helpful guidance for other errors
                    elif 'policies' in str(error_msg).lower() or 'policy' in str(error_msg).lower():
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
            if st.button("🔄 Refresh Status", use_container_width=True, key="refresh_auto"):
                st.rerun()
    
    with tab2:
        st.info("""
        **Manually enter your policy IDs and location key.**
        
        If auto-configure didn't work, you can enter these values directly.
        You can find them in your eBay Seller Hub or by creating them first.
        """)
        
        # Show example from user's policies
        st.expander("📋 Quick Reference: Your Visible Policy IDs", expanded=False)
        with st.expander("📋 Quick Reference: Your Visible Policy IDs", expanded=False):
            st.write("**From your policy list, I can see:**")
            st.code("""
Return Policies:
  - No Return Accepted: 4b040f2c108e000
  - 30 days money back: 257398528019

Payment Policies:
  - Managed Payments (click to see full ID)
  - Payments managed by eBay (click to see full ID)

Shipping/Fulfillment Policies:
  - International Shipping No Exclusions (click to see full ID)
  - PWE eBay Shipping Envelope ONLY Cards Under $20 (click to see full ID)
  - FREE SHIPPING UNDER $20 (click to see full ID)
            """)
            st.warning("💡 **Tip**: Click on each policy in eBay Seller Hub to see the full Policy ID in the URL or details page.")
        
        # Load current values
        try:
            from config import Config
            config = Config()
            current_fulfillment = config.FULFILLMENT_POLICY_ID
            current_payment = config.PAYMENT_POLICY_ID
            current_return = config.RETURN_POLICY_ID
            current_location = config.MERCHANT_LOCATION_KEY
        except:
            current_fulfillment = ""
            current_payment = ""
            current_return = ""
            current_location = ""
        
        with st.form("manual_policy_form"):
            st.subheader("Enter Policy IDs")
            
            st.markdown("**💡 How to find Policy IDs:**")
            st.markdown("""
            1. In eBay Seller Hub → **Account → Business Policies**
            2. Click on the policy name to open it
            3. The Policy ID appears in:
               - The URL (look for a long alphanumeric string)
               - The policy details page
               - Sometimes at the end of the policy name
            """)
            
            st.markdown("**Note:** In eBay, 'Fulfillment Policy' = 'Shipping Policy'. Look for shipping policies in your list.")
            st.info("💡 **Tip:** When you click a shipping policy in eBay, the URL will look like: `.../ship/edit/254009535019` - the number at the end is the Policy ID!")
            fulfillment_id = st.text_input(
                "Fulfillment Policy ID (This is a SHIPPING policy)",
                value=current_fulfillment,
                help="Click on a SHIPPING policy in eBay Seller Hub. The ID is the number in the URL (e.g., from '.../ship/edit/254009535019' the ID is '254009535019')",
                placeholder="e.g., 254009535019"
            )
            
            payment_id = st.text_input(
                "Payment Policy ID",
                value=current_payment,
                help="Click on a payment policy (like 'Managed Payments') to get the ID",
                placeholder="e.g., 1234567890"
            )
            
            return_id = st.text_input(
                "Return Policy ID",
                value=current_return,
                help="From your list: '4b040f2c108e000' or '257398528019' - click the policy to confirm the full ID",
                placeholder="e.g., 4b040f2c108e000 or 257398528019"
            )
            
            location_key = st.text_input(
                "Merchant Location Key (Optional - can leave blank for now)",
                value=current_location,
                help="Your eBay merchant location key. You can set this up later if needed.",
                placeholder="Leave blank if not sure"
            )
            
            submitted = st.form_submit_button("💾 Save Configuration", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    import os
                    import re
                    from dotenv import load_dotenv
                    
                    # Helper function to extract ID from name+ID combo or URL
                    def extract_policy_id(value):
                        """Extract policy ID from text that might contain name + ID or URL."""
                        if not value:
                            return ''
                        value = value.strip()
                        
                        # First, try to extract from URL pattern (e.g., .../ship/edit/254009535019)
                        url_patterns = [
                            r'/(?:ship|payment|return)/edit/([0-9a-f]{10,16})',  # URL with /edit/ID
                            r'/policies/(?:fulfillment|payment|return)/([0-9a-f]{10,16})',  # Alternative URL format
                            r'[?&]id=([0-9a-f]{10,16})',  # Query parameter
                        ]
                        for pattern in url_patterns:
                            match = re.search(pattern, value, re.IGNORECASE)
                            if match:
                                return match.group(1)
                        
                        # Look for alphanumeric ID patterns (typically 10-16 chars)
                        # Pattern: long alphanumeric string (policy IDs can be numeric or hex)
                        id_pattern = r'([0-9a-f]{10,16})'
                        matches = re.findall(id_pattern, value, re.IGNORECASE)
                        if matches:
                            # Return the longest match (most likely the ID)
                            return max(matches, key=len)
                        # If no pattern found, return as-is (might be valid)
                        return value
                    
                    # Check if user entered policy names instead of IDs
                    warnings = []
                    
                    # Check fulfillment (should be alphanumeric, not a long name)
                    if fulfillment_id and len(fulfillment_id) > 30 and ' ' in fulfillment_id:
                        warnings.append("⚠️ Fulfillment Policy looks like a NAME, not an ID. Click the policy in eBay to get the ID from the URL.")
                    fulfillment_id_clean = extract_policy_id(fulfillment_id)
                    
                    # Check payment (should be alphanumeric, not a long name)
                    if payment_id and len(payment_id) > 30 and ' ' in payment_id:
                        warnings.append("⚠️ Payment Policy looks like a NAME, not an ID. Click the policy in eBay to get the ID from the URL.")
                    payment_id_clean = extract_policy_id(payment_id)
                    
                    # Check return (might have name + ID)
                    return_id_clean = extract_policy_id(return_id)
                    if return_id and return_id != return_id_clean:
                        st.info(f"ℹ️ Extracted Return Policy ID: `{return_id_clean}` (from: '{return_id}')")
                    
                    # Show warnings
                    if warnings:
                        for warning in warnings:
                            st.warning(warning)
                        st.error("❌ Please enter Policy IDs (alphanumeric strings), not policy names!")
                        st.info("""
                        **How to get the actual Policy ID:**
                        1. In eBay Seller Hub, click on the policy name
                        2. Look at the URL - it will be like: `.../policies/fulfillment/4b040f2c108e000`
                        3. Copy ONLY the ID part (the alphanumeric string at the end)
                        4. Paste just that ID into the form
                        """)
                        # Don't save if they entered names
                        if any(len(id) > 30 and ' ' in id for id in [fulfillment_id, payment_id] if id):
                            return
                    
                    # Load existing .env
                    env_vars = {}
                    if os.path.exists('.env'):
                        load_dotenv()
                        with open('.env', 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    env_vars[key] = value
                    
                    # Update with cleaned values
                    env_vars['FULFILLMENT_POLICY_ID'] = fulfillment_id_clean
                    env_vars['PAYMENT_POLICY_ID'] = payment_id_clean
                    env_vars['RETURN_POLICY_ID'] = return_id_clean
                    env_vars['MERCHANT_LOCATION_KEY'] = location_key.strip() if location_key else ''
                    
                    # Read template
                    template_lines = []
                    if os.path.exists('env_example.txt'):
                        with open('env_example.txt', 'r') as f:
                            template_lines = f.readlines()
                    
                    # Write .env file
                    with open('.env', 'w') as f:
                        for line in template_lines:
                            line_stripped = line.strip()
                            if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                                key = line_stripped.split('=', 1)[0]
                                if key in env_vars:
                                    f.write(f"{key}={env_vars[key]}\n")
                                else:
                                    f.write(line)
                            else:
                                f.write(line)
                        
                        # Add any new variables not in template
                        template_keys = set()
                        for line in template_lines:
                            if '=' in line and not line.strip().startswith('#'):
                                template_keys.add(line.split('=', 1)[0].strip())
                        
                        for key, value in env_vars.items():
                            if key not in template_keys:
                                f.write(f"{key}={value}\n")
                    
                    # Show what was saved
                    saved_items = []
                    if env_vars.get('FULFILLMENT_POLICY_ID'):
                        saved_items.append(f"✅ Fulfillment Policy: `{env_vars['FULFILLMENT_POLICY_ID']}`")
                    if env_vars.get('PAYMENT_POLICY_ID'):
                        saved_items.append(f"✅ Payment Policy: `{env_vars['PAYMENT_POLICY_ID']}`")
                    if env_vars.get('RETURN_POLICY_ID'):
                        saved_items.append(f"✅ Return Policy: `{env_vars['RETURN_POLICY_ID']}`")
                    if env_vars.get('MERCHANT_LOCATION_KEY'):
                        saved_items.append(f"✅ Location Key: `{env_vars['MERCHANT_LOCATION_KEY']}`")
                    
                    if saved_items:
                        st.success("✅ Configuration saved successfully!")
                        st.markdown("\n".join(saved_items))
                        st.info("👉 Continue to Step 4: Verify")
                    else:
                        st.warning("⚠ No values were saved. Please enter at least one policy ID.")
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error saving configuration: {str(e)}")
                    st.exception(e)
        
        st.markdown("---")
        st.subheader("💡 How to Find Policy IDs")
        st.info("""
        **Option 1: eBay Seller Hub (Production)**
        1. Go to [eBay Seller Hub](https://www.ebay.com/sh/landing)
        2. Navigate to **Account → Business Policies**
        3. Click on each policy type (Fulfillment, Payment, Return)
        4. The Policy ID is usually shown in the URL or policy details
        
        **Option 2: Create New Policies**
        1. In eBay Seller Hub, go to **Account → Business Policies**
        2. Click "Create" for each policy type
        3. Fill in the details and save
        4. The Policy ID will be shown after creation
        
        **Option 3: For Sandbox**
        - Policies may need to be created in the Sandbox environment first
        - Visit the Sandbox Seller Hub and create policies there
        - Or use default/test values if available
        """)
    
    # Show current status (outside tabs)
    st.markdown("---")
    st.subheader("Current Status")
    try:
        from config import Config
        config = Config()
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**Policies:**")
            st.write(f"Fulfillment: {'✅ Set' if config.FULFILLMENT_POLICY_ID else '❌ Not set'}")
            if config.FULFILLMENT_POLICY_ID:
                st.caption(f"ID: `{config.FULFILLMENT_POLICY_ID}`")
            st.write(f"Payment: {'✅ Set' if config.PAYMENT_POLICY_ID else '❌ Not set'}")
            if config.PAYMENT_POLICY_ID:
                st.caption(f"ID: `{config.PAYMENT_POLICY_ID}`")
            st.write(f"Return: {'✅ Set' if config.RETURN_POLICY_ID else '❌ Not set'}")
            if config.RETURN_POLICY_ID:
                st.caption(f"ID: `{config.RETURN_POLICY_ID}`")
        
        with col_b:
            st.write("**Location:**")
            st.write(f"Merchant Location: {'✅ Set' if config.MERCHANT_LOCATION_KEY else '❌ Not set'}")
            if config.MERCHANT_LOCATION_KEY:
                st.caption(f"Key: `{config.MERCHANT_LOCATION_KEY}`")
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
        
        # Required items (policies are critical)
        required_items = [item for item in status_items if item[0] != "Merchant Location"]
        all_required_good = all(item[1] for item in required_items)
        
        # Optional items
        location_set = bool(config.MERCHANT_LOCATION_KEY)
        
        for name, status in status_items:
            if name == "Merchant Location":
                # Show as info/warning, not error (it's optional)
                if status:
                    st.success(f"✅ {name}")
                else:
                    st.info(f"ℹ️ {name} (Optional - can be set later)")
            elif status:
                st.success(f"✅ {name}")
            else:
                st.error(f"❌ {name}")
        
        if all_required_good:
            st.success("🎉 **All required configuration is complete!**")
            if not location_set:
                st.info("""
                **Optional: Merchant Location Key**
                
                The Merchant Location Key is optional but can be useful for:
                - Managing inventory from multiple locations
                - Tracking where items ship from
                
                **To set it (optional):**
                1. Go to **Step 3: Auto-Configure** → Click "🚀 Auto-Configure Now"
                2. Or go to eBay Seller Hub → **Account → Shipping Preferences**
                3. Find your default shipping location
                4. The location key will be shown there
                
                **You can start using the bot now** - the location can be set later if needed!
                """)
            else:
                st.balloons()
                st.success("✨ **Perfect! Everything is configured and ready to go!**")
        else:
            st.warning("""
            ⚠️ **Some required configuration is missing!**
            
            **What to do:**
            1. Go back to **Step 3: Auto-Configure**
            2. Use the **"✏️ Manual Entry"** tab to enter your Policy IDs
            3. Or click **"🚀 Auto-Configure Now"** to fetch them automatically
            4. Come back to Step 4 and verify again
            
            **If Auto-Configure doesn't find policies:**
            - You may need to create them in eBay Seller Hub first
            - Go to: eBay Seller Hub → Account → Business Policies
            - Create at least one Fulfillment, Payment, and Return policy
            - Then run Auto-Configure again
            
            **Note:** Merchant Location is optional and not required for creating listings.
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

def step6_publish_drafts():
    """Step 6: Publish existing draft listings."""
    st.header("Step 6: Publish Draft Listings")
    st.info("""
    Publish your existing draft listings. This will automatically fix any issues (description, policies) and publish them to eBay Sandbox.
    """)
    
    # Check if setup is complete
    try:
        from config import Config
        config = Config()
        if not config.ebay_token:
            st.error("❌ Please complete Step 2 (Login) first!")
            return
    except Exception as e:
        st.error(f"❌ Configuration error: {str(e)}")
        return
    
    st.success("✅ Ready to publish drafts!")
    
    # Show sandbox limitation warning
    st.warning("""
    **⚠️ Sandbox Limitation Notice:**
    
    eBay Sandbox has a known issue where descriptions don't always persist properly, 
    which can prevent publishing. If publishing fails with Error 25016, this is a 
    sandbox quirk, not a problem with your listings.
    
    **Your listings are saved as drafts** with all the correct data. You can:
    1. View them in the HTML page (editable_listings.html)
    2. Add images to them
    3. Try publishing again later (sometimes sandbox needs time)
    4. Use production environment when ready (will work better)
    """)
    
    st.markdown("---")
    
    # Check for published listings
    if st.button("🔍 Check Published Listings", type="primary", key="check_published"):
        with st.spinner("Checking for published listings..."):
            try:
                from ebay_api_client import eBayAPIClient
                client = eBayAPIClient()
                
                # Get inventory items
                items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
                
                if items_response.status_code != 200:
                    st.error(f"Failed to fetch listings: {items_response.status_code}")
                else:
                    items_data = items_response.json()
                    inventory_items = items_data.get('inventoryItems', [])
                    
                    # Get offers and find published ones
                    published = []
                    for item in inventory_items:
                        sku = item.get('sku')
                        if sku:
                            offer_result = client.get_offer_by_sku(sku)
                            if offer_result.get('success') and offer_result.get('offer'):
                                offer = offer_result['offer']
                                listing_id = offer.get('listingId')
                                if listing_id:  # Published
                                    title = (
                                        offer.get('listing', {}).get('title', '') or
                                        offer.get('title', '') or
                                        'Untitled Listing'
                                    )
                                    published.append({
                                        'sku': sku,
                                        'title': title,
                                        'listing_id': listing_id,
                                        'offer_id': offer.get('offerId'),
                                        'price': offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A'),
                                        'quantity': offer.get('availableQuantity', offer.get('quantity', 'N/A'))
                                    })
                    
                    st.session_state['published_listings'] = published
                    if published:
                        st.success(f"✅ Found {len(published)} published listing(s)!")
                    else:
                        st.info("No published listings found yet.")
                        
            except Exception as e:
                st.error(f"Error checking published listings: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Show published listings
    if 'published_listings' in st.session_state and st.session_state['published_listings']:
        published = st.session_state['published_listings']
        
        st.markdown("---")
        st.subheader(f"✅ Published Listings ({len(published)} found)")
        
        for i, listing in enumerate(published):
            listing_url = f"https://sandbox.ebay.com/itm/{listing['listing_id']}"
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{listing['title']}**")
                st.caption(f"SKU: {listing['sku']} | Listing ID: {listing['listing_id']} | Price: ${listing['price']}")
            
            with col2:
                st.markdown(f"""
                <a href="{listing_url}" target="_blank">
                    <button style="
                        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                        color: white;
                        border: none;
                        border-radius: 15px;
                        padding: 10px 20px;
                        font-size: 14px;
                        font-weight: bold;
                        cursor: pointer;
                        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
                        text-decoration: none;
                        display: inline-block;
                        width: 100%;
                    ">
                        🔗 View on Sandbox
                    </button>
                </a>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    st.markdown("---")
    
    # Fetch all drafts
    if st.button("🔍 Load Draft Listings", type="primary"):
        with st.spinner("Fetching draft listings..."):
            try:
                from ebay_api_client import eBayAPIClient
                client = eBayAPIClient()
                
                # Get inventory items
                items_response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 100})
                
                if items_response.status_code != 200:
                    st.error(f"Failed to fetch listings: {items_response.status_code}")
                    return
                
                items_data = items_response.json()
                inventory_items = items_data.get('inventoryItems', [])
                
                # Get offers
                drafts = []
                for item in inventory_items:
                    sku = item.get('sku')
                    if sku:
                        offer_result = client.get_offer_by_sku(sku)
                        if offer_result.get('success') and offer_result.get('offer'):
                            offer = offer_result['offer']
                            if not offer.get('listingId'):  # Draft
                                title = (
                                    offer.get('listing', {}).get('title', '') or
                                    offer.get('title', '') or
                                    'Untitled Listing'
                                )
                                drafts.append({
                                    'sku': sku,
                                    'title': title,
                                    'offer_id': offer.get('offerId'),
                                    'group_key': offer.get('inventoryItemGroupKey', ''),
                                    'price': offer.get('pricingSummary', {}).get('price', {}).get('value', 'N/A'),
                                    'quantity': offer.get('availableQuantity', offer.get('quantity', 'N/A'))
                                })
                
                st.session_state['draft_listings'] = drafts
                st.success(f"✅ Found {len(drafts)} draft listing(s)")
                
            except Exception as e:
                st.error(f"Error fetching drafts: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display drafts
    if 'draft_listings' in st.session_state and st.session_state['draft_listings']:
        drafts = st.session_state['draft_listings']
        
        st.subheader(f"📦 Draft Listings ({len(drafts)} found)")
        
        # Publish all button
        if st.button("🚀 Publish ALL Drafts", type="primary", use_container_width=True):
            with st.spinner("Publishing all drafts (this may take a few minutes)..."):
                from ebay_api_client import eBayAPIClient
                import time
                import subprocess
                import sys
                
                client = eBayAPIClient()
                
                published_count = 0
                failed_count = 0
                results = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, draft in enumerate(drafts):
                    status_text.text(f"Publishing {i+1}/{len(drafts)}: {draft['title'][:40]}...")
                    progress_bar.progress((i + 1) / len(drafts))
                    
                    try:
                        # Use the publish_draft script which handles everything
                        result = subprocess.run(
                            [sys.executable, "publish_draft.py", draft['sku']],
                            capture_output=True,
                            text=True,
                            timeout=60,
                            cwd=os.getcwd()
                        )
                        
                        output = result.stdout + result.stderr
                        
                        if "SUCCESS" in output or "Listing Published" in output or "Listing ID:" in output:
                            published_count += 1
                            # Extract listing ID if present
                            import re
                            listing_id_match = re.search(r'Listing ID:\s*(\d+)', output)
                            if listing_id_match:
                                listing_id = listing_id_match.group(1)
                                results.append(f"✅ {draft['sku'][:30]}... → Published (ID: {listing_id})")
                            else:
                                results.append(f"✅ {draft['sku'][:30]}... → Published")
                        else:
                            failed_count += 1
                            error_msg = output[-200:] if len(output) > 200 else output
                            results.append(f"❌ {draft['sku'][:30]}... → Failed")
                        
                        time.sleep(2)  # Rate limiting
                    except Exception as e:
                        failed_count += 1
                        results.append(f"❌ {draft['sku'][:30]}... → Error: {str(e)[:50]}")
                
                progress_bar.empty()
                status_text.empty()
                
                # Show results
                if published_count > 0:
                    st.success(f"✅ Published {published_count} listing(s)!")
                    st.balloons()
                    st.info("💡 Click 'Check Published Listings' above to see them with view buttons!")
                if failed_count > 0:
                    st.warning(f"⚠️ {failed_count} listing(s) failed to publish")
                    st.info("""
                    **If you see Error 25016 (description required):**
                    This is a known eBay Sandbox limitation. The listings are saved as drafts 
                    with all correct data. The sandbox API sometimes doesn't recognize descriptions 
                    even though they're saved.
                    
                    **Options:**
                    1. View your drafts in the HTML page (editable_listings.html)
                    2. Add images to them
                    3. Try again later (sandbox may need time to propagate)
                    4. Wait until production - this works better in production
                    """)
                
                # Show detailed results
                with st.expander("📋 Detailed Results", expanded=True):
                    for result in results:
                        st.text(result)
                
                # Auto-refresh to show published listings
                if published_count > 0:
                    st.info("🔄 Refreshing to show published listings...")
                    time.sleep(2)
                    st.rerun()
        
        st.markdown("---")
        
        # Individual listings
        for i, draft in enumerate(drafts):
            with st.expander(f"📦 {draft['title'][:50]}... (SKU: {draft['sku'][:30]}...)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**SKU:** {draft['sku']}")
                    st.write(f"**Offer ID:** {draft['offer_id']}")
                    st.write(f"**Price:** ${draft['price']}")
                    st.write(f"**Quantity:** {draft['quantity']}")
                    if draft['group_key']:
                        st.write(f"**Group Key:** {draft['group_key']} (Variation Listing)")
                
                with col2:
                    if st.button("🚀 Publish", key=f"publish_{i}", type="primary"):
                        with st.spinner("Publishing (this may take a moment)..."):
                            try:
                                import subprocess
                                import sys
                                
                                # Use the publish_draft script which handles everything automatically
                                result = subprocess.run(
                                    [sys.executable, "publish_draft.py", draft['sku']],
                                    capture_output=True,
                                    text=True,
                                    timeout=60,
                                    cwd=os.getcwd()
                                )
                                
                                output = result.stdout + result.stderr
                                
                                if "SUCCESS" in output or "Listing Published" in output or "Listing ID:" in output:
                                    # Extract listing ID if present
                                    import re
                                    listing_id_match = re.search(r'Listing ID:\s*(\d+)', output)
                                    if listing_id_match:
                                        listing_id = listing_id_match.group(1)
                                        listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
                                        st.success(f"✅ Published! Listing ID: {listing_id}")
                                        st.markdown(f"[🔗 View Listing on Sandbox]({listing_url})")
                                    else:
                                        st.success("✅ Published! (Check output for details)")
                                    
                                    # Show last few lines of output
                                    output_lines = output.split('\n')
                                    last_lines = [l for l in output_lines[-10:] if l.strip()]
                                    if last_lines:
                                        with st.expander("📋 Details"):
                                            st.code('\n'.join(last_lines))
                                else:
                                    st.error("❌ Failed to publish")
                                    # Show error details
                                    error_lines = [l for l in output.split('\n') if 'ERROR' in l or 'Error' in l or 'error' in l][-5:]
                                    if error_lines:
                                        st.code('\n'.join(error_lines))
                                    else:
                                        st.code(output[-500:])  # Last 500 chars
                                        
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                import traceback
                                st.code(traceback.format_exc())

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
                
                # Always create as drafts in production to avoid going live
                from config import Config
                config = Config()
                is_production = config.EBAY_ENVIRONMENT.lower() == 'production'
                
                if is_production:
                    publish_immediately = False  # Force drafts in production
                    st.warning("⚠️ **PRODUCTION MODE:** Listings will be created as DRAFTS only (not published live). You can view and edit them in eBay Seller Hub.")
                else:
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
                        
                        # Create listing - ONLY cards with quantity > 0
                        result = listing_manager.create_variation_listing(
                            cards=listing_cards,  # Pass cards directly
                            title=final_title.strip(),  # Ensure it's trimmed
                            description=final_description or f"Variation listing with {len(listing_cards)} cards. Each card listed separately as a variation.",
                            category_id=category_id,
                            price=final_price,  # Can be float or dict of per-card prices
                            quantity=1,  # Per-card quantity is in the card data
                            condition=condition,
                            publish=publish_immediately
                        )
                        
                        if result.get('success'):
                            is_draft = result.get('draft', False)
                            listing_id = result.get('listing_id')
                            group_key = result.get('group_key')
                            
                            # Show success message
                            st.success("🎉 Listing created successfully!")
                            st.balloons()
                            
                            # Provide multiple ways to view the listing
                            st.markdown("---")
                            st.subheader("📍 How to View Your Listing in Sandbox")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### Option 1: eBay Seller Hub (Inventory)")
                                st.markdown("""
                                **Best for:** Viewing all your listings, drafts, and active listings
                                
                                **Steps:**
                                1. Click the button below
                                2. Log in to sandbox (if needed)
                                3. Go to **"Active"** or **"Drafts"** tab
                                4. Find your listing by title: **""" + final_title + """**
                                """)
                                # Try multiple sandbox URLs - eBay sandbox URLs can be tricky
                                st.markdown("### 🔗 Try These Sandbox Links:")
                                
                                sandbox_urls = [
                                    ("Seller Hub - Inventory", "https://sandbox.ebay.com/sh/account/inventory"),
                                    ("Seller Hub - Listings", "https://sandbox.ebay.com/sh/account/listings"),
                                    ("Seller Hub - Drafts", "https://sandbox.ebay.com/sh/account/listings?status=DRAFT"),
                                    ("Seller Hub - Active", "https://sandbox.ebay.com/sh/account/listings?status=ACTIVE"),
                                    ("Seller Hub - Main", "https://sandbox.ebay.com/sh/landing"),
                                ]
                                
                                for url_name, url_link in sandbox_urls:
                                    st.markdown(f"""
                                    <a href="{url_link}" target="_blank" style="text-decoration: none;">
                                        <button style="
                                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                            color: white;
                                            border: none;
                                            border-radius: 15px;
                                            padding: 10px 20px;
                                            font-size: 14px;
                                            font-weight: bold;
                                            cursor: pointer;
                                            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                                            text-decoration: none;
                                            display: inline-block;
                                            margin: 5px;
                                        ">
                                            🔗 {url_name}
                                        </button>
                                    </a>
                                    """, unsafe_allow_html=True)
                                
                                st.markdown("---")
                                st.warning("""
                                **⚠️ Important:** eBay sandbox Seller Hub URLs often redirect to error pages.
                                
                                **✅ Best Solution - Use the API Script:**
                                1. Run this command in terminal:
                                   ```
                                   python find_my_listing.py """ + final_title + """
                                   ```
                                2. Or if you have the group key:
                                   ```
                                   python find_my_listing.py """ + (group_key if group_key else "YOUR_GROUP_KEY") + """
                                   ```
                                3. Or see ALL listings:
                                   ```
                                   python find_my_listing.py
                                   ```
                                4. This will show you direct links to your listing!
                                
                                **Alternative - Manual Navigation:**
                                1. Go to: https://sandbox.ebay.com
                                2. Sign in with your sandbox test user (TESTUSER_...)
                                3. The listing should appear in your account
                                4. Look for it in "My eBay" → "Selling" → "Active" or "Drafts"
                                
                                **Note:** Sandbox UI is limited - API is more reliable!
                                """)
                                
                                if group_key:
                                    st.code(f"python find_my_listing.py \"{final_title}\"\n# OR\npython find_my_listing.py {group_key}\n# OR see all listings:\npython find_my_listing.py", language="bash")
                                
                                # Add a button to run the script directly
                                st.markdown("---")
                                if st.button("🔍 Find My Listing (Run Script)", key="find_listing_btn"):
                                    import subprocess
                                    import sys
                                    try:
                                        result = subprocess.run(
                                            [sys.executable, "find_my_listing.py", final_title] if final_title else [sys.executable, "find_my_listing.py"],
                                            capture_output=True,
                                            text=True,
                                            cwd=os.getcwd()
                                        )
                                        st.code(result.stdout, language="text")
                                        if result.stderr:
                                            st.code(result.stderr, language="text")
                                    except Exception as e:
                                        st.error(f"Error running script: {e}")
                                        st.info("You can also run it manually in terminal: `python find_my_listing.py\"")
                            
                            with col2:
                                st.markdown("### Option 2: Direct Listing Link")
                                if listing_id:
                                    listing_url = f"https://sandbox.ebay.com/itm/{listing_id}"
                                    st.markdown(f"""
                                    **Direct link to your listing:**
                                    
                                    [View Listing: {listing_id}]({listing_url})
                                    """)
                                    st.markdown(f"""
                                    <a href="{listing_url}" target="_blank">
                                        <button style="
                                            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                                            color: white;
                                            border: none;
                                            border-radius: 25px;
                                            padding: 15px 30px;
                                            font-size: 16px;
                                            font-weight: bold;
                                            cursor: pointer;
                                            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
                                            text-decoration: none;
                                            display: inline-block;
                                            width: 100%;
                                        ">
                                            🔗 View Published Listing
                                        </button>
                                    </a>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.info("""
                                    **Note:** This listing was created as a draft.
                                    
                                    Use **Option 1** above to view it in Seller Hub.
                                    """)
                            
                            # Show listing details
                            st.markdown("---")
                            st.subheader("📋 Listing Details")
                            
                            info_cols = st.columns(3)
                            with info_cols[0]:
                                st.metric("Title", final_title[:40] + "..." if len(final_title) > 40 else final_title)
                            with info_cols[1]:
                                if listing_id:
                                    st.metric("Listing ID", listing_id)
                                elif group_key:
                                    st.metric("Group Key", group_key[:20] + "..." if len(group_key) > 20 else group_key)
                            with info_cols[2]:
                                st.metric("Cards", len(listing_cards))
                            
                            if group_key:
                                with st.expander("🔧 Technical Details", expanded=False):
                                    st.code(f"Group Key: {group_key}", language=None)
                                    st.caption("Use this to reference the listing in API calls")
                            
                            if is_draft:
                                # Draft listing created (workaround for Error 25016)
                                st.warning("""
                                **⚠️ Note:** The listing was saved as a draft due to a sandbox API limitation (Error 25016).
                                
                                **What to do next:**
                                1. Use the links above to open eBay Seller Hub
                                2. Go to **"Drafts"** tab
                                3. Find your listing (title: **""" + final_title + """**)
                                4. Add/edit the description if needed
                                5. Publish the listing from eBay Seller Hub
                                """)
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            st.error(f"❌ Failed to create listing: {error_msg}")
                            
                            # Show debug info if available
                            if result.get('debug_info'):
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

def check_credentials():
    """Check if API credentials are set."""
    try:
        from config import Config
        config = Config()
        return bool(config.EBAY_APP_ID and config.EBAY_DEV_ID and config.EBAY_CERT_ID)
    except:
        return False

if __name__ == "__main__":
    main()
