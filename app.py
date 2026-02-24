"""eBay Card Listing Tool - Main Application
Multi-user support with PayPal subscription
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from ebay_api_client import eBayAPIClient
from ebay_listing import eBayListingManager
from card_checklist import CardChecklistFetcher
import sys
import time
import uuid
import re
import json
import os
import hashlib
import urllib.parse
from datetime import datetime
from functools import wraps
from json import JSONDecodeError

sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# VERSION - Single source of truth
# =============================================================================
VERSION = "4.0"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# =============================================================================
# GLOBAL ERROR HANDLERS - Prevent crashes
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors gracefully."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully."""
    import traceback
    print(f"[ERROR] Internal server error: {error}")
    traceback.print_exc()
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again."
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions."""
    import traceback
    error_trace = traceback.format_exc()
    print(f"[ERROR] Unhandled exception: {e}")
    print(f"[ERROR] Traceback:\n{error_trace}")
    
    # Return JSON error for API routes
    if request.path.startswith('/api/'):
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "An error occurred. Please try again."
        }), 500
    
    # Return HTML error for page routes
    return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.before_request
def before_request():
    """Run before each request."""
    try:
        # Add request ID for tracking
        request.request_id = str(uuid.uuid4())[:8]
    except Exception as e:
        print(f"[WARNING] Error in before_request: {e}")

@app.after_request
def after_request(response):
    """Run after each request."""
    try:
        # Add CORS headers if needed
        response.headers['X-Request-ID'] = getattr(request, 'request_id', 'unknown')
        # Prevent crashes from response errors
        return response
    except Exception as e:
        print(f"[WARNING] Error in after_request: {e}")
        return response

# =============================================================================
# CONFIGURATION
# =============================================================================

# Owner email - FREE ACCESS (configurable via env, default for manhattanbreaks)
OWNER_EMAIL = os.environ.get('OWNER_EMAIL', 'manhattanbreaks@gmail.com')

# Admin password (hashed) - set ADMIN_PASSWORD in env for production
_admin_pw = os.environ.get('ADMIN_PASSWORD', 'Bobbo2365@ss')
ADMIN_PASSWORD_HASH = hashlib.sha256(_admin_pw.encode()).hexdigest()

# PayPal configuration (configurable via env)
PAYPAL_EMAIL = os.environ.get('PAYPAL_EMAIL', 'manhattanbreaks@gmail.com')
SUBSCRIPTION_PRICE_MONTHLY = "14.99"  # Discounted from $29.99 (50% off)
SUBSCRIPTION_PRICE_YEARLY = "124.00"  # Discounted from $249 (50% off)
SUBSCRIPTION_PRICE_MONTHLY_ORIGINAL = "29.99"
SUBSCRIPTION_PRICE_YEARLY_ORIGINAL = "249.00"
SUBSCRIPTION_PERIOD = "month"

# PayPal subscription button ID (you'll get this from PayPal)
# For now, we'll use a direct PayPal.me link or subscription button
PAYPAL_BUTTON_ID = ""  # Set this after creating in PayPal

# 3-day free trial for new registrations
TRIAL_DAYS = 3

# Store active subscriptions (in production, use a database)
# Format: {"email": {"status": "active", "expires": "2024-02-01", "paypal_id": "xxx", "last_payment": "2024-01-01"}}
SUBSCRIPTIONS_FILE = "subscriptions.json"

# Store payment records
# Format: {"email": [{"date": "2024-01-01", "amount": "9.99", "transaction_id": "xxx", "notes": ""}]}
PAYMENTS_FILE = "payments.json"

# Per-user eBay tokens (each subscriber uses their own eBay account)
USER_TOKENS_FILE = "user_tokens.json"

# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

def load_subscriptions():
    """Load subscriptions from file."""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_subscriptions(subs):
    """Save subscriptions to file."""
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subs, f, indent=2)

def load_payments():
    """Load payment records from file."""
    if os.path.exists(PAYMENTS_FILE):
        try:
            with open(PAYMENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_payments(payments):
    """Save payment records to file."""
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(payments, f, indent=2)

def load_user_tokens():
    """Load per-user eBay tokens from file."""
    if os.path.exists(USER_TOKENS_FILE):
        try:
            with open(USER_TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_tokens(tokens):
    """Save per-user eBay tokens to file."""
    with open(USER_TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2)

def get_token_for_user(email):
    """Get eBay token for current user. Returns user's token if set, else None (use env token)."""
    if not email:
        return None
    tokens = load_user_tokens()
    entry = tokens.get(email.lower(), {})
    token = entry.get('token')
    if not token:
        return None
    # User tokens (v^1.1#) can be used directly
    if entry.get('is_user_token', token.startswith('v^1.1#')):
        return token
    # OAuth refresh token - exchange for access token
    try:
        from ebay_oauth import eBayOAuth
        oauth = eBayOAuth()
        result = oauth.refresh_token(token)
        if result.get('success') and result.get('access_token'):
            return result['access_token']
    except Exception as e:
        print(f"[WARNING] Could not refresh user token for {email}: {e}")
    return None

def is_subscribed(email):
    """Check if email has active subscription or valid trial."""
    if email.lower() == OWNER_EMAIL.lower():
        return True  # Owner always has access
    
    subs = load_subscriptions()
    sub = subs.get(email.lower(), {})
    
    # Check for active trial
    trial_ends = sub.get('trial_ends', '')
    if trial_ends:
        from datetime import datetime
        try:
            trial_end_date = datetime.strptime(trial_ends, '%Y-%m-%d')
            if datetime.now().date() <= trial_end_date.date():
                return True  # Trial still active
        except Exception:
            pass
    
    if sub.get('status') != 'active':
        return False
    
    # Check subscription expiration
    expires = sub.get('expires', '')
    if expires:
        from datetime import datetime
        try:
            expires_date = datetime.strptime(expires, '%Y-%m-%d')
            if datetime.now() > expires_date:
                return False
        except Exception:
            pass
    
    return True

def require_subscription(f):
    """Decorator to require active subscription."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            email = session.get('user_email', '')
            if not email:
                return redirect('/login')
            
            # Owner always has access
            if email.lower() == OWNER_EMAIL.lower():
                return f(*args, **kwargs)
            
            if not is_subscribed(email):
                return jsonify({"error": "Subscription required. Please subscribe to continue."}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            print(f"[ERROR] Error in require_subscription decorator: {e}")
            import traceback
            traceback.print_exc()
            # Return appropriate error based on request type
            if request.path.startswith('/api/'):
                return jsonify({"error": "An error occurred. Please try again."}), 500
            return redirect('/login')
    return decorated_function

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def landing():
    """Landing page."""
    try:
        return render_template('landing.html')
    except Exception as e:
        print(f"[ERROR] Error in landing: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/pictures/<filename>')
def serve_picture(filename):
    """Serve images from the pictures folder."""
    try:
        return send_from_directory('pictures', filename)
    except Exception as e:
        print(f"[ERROR] Error serving picture {filename}: {e}")
        return f"<h1>Error</h1><p>Image not found: {filename}</p>", 404

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with 3-day free trial."""
    try:
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            name = request.form.get('name', '').strip()
            
            if not email:
                return render_template('register.html', error='Email is required.')
            
            # Owner cannot register as new user
            if email == OWNER_EMAIL.lower():
                return render_template('register.html', error='Please use Login for this account.')
            
            subs = load_subscriptions()
            
            # If already have active sub or trial, redirect to login
            if email in subs:
                sub = subs[email]
                if is_subscribed(email):
                    session['user_email'] = email
                    return redirect('/app')
                # Expired - allow re-register for new trial?
                # For now we'll give them another trial if they register again
                # (removes old record and creates fresh trial)
            
            # Create new account with 3-day trial
            from datetime import datetime, timedelta
            trial_end = (datetime.now() + timedelta(days=TRIAL_DAYS)).strftime('%Y-%m-%d')
            
            subs[email] = {
                'status': 'trial',
                'trial_ends': trial_end,
                'name': name or '',
                'registered': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'expires': ''  # No paid expiry yet
            }
            save_subscriptions(subs)
            
            session['user_email'] = email
            return redirect('/app')
        
        return render_template('register.html')
    except Exception as e:
        print(f"[ERROR] Error in register: {e}")
        import traceback
        traceback.print_exc()
        return render_template('register.html', error=f'An error occurred: {str(e)}')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    try:
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            # Owner login requires password
            if email == OWNER_EMAIL.lower():
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if password_hash == ADMIN_PASSWORD_HASH:
                    session['user_email'] = email
                    return redirect('/app')
                else:
                    return render_template('login.html', error='Invalid password')
            
            # For other users, just check subscription
            if is_subscribed(email):
                session['user_email'] = email
                return redirect('/app')
            else:
                return render_template('login.html', error='Subscription required. Please subscribe first.')
        
        return render_template('login.html')
    except Exception as e:
        print(f"[ERROR] Error in login: {e}")
        import traceback
        traceback.print_exc()
        return render_template('login.html', error=f'An error occurred: {str(e)}')

@app.route('/logout')
def logout():
    """User logout."""
    session.pop('user_email', None)
    session.pop('admin_authenticated', None)
    return redirect('/')

@app.route('/subscribe')
def subscribe():
    """Subscription page."""
    try:
        # Build return URLs for PayPal (use request host for correct redirect)
        base = request.url_root.rstrip('/')
        return_url = f"{base}/payment-success"
        cancel_url = f"{base}/payment-cancel"
        return render_template('subscribe.html', 
                             monthly_price=SUBSCRIPTION_PRICE_MONTHLY,
                             yearly_price=SUBSCRIPTION_PRICE_YEARLY,
                             monthly_original=SUBSCRIPTION_PRICE_MONTHLY_ORIGINAL,
                             yearly_original=SUBSCRIPTION_PRICE_YEARLY_ORIGINAL,
                             paypal_email=PAYPAL_EMAIL,
                             return_url=return_url,
                             cancel_url=cancel_url)
    except Exception as e:
        print(f"[ERROR] Error in subscribe: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/contact')
def contact():
    """Contact page."""
    try:
        return render_template('contact.html')
    except Exception as e:
        print(f"[ERROR] Error in contact: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/auth/ebay')
def auth_ebay():
    """Redirect to eBay OAuth - for subscribers to connect their eBay account."""
    email = session.get('user_email', '')
    if not email:
        return redirect(url_for('login') + '?next=/auth/ebay')
    try:
        from ebay_oauth import eBayOAuth
        oauth = eBayOAuth()
        auth_url = oauth.get_authorization_url()
        return redirect(auth_url)
    except Exception as e:
        print(f"[ERROR] OAuth init failed: {e}")
        return redirect('/setup')

@app.route('/callback')
def oauth_callback():
    """eBay OAuth callback - exchange code for token and save to user account."""
    email = session.get('user_email', '')
    if not email:
        return redirect('/login?error=Session expired. Please log in again.')
    code = request.args.get('code')
    error = request.args.get('error')
    if error:
        return redirect(f'/setup?error={error}')
    if not code:
        return redirect('/setup?error=No authorization code received')
    try:
        from ebay_oauth import eBayOAuth
        oauth = eBayOAuth()
        result = oauth.exchange_code_for_token(code)
        if result.get('success') and result.get('refresh_token'):
            refresh_token = result['refresh_token']
            tokens = load_user_tokens()
            tokens[email.lower()] = {
                "token": refresh_token,
                "type": "OAuth Refresh Token",
                "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "is_user_token": False
            }
            save_user_tokens(tokens)
            print(f"[INFO] OAuth token saved for {email}")
            return redirect('/app?ebay_connected=1')
        else:
            err_msg = result.get('message', result.get('error', {}).get('error_description', 'Unknown error'))
            return redirect(f'/setup?error={urllib.parse.quote(str(err_msg)[:200])}')
    except Exception as e:
        print(f"[ERROR] OAuth callback failed: {e}")
        import traceback
        traceback.print_exc()
        return redirect(f'/setup?error={urllib.parse.quote(str(e)[:200])}')

@app.route('/setup')
def setup():
    """Setup guide."""
    try:
        is_hosted = os.environ.get('RENDER') == 'true'
        app_url = os.environ.get('RENDER_EXTERNAL_URL', request.url_root.rstrip('/'))
        oauth_error = request.args.get('error', '')
        return render_template('setup.html', is_hosted=is_hosted, app_url=app_url, oauth_error=oauth_error)
    except Exception as e:
        print(f"[ERROR] Error in setup: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/app')
def app_page():
    """Main application page (requires subscription)."""
    try:
        email = session.get('user_email', '')
        if not email:
            return redirect('/login')
        
        # Owner always has access
        if email.lower() == OWNER_EMAIL.lower():
            return render_template('app.html', email=email)
        
        # Check subscription for other users
        if not is_subscribed(email):
            return redirect('/subscribe')
        
        return render_template('app.html', email=email)
    except Exception as e:
        print(f"[ERROR] Error in app_page: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/payment-success')
def payment_success():
    """Payment success page."""
    try:
        return render_template('payment_success.html')
    except Exception as e:
        print(f"[ERROR] Error in payment_success: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/payment-cancel')
def payment_cancel():
    """Payment cancel page."""
    try:
        return render_template('payment_cancel.html')
    except Exception as e:
        print(f"[ERROR] Error in payment_cancel: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

# =============================================================================
# API ROUTES
# =============================================================================

def _get_effective_token():
    """Get eBay token for current user: per-user token if set, else env token."""
    email = session.get('user_email', '')
    return get_token_for_user(email)

@app.route('/api/policies')
@require_subscription
def get_policies():
    """Get eBay policies (payment, shipping, return)."""
    try:
        token = _get_effective_token()
        client = eBayAPIClient(token_override=token)
        client._update_headers()
        
        policies = {"payment": [], "shipping": [], "returns": []}
        
        # Get payment policies
        try:
            resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
            if resp.status_code == 200:
                data = resp.json()
                policies['payment'] = [{"id": p.get('paymentPolicyId'), "name": p.get('name')} 
                                       for p in data.get('paymentPolicies', [])]
            elif resp.status_code == 401:
                error_text = resp.text[:500]
                print(f"[DEBUG] Payment policy API returned 401 (Unauthorized)")
                print(f"[DEBUG] Response: {error_text}")
                # Check for specific error types
                try:
                    error_json = resp.json()
                    if 'unauthorized_client' in str(error_json).lower() or 'oauth client was not found' in str(error_json).lower():
                        return jsonify({"error": "OAuth client not found. Check your APP_ID and CERT_ID in .env file. See /setup for help."}), 401
                except:
                    pass
                return jsonify({"error": "Token expired or invalid. Click 'Get OAuth Token' button or run 'python refresh_token.py' to refresh, or check your .env credentials."}), 401
            else:
                print(f"[DEBUG] Payment policy API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[DEBUG] Error fetching payment policies: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                return jsonify({"error": "Token expired or invalid. Run 'python refresh_token.py' to refresh."}), 401
        
        # Get shipping policies
        try:
            resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
            if resp.status_code == 200:
                data = resp.json()
                policies['shipping'] = [{"id": p.get('fulfillmentPolicyId'), "name": p.get('name')} 
                                        for p in data.get('fulfillmentPolicies', [])]
            elif resp.status_code == 401:
                error_text = resp.text[:500]
                print(f"[DEBUG] Shipping policy API returned 401 (Unauthorized)")
                print(f"[DEBUG] Response: {error_text}")
                # Check for specific error types
                try:
                    error_json = resp.json()
                    if 'unauthorized_client' in str(error_json).lower() or 'oauth client was not found' in str(error_json).lower():
                        return jsonify({"error": "OAuth client not found. Check your APP_ID and CERT_ID in .env file. See /setup for help."}), 401
                except:
                    pass
                return jsonify({"error": "Token expired or invalid. Click 'Get OAuth Token' button or run 'python refresh_token.py' to refresh, or check your .env credentials."}), 401
            else:
                print(f"[DEBUG] Shipping policy API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[DEBUG] Error fetching shipping policies: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                return jsonify({"error": "Token expired or invalid. Run 'python refresh_token.py' to refresh."}), 401
        
        # Get return policies
        try:
            resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
            if resp.status_code == 200:
                data = resp.json()
                policies['returns'] = [{"id": p.get('returnPolicyId'), "name": p.get('name'), "accepted": p.get('returnsAccepted')} 
                                       for p in data.get('returnPolicies', [])]
            elif resp.status_code == 401:
                error_text = resp.text[:500]
                print(f"[DEBUG] Return policy API returned 401 (Unauthorized)")
                print(f"[DEBUG] Response: {error_text}")
                # Check for specific error types
                try:
                    error_json = resp.json()
                    if 'unauthorized_client' in str(error_json).lower() or 'oauth client was not found' in str(error_json).lower():
                        return jsonify({"error": "OAuth client not found. Check your APP_ID and CERT_ID in .env file. See /setup for help."}), 401
                except:
                    pass
                return jsonify({"error": "Token expired or invalid. Click 'Get OAuth Token' button or run 'python refresh_token.py' to refresh, or check your .env credentials."}), 401
            else:
                print(f"[DEBUG] Return policy API returned status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[DEBUG] Error fetching return policies: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                return jsonify({"error": "Token expired or invalid. Run 'python refresh_token.py' to refresh."}), 401
        
        return jsonify(policies)
    except Exception as e:
        print(f"[DEBUG] Error in get_policies: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/fetch-checklist', methods=['POST'])
@require_subscription
def fetch_checklist():
    """Fetch checklist from URL."""
    # FORCE OUTPUT IMMEDIATELY - THIS SHOULD APPEAR FIRST
    import sys
    print("\n" + "!"*60)
    print("[APP] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("[APP] FETCH CHECKLIST ENDPOINT CALLED!")
    print("[APP] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    sys.stdout.flush()
    
    data = request.json
    url = data.get('url', '')
    checklist_type = data.get('type', 'base')
    default_price = float(data.get('defaultPrice', 1.00))
    default_qty = int(data.get('defaultQty', 0))
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        # Get UI version from headers for debugging
        ui_version = request.headers.get('X-UI-Version', 'unknown')
        print(f"[APP] ========================================")
        print(f"[APP] API ENDPOINT CALLED")
        print(f"[APP] Server Version: {VERSION}")
        print(f"[APP] UI Version: {ui_version}")
        print(f"[APP] Fetching checklist - type: '{checklist_type}', URL: {url}")
        print(f"[APP] ========================================")
        
        fetcher = CardChecklistFetcher(source='beckett')
        print(f"[APP] ========================================")
        print(f"[APP] ABOUT TO CALL PARSER")
        print(f"[APP] URL: {url}")
        print(f"[APP] Checklist type: {checklist_type}")
        print(f"[APP] Fetcher object: {fetcher}")
        print(f"[APP] ========================================")
        print(f"[APP] ========================================")
        print(f"[APP] ABOUT TO CALL PARSER")
        print(f"[APP] URL: {url}")
        print(f"[APP] Checklist type: {checklist_type}")
        print(f"[APP] ========================================")
        sys.stdout.flush()
        
        result = fetcher.fetch_from_beckett_url(url, checklist_type=checklist_type)
        
        print(f"[APP] ========================================")
        print(f"[APP] PARSER RETURNED!")
        print(f"[APP] Result type: {type(result)}")
        print(f"[APP] Result is tuple: {isinstance(result, tuple)}")
        print(f"[APP] ========================================")
        sys.stdout.flush()
        
        # Handle both old format (just cards) and new format (cards, description)
        if isinstance(result, tuple):
            cards, extracted_description = result
            print(f"[APP] Unpacked tuple - cards: {len(cards) if cards else 0}, description: {len(extracted_description) if extracted_description else 0} chars")
        else:
            cards = result
            extracted_description = None
            print(f"[APP] Result is not tuple - using as cards directly")
        
        print(f"[APP] ========================================")
        print(f"[APP] STEP 1: After unpacking (BEFORE ANY PROCESSING)")
        print(f"[APP] Cards type: {type(cards)}")
        print(f"[APP] Cards length: {len(cards) if cards else 0}")
        print(f"[APP] Checklist type: '{checklist_type}'")
        sys.stdout.flush()
        
        # Simple logging - no restrictive validation
        if cards and len(cards) > 0:
            has_prefix = any('-' in str(c.get('number', '')) for c in cards)
            print(f"[APP] ========================================")
            print(f"[APP] PARSER RETURNED {len(cards)} CARDS")
            print(f"[APP] Format: {'PREFIXED' if has_prefix else 'PLAIN NUMBERS'}")
            print(f"[APP] First card: {cards[0]['number']} {cards[0]['name']}")
            print(f"[APP] Last card: {cards[-1]['number']} {cards[-1]['name']}")
            print(f"[APP] ========================================")
        else:
            print(f"[APP] WARNING: No cards returned from parser!")
        print(f"[APP] ========================================")
        sys.stdout.flush()
        
        # Simple logging - no restrictive validation
        if checklist_type == 'base':
            if not cards:
                print(f"[APP] No cards returned for base type")
            else:
                card_count = len(cards)
                has_prefix = any('-' in str(c.get('number', '')) for c in cards)
                print(f"[APP] Base cards: {card_count} ({'PREFIXED' if has_prefix else 'PLAIN NUMBERS'})")
        
        if not cards:
            return jsonify({"error": "No cards found. Check the URL and try again."}), 404
        
        print(f"[APP] ========================================")
        print(f"[APP] STEP 2: Before sorting")
        print(f"[APP] Cards count: {len(cards) if cards else 0}")
        print(f"[APP] Checklist type: '{checklist_type}'")
        if cards and len(cards) > 0:
            print(f"[APP] First 5 cards before sorting:")
            for i, c in enumerate(cards[:5]):
                print(f"[APP]   {i+1}. {c.get('number')} {c.get('name')}")
        print(f"[APP] ========================================")
        sys.stdout.flush()
        
        # Sort cards - for inserts, sort by prefix first, then number
        # For other types, sort by number first
        def sort_card_key(card):
            num = str(card.get('number', ''))
            if not num:
                return (999, '', '')
            # Extract numeric part for sorting
            try:
                if '-' in num:
                    # Prefixed format: "BD-1", "FD-1", "A-1", etc.
                    parts = num.split('-', 1)
                    prefix = parts[0] if len(parts) > 1 else ''
                    num_part = parts[-1] if len(parts) > 1 else parts[0]
                    
                    # For inserts, sort by prefix order first, then number
                    if checklist_type == 'inserts':
                        # Define prefix order: FD-, PP-, A-, BIA-, BDN-, BS-, C-, 79D-
                        prefix_order = {
                            'FD': 1,   # Final Draft
                            'PP': 2,   # Prized Prospects
                            'A': 3,    # Axis
                            'BIA': 4,  # Bowman In Action
                            'BDN': 5,  # Bowman Draft Night
                            'BS': 6,   # Bowman Spotlights
                            'C': 7,    # Crystallized
                            '79D': 8,  # Dream Draft Pick
                        }
                        prefix_ord = prefix_order.get(prefix, 999)
                        # Extract numeric part (handle cases like "79D-DM")
                        import re
                        num_match = re.search(r'\d+', num_part)
                        if num_match:
                            num_val = int(num_match.group())
                        else:
                            num_val = 0  # Special format like "79D-DM"
                        # Return tuple: (prefix_order, number)
                        sort_key = (prefix_ord, num_val)
                        if len(cards) <= 10:  # Debug for small sets
                            print(f"[APP] [SORT] Card {num}: prefix='{prefix}', prefix_ord={prefix_ord}, num_val={num_val}, sort_key={sort_key}")
                        return sort_key
                    elif checklist_type == 'autographs':
                        # For autographs, sort alphabetically by the full card number
                        # Examples: CPA-AE, DPPBA-EW, BIA-BC - sort alphabetically
                        return (0, num)  # Use 0 as first sort key, then alphabetical
                    else:
                        # For base cards with prefixes (BD-1, BDC-1), sort by number first, then prefix
                        return (int(num_part), prefix, num)
                elif num.isdigit():
                    # Plain number format: "1", "2", etc.
                    return (int(num), '', num)
                else:
                    # Try to extract first number
                    import re
                    match = re.search(r'\d+', num)
                    if match:
                        return (int(match.group()), '', num)
                    return (999, '', num)
            except:
                return (999, '', num)
        
        cards = sorted(cards, key=sort_card_key)
        
        print(f"[APP] ========================================")
        print(f"[APP] STEP 3: After sorting")
        print(f"[APP] Cards count: {len(cards) if cards else 0}")
        print(f"[APP] Checklist type: '{checklist_type}'")
        if cards and len(cards) > 0:
            print(f"[APP] First 10 cards after sorting:")
            for i, c in enumerate(cards[:10]):
                print(f"[APP]   {i+1}. {c.get('number')} {c.get('name')}")
        print(f"[APP] ========================================")
        sys.stdout.flush()
        
        formatted_cards = []
        parallel_types = []  # For parallels, store available types
        
        print(f"[APP] ========================================")
        print(f"[APP] STEP 4: Starting to format cards")
        print(f"[APP] Cards to format: {len(cards) if cards else 0}")
        print(f"[APP] ========================================")
        
        for i, card in enumerate(cards):
            card_data = {
                "number": str(card.get('number', '')),
                "name": card.get('name', ''),
                "team": card.get('team', ''),
                "price": default_price,
                "quantity": default_qty,  # Set to 0 by default
                "imageUrl": card.get('image_url', '')
            }
            
            # For parallels/#'ed, include parallel type info
            if checklist_type in ['parallels', 'numbered']:
                # Collect parallel types from cards (they all have the same list)
                # Only update if we haven't collected them yet
                if not parallel_types and card.get('parallel_types'):
                    parallel_types = card.get('parallel_types', [])
                    print(f"[APP] Collected {len(parallel_types)} parallel types from cards")
                if card.get('parallel_type'):
                    card_data['parallelType'] = card.get('parallel_type', '')
                if card.get('numbering'):
                    card_data['numbering'] = card.get('numbering', '')
            
            formatted_cards.append(card_data)
            
            # Log every 50th card to track progress
            if (i + 1) % 50 == 0:
                print(f"[APP] Formatted {i + 1} cards so far...")
        
        print(f"[APP] ========================================")
        print(f"[APP] STEP 5: After formatting")
        print(f"[APP] Formatted cards count: {len(formatted_cards)}")
        print(f"[APP] ========================================")
        
        # Try to extract set name from description if available
        set_name = ""
        if extracted_description:
            # Try to extract set name from description (look for <strong> tags)
            import re
            strong_match = re.search(r'<strong>(.*?)</strong>', extracted_description)
            if strong_match:
                set_name = strong_match.group(1).strip()
                print(f"[INFO] Extracted set name from description: {set_name}")
        
        if not set_name:
            if 'cardsmithsbreaks.com' in url:
                set_name = "Cardsmiths Breaks Set"
            elif 'beckett.com' in url:
                # Try to extract set name from URL
                import re
                url_match = re.search(r'/([^/]+-cards?)/?$', url)
                if url_match:
                    set_name = url_match.group(1).replace('-cards', '').replace('-card', '').replace('-', ' ').title()
                else:
                    set_name = "Beckett Checklist Set"
        
        # Simple logging - no restrictive validation
        formatted_count = len(formatted_cards)
        has_prefix = any('-' in str(c.get('number', '')) for c in formatted_cards) if formatted_cards else False
        print(f"[APP] ========================================")
        print(f"[APP] BEFORE RETURNING:")
        print(f"[APP] Checklist type: {checklist_type}")
        print(f"[APP] Formatted cards count: {formatted_count}")
        print(f"[APP] Format: {'PREFIXED' if has_prefix else 'PLAIN NUMBERS'}")
        print(f"[APP] ========================================")
        
        response_data = {
            "success": True,
            "cards": formatted_cards,
            "count": formatted_count,
            "setName": set_name,
            "source": "beckett" if 'beckett.com' in url else ("cardsmiths" if 'cardsmithsbreaks.com' in url else "universal"),
            "checklistType": checklist_type
        }
        
        # For parallels/#'ed, include the list of available parallel types
        if checklist_type in ['parallels', 'numbered']:
            # Get parallel types from cards (they all have the same list stored in parallel_types)
            # If we didn't get them from cards, try to extract them
            if not parallel_types and formatted_cards:
                # Try to get from first card
                first_card = formatted_cards[0] if formatted_cards else None
                if first_card and hasattr(first_card, 'get') and first_card.get('parallel_types'):
                    parallel_types = first_card.get('parallel_types', [])
            
            if parallel_types:
                response_data['parallelTypes'] = parallel_types
                print(f"[APP] Including {len(parallel_types)} parallel types in response")
            else:
                print(f"[APP] WARNING: No parallel types found for {checklist_type}")
        
        # No restrictive validation - trust the parser
        
        # Add version to response to prevent caching - ALWAYS set these
        # CRITICAL: Set version/timestamp IMMEDIATELY - cannot be missing
        response_data['version'] = VERSION
        response_data['timestamp'] = __import__('datetime').datetime.now().isoformat()
        response_data['server_version'] = VERSION
        
        # Validate version is set
        if not response_data.get('version'):
            print(f"[APP] ERROR: Version not set! Forcing to {VERSION}")
            response_data['version'] = VERSION
        
        print(f"[APP] ========================================")
        print(f"[APP] FINAL RESPONSE:")
        print(f"[APP] Success: {response_data['success']}")
        print(f"[APP] Count: {response_data['count']}")
        print(f"[APP] Source: {response_data['source']}")
        print(f"[APP] Version: {response_data['version']}")
        print(f"[APP] ========================================")
        
        # For parallels, include available parallel types
        if checklist_type == 'parallels' and parallel_types:
            response_data["parallelTypes"] = parallel_types
            print(f"[INFO] Found {len(parallel_types)} parallel types: {', '.join(parallel_types[:10])}...")
        
        # Include extracted description if available
        if extracted_description:
            response_data["description"] = extracted_description
            print(f"[INFO] ✅ Extracted description from checklist page (length: {len(extracted_description)})")
            print(f"[INFO] Description preview: {extracted_description[:150]}...")
        else:
            print(f"[INFO] ⚠️ No description extracted from page, will use default")
        
        # FINAL FINAL CHECK: Make absolutely sure version is set
        if 'version' not in response_data or not response_data['version']:
            response_data['version'] = VERSION
        if 'timestamp' not in response_data or not response_data['timestamp']:
            response_data['timestamp'] = __import__('datetime').datetime.now().isoformat()
        if 'server_version' not in response_data or not response_data['server_version']:
            response_data['server_version'] = VERSION
        
        print(f"[APP] ========================================")
        print(f"[APP] ABOUT TO RETURN JSON RESPONSE")
        print(f"[APP] Version in response: {response_data.get('version')}")
        print(f"[APP] Count in response: {response_data.get('count')}")
        print(f"[APP] Success in response: {response_data.get('success')}")
        print(f"[APP] ========================================")
        
        return jsonify(response_data)
    except Exception as e:
        print(f"[APP] ========================================")
        print(f"[APP] EXCEPTION CAUGHT!")
        print(f"[APP] Error type: {type(e).__name__}")
        print(f"[APP] Error message: {str(e)}")
        print(f"[APP] ========================================")
        import traceback
        traceback.print_exc()
        print(f"[APP] ========================================")
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "success": False,
            "cards": [],
            "count": 0,
            "version": VERSION,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "server_version": VERSION
        }), 500

@app.route('/api/list', methods=['POST'])
@require_subscription
def create_listing():
    """Create and publish a listing using eBayListingManager."""
    data = request.json
    
    try:
        set_name = data.get('setName', 'Card Set')
        description = data.get('description', '')
        cards = data.get('cards', [])
        image_url = data.get('imageUrl', '')  # No default image - only use if provided
        payment_id = data.get('paymentPolicyId', '').strip() or None  # Default to None (Managed by eBay)
        shipping_id = data.get('shippingPolicyId')
        return_id = data.get('returnPolicyId')
        publish = True  # Always publish live - drafts not supported
        
        # Check environment - CRITICAL: Force reload .env
        from config import Config
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Force reload .env file
        config = Config()
        env_name = config.EBAY_ENVIRONMENT.upper()
        api_url = config.ebay_api_url
        print(f"[INFO] ========== ENVIRONMENT CHECK ==========")
        print(f"[INFO] Environment from .env: {env_name}")
        print(f"[INFO] API URL: {api_url}")
        if env_name != 'PRODUCTION':
            print(f"[INFO] ⚠️ WARNING: Not using PRODUCTION!")
            print(f"[INFO] ⚠️ Check your .env file - EBAY_ENVIRONMENT should be 'production'")
        else:
            print(f"[INFO] ✅ Using PRODUCTION environment")
        print(f"[INFO] ======================================")
        
        # PRODUCTION SAFETY: Warn if trying to publish live in production
        # Always publish live - drafts not supported
        
        if not cards:
            return jsonify({"error": "No cards provided"}), 400
        
        # Filter out cards with quantity 0
        valid_cards = [c for c in cards if int(c.get('quantity', 0)) > 0]
        if not valid_cards:
            return jsonify({"error": "No cards with quantity > 0. Cards with quantity 0 are excluded from listings."}), 400
        
        # Prepare cards for eBayListingManager
        listing_cards = []
        prices = {}
        for card in valid_cards:
            card_data = {
                'name': card.get('name', ''),
                'number': str(card.get('number', '')),
                'quantity': int(card.get('quantity', 1)),
                'team': card.get('team', ''),
                'image_url': card.get('imageUrl', image_url)
            }
            listing_cards.append(card_data)
            price = float(card.get('price', 1.00))
            # Use card name as key for pricing
            if card_data['name']:
                prices[card_data['name']] = price
        
        # Use base price if all cards have same price, otherwise use dict
        if len(set(prices.values())) == 1:
            base_price = list(prices.values())[0]
        else:
            base_price = prices
        
        # Create listing manager with current user's token
        token = _get_effective_token()
        listing_manager = eBayListingManager(token_override=token)
        
        # Override policies if provided
        if shipping_id:
            listing_manager.policies['fulfillment_policy_id'] = shipping_id
        if payment_id:
            listing_manager.policies['payment_policy_id'] = payment_id
        if return_id:
            listing_manager.policies['return_policy_id'] = return_id
        
        print(f"[INFO] Creating listing: {set_name}")
        print(f"[INFO] Cards: {len(listing_cards)} (filtered from {len(cards)})")
        print(f"[INFO] Publish: {publish} (always live)")
        
        # Create the listing using the proper manager
        result = listing_manager.create_variation_listing(
            cards=listing_cards,
            title=set_name[:80],  # eBay limit
            description=description or f"<p><strong>{set_name}</strong></p><p>Select your card from the dropdown menu.</p>",
            category_id="261328",  # Trading Cards
            price=base_price,
            quantity=1,  # Per-card quantity is in card data
            condition="Near Mint",
            images=[image_url] if image_url else None,
            publish=publish,
            fulfillment_policy_id=shipping_id,
            use_base_cards_policy=None,
            schedule_draft=False,  # Removed - not supported
            schedule_hours=0  # Not used
        )
        
        # CRITICAL: Log the result to see what's happening
        print(f"[CRITICAL] ========== LISTING CREATION RESULT ==========")
        print(f"[CRITICAL] result.get('success'): {result.get('success')}")
        print(f"[CRITICAL] result.get('error'): {result.get('error')}")
        print(f"[CRITICAL] result.get('group_key'): {result.get('group_key')}")
        print(f"[CRITICAL] result.get('listing_id'): {result.get('listing_id')}")
        print(f"[CRITICAL] result.get('scheduled'): {result.get('scheduled')}")
        print(f"[CRITICAL] result.get('status'): {result.get('status')}")
        print(f"[CRITICAL] ============================================")
        
        if result.get('success'):
            group_key = result.get('group_key') or result.get('groupKey')
            
            if not group_key:
                print(f"[ERROR] No group_key in result! Result keys: {list(result.keys())}")
                return jsonify({
                    "success": False,
                    "error": "Listing creation returned success but no group_key. Check server logs for details.",
                    "details": str(result)
                }), 500
            
            # Verify the draft was created by checking the group
            if not publish:
                print(f"[INFO] Verifying draft creation for group: {group_key}")
                try:
                    verify_result = listing_manager.api_client.get_inventory_item_group(group_key)
                    if verify_result.get('success'):
                        print(f"[INFO] ✓ Group verified: {group_key}")
                        group_data = verify_result.get('data', {})
                        variant_skus = group_data.get('variantSKUs', [])
                        
                        # Check if offers exist
                        if variant_skus:
                            offer_count = 0
                            for sku in variant_skus[:3]:  # Check first 3 offers
                                offer_result = listing_manager.api_client.get_offer_by_sku(sku)
                                if offer_result.get('success'):
                                    offer = offer_result.get('offer', {})
                                    offer_id = offer_result.get('offer', {}).get('offerId')
                                    print(f"[INFO] ✓ Offer verified: {sku} (ID: {offer_id})")
                                    offer_count += 1
                            print(f"[INFO] ✓ Verified {offer_count}/{min(3, len(variant_skus))} offers created")
                            
                            # Check if any offers have listingId (published) or are drafts
                            has_listing_id = False
                            for sku in variant_skus[:3]:
                                offer_result = listing_manager.api_client.get_offer_by_sku(sku)
                                if offer_result.get('success'):
                                    offer = offer_result.get('offer', {})
                                    listing_id = offer.get('listingId')
                                    if listing_id:
                                        has_listing_id = True
                                        print(f"[INFO] ✓ Offer has listingId: {listing_id} (published)")
                                        break
                            
                            if not has_listing_id:
                                print(f"[INFO] ⚠️ Offers created but not published (draft state)")
                                print(f"[INFO] ⚠️ Drafts may not appear in Seller Hub 'Drafts' section")
                                print(f"[INFO] ⚠️ Check 'Unsold' or 'Active Listings' tabs instead")
                except Exception as e:
                    print(f"[WARNING] Could not verify draft: {e}")
                    import traceback
                    traceback.print_exc()
            
            # DEBUG: Log what we received from ebay_listing.py
            print(f"[DEBUG] ========== RESPONSE FROM ebay_listing.py ==========")
            print(f"[DEBUG] result.get('scheduled'): {result.get('scheduled')}")
            print(f"[DEBUG] result.get('status'): {result.get('status')}")
            print(f"[DEBUG] result.get('published'): {result.get('published')}")
            print(f"[DEBUG] publish: {publish} (always live)")
            print(f"[DEBUG] result.get('ebay_url'): {result.get('ebay_url')}")
            print(f"[DEBUG] result.get('seller_hub_scheduled'): {result.get('seller_hub_scheduled')}")
            print(f"[DEBUG] ===================================================")
            
            # Determine status - CHECK SCHEDULED FIRST before published
            if result.get('scheduled') or (schedule_draft and publish):
                final_status = "scheduled"
                print(f"[DEBUG] ✅ Status set to 'scheduled'")
            elif publish:
                final_status = "published"
                print(f"[DEBUG] ⚠️ Status set to 'published' (not scheduled)")
            else:
                final_status = "draft"
                print(f"[DEBUG] Status set to 'draft'")
            
            # Determine base URL for Seller Hub links
            base_url = "https://www.ebay.com" if config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
            
            # Format response for frontend
            response_data = {
                "success": True,
                "groupKey": group_key,
                "setName": set_name,
                "cardsCreated": len(listing_cards),
                "status": final_status,  # Use determined status
                "listingId": result.get('listing_id') or result.get('listingId'),
                "listingUrl": result.get('ebay_url', '') or f"{base_url}/sh/account/listings",
                "sellerHubUrl": result.get('seller_hub_url', f"{base_url}/sh/landing"),
                "sellerHubDrafts": result.get('seller_hub_drafts', f"{base_url}/sh/account/listings?status=DRAFT"),
                "sellerHubActive": result.get('seller_hub_active', f"{base_url}/sh/account/listings?status=ACTIVE"),
                "sellerHubUnsold": result.get('seller_hub_unsold', f"{base_url}/sh/account/listings?status=UNSOLD"),
                "sellerHubScheduled": result.get('seller_hub_scheduled', f"{base_url}/sh/lst/scheduled"),
                "message": result.get('message', 'Listing created successfully'),
                "skus": result.get('skus', [])[:5],  # Include first few SKUs for reference
                # Add listing status information if available
                "listingStatus": result.get('listingStatus'),
                "sellerHubLocation": result.get('sellerHubLocation'),
                "whereToFind": result.get('whereToFind'),
                "statusMessage": result.get('statusMessage')
            }
            
            # Ensure scheduled field is set if status is scheduled
            if final_status == "scheduled":
                response_data["scheduled"] = True
                print(f"[DEBUG] ✅ Set response_data['scheduled'] = True")
            
            print(f"[DEBUG] Final response_data['status']: {response_data['status']}")
            print(f"[DEBUG] Final response_data['sellerHubScheduled']: {response_data.get('sellerHubScheduled')}")
            
            # Use the status and data from the result
            # Note: We already set scheduled=True above if final_status == "scheduled"
            if result.get('scheduled') or final_status == "scheduled":
                # Don't override status if already set correctly
                if final_status != "scheduled":
                    response_data["status"] = "scheduled"
                response_data.update({
                    "scheduled": True,  # Ensure this is always True for scheduled
                    "sellerHubScheduled": result.get('seller_hub_scheduled') or result.get('sellerHubScheduled', f"{base_url}/sh/lst/scheduled"),
                    "scheduleHours": result.get('scheduleHours', 0),
                    "listingStartDate": result.get('listingStartDate'),
                    "verificationStatus": result.get('verificationStatus', 'unknown'),
                    "verificationDetails": result.get('verificationDetails', {})
                })
                print(f"[DEBUG] ✅ Updated response_data with scheduled info")
                
                # Add verification message if available
                if result.get('verificationStatus') == 'success':
                    response_data["verificationMessage"] = f"✅ Verified: All offers have listingStartDate. Listing should appear in 'Scheduled Listings' section."
                elif result.get('verificationStatus') == 'partial':
                    response_data["verificationMessage"] = f"⚠️ Partial: Some offers have listingStartDate. Check Seller Hub to confirm location."
                elif result.get('verificationStatus') == 'warning':
                    response_data["verificationMessage"] = f"⚠️ Warning: No offers have listingStartDate. Listing will go live immediately."
                
                # Add comprehensive check results if available
                if result.get('comprehensiveCheck'):
                    comp_check = result.get('comprehensiveCheck', {})
                    response_data["comprehensiveCheck"] = comp_check
                    response_data["whereToFindListing"] = comp_check.get('recommendedLocation', 'Unknown')
                    response_data["sellerHubDirectUrl"] = comp_check.get('sellerHubUrl', '')
                    
                    if comp_check.get('offersWithStartDate', 0) > 0:
                        response_data["finalStatus"] = "scheduled"
                        response_data["finalMessage"] = f"✅ Listing found with start dates! It should appear in 'Scheduled Listings' in Seller Hub."
                    elif comp_check.get('offersPublished', 0) > 0:
                        response_data["finalStatus"] = "active"
                        response_data["finalMessage"] = f"⚠️ Listing is published but missing start dates. It may be in 'Active Listings' instead of 'Scheduled'."
                    else:
                        response_data["finalStatus"] = "not_found"
                        response_data["finalMessage"] = f"⚠️ Listing not found in API yet. It may take a few minutes to appear. Check Seller Hub."
                
                # Enhanced verification info is already in result from ebay_listing.py
                print(f"[INFO] Scheduled listing created with verification status: {result.get('verificationStatus', 'unknown')}")
            elif not publish:
                response_data["draft"] = True
                response_data["message"] = f"Draft created! Group: {group_key}"
                
                # Add verification details if available
                if result.get('verificationDetails'):
                    verification = result.get('verificationDetails', {})
                    offers_draft = verification.get('offersDraft', 0)
                    offers_published = verification.get('offersPublished', 0)
                    
                    if offers_published > 0:
                        response_data["note"] = f"⚠️ WARNING: {offers_published} offer(s) were published (have listingId). This should not happen for drafts."
                        response_data["verificationStatus"] = "warning"
                    elif offers_draft > 0:
                        response_data["note"] = f"⚠️ IMPORTANT: {offers_draft} draft offer(s) created, but they may NOT be visible in Seller Hub 'Drafts' section. This is a known eBay API limitation. Use 'Save as Scheduled Draft' instead."
                        response_data["verificationStatus"] = "draft_created_but_may_not_be_visible"
                    else:
                        response_data["note"] = "Draft created. Verification status unknown."
                        response_data["verificationStatus"] = "unknown"
                    
                    response_data["verificationDetails"] = verification
                else:
                    response_data["note"] = "IMPORTANT: Draft listings created via Inventory API may not appear in the 'Drafts' section. Check 'Unsold' or 'Active Listings' tabs. It may take 1-2 minutes to appear."
                    response_data["verificationStatus"] = "unknown"
                
                response_data["instructions"] = [
                    "1. Drafts created via Inventory API are often NOT visible in Seller Hub 'Drafts'",
                    "2. To get editable listings that appear in Seller Hub, use 'Save as Scheduled Draft' button",
                    "3. Scheduled drafts appear in Seller Hub 'Scheduled Listings' where you can edit them",
                    f"4. Group Key: {group_key}",
                    "5. You can publish this draft later using the group key via API",
                    "6. Check verification details below to see offer status"
                ]
                response_data["troubleshooting"] = "If the draft doesn't appear, this is expected - eBay Inventory API drafts are often not visible. Use 'Save as Scheduled Draft' instead to get listings that appear in Seller Hub."
            
            return jsonify(response_data)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"[ERROR] Listing creation failed: {error_msg}")
            print(f"[ERROR] Error details: {result.get('details', '')}")
            print(f"[ERROR] Group key: {result.get('group_key', 'N/A')}")
            
            # Check for specific errors that need special handling
            if '25007' in str(error_msg) or 'shipping service' in str(error_msg).lower():
                print(f"[ERROR] Error 25007 detected - Fulfillment policy issue")
                return jsonify({
                    "success": False,
                    "error": error_msg,
                    "error_code": "25007",
                    "group_key": result.get('group_key'),
                    "details": result.get('details', ''),
                    "action_required": result.get('action_required', 'Please check your fulfillment policy in eBay Seller Hub and add shipping services.'),
                    "note": result.get('note', 'Your fulfillment policy needs shipping services configured.')
                }), 400
            
            # Check if error is due to HTML response (auth issue)
            if result.get('is_html'):
                error_msg = "Authentication Error: eBay returned an HTML page instead of JSON.\n\n"
                error_msg += "This usually means your access token is expired or invalid.\n"
                error_msg += "Please:\n"
                error_msg += "1. Go to Step 2 (Login) in the UI\n"
                error_msg += "2. Click 'Refresh Token' or 'Get OAuth Token'\n"
                error_msg += "3. Try creating the listing again\n\n"
                error_msg += f"Original error: {result.get('error', 'Unknown error')}"
            
            return jsonify({
                "success": False,
                "error": error_msg,
                "details": result.get('details', ''),
                "is_html": result.get('is_html', False)
            }), 400
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decode error in create_listing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Invalid JSON in request or response: {str(e)}"}), 400
    except Exception as e:
        print(f"[ERROR] Exception in create_listing: {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Full traceback:\n{error_trace}")
        
        # Check if it's the datetime OSError and provide more specific help
        error_msg = str(e)
        if "Errno 22" in error_msg or "Invalid argument" in error_msg:
            error_msg = f"Datetime formatting error (Windows compatibility issue). Please restart the Flask server to apply the fix. Original error: {error_msg}"
        
        # Return a proper error response instead of crashing
        error_details = {
            "success": False,
            "error": f"Server error: {error_msg}",
            "error_type": type(e).__name__,
            "message": "An error occurred while creating the listing. Please check your input and try again.",
            "traceback": error_trace
        }
        print(f"[ERROR] Returning error: {error_details}")
        return jsonify(error_details), 500

# =============================================================================
# ADMIN ROUTES (OWNER ONLY)
# =============================================================================

def require_admin(f):
    """Decorator to require admin email and password."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = session.get('user_email', '')
        admin_authenticated = session.get('admin_authenticated', False)
        
        if email.lower() != OWNER_EMAIL.lower():
            return redirect('/')
        
        if not admin_authenticated:
            return redirect('/admin/login')
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@require_admin
def admin():
    """Admin panel."""
    subs = load_subscriptions()
    payments = load_payments()
    
    # Calculate expiring soon (within 7 days)
    from datetime import datetime, timedelta
    expiring_soon = []
    for email, sub in subs.items():
        if sub.get('status') == 'active':
            expires = sub.get('expires', '')
            if expires:
                try:
                    expires_date = datetime.strptime(expires, '%Y-%m-%d')
                    if datetime.now() <= expires_date <= datetime.now() + timedelta(days=7):
                        expiring_soon.append({
                            'email': email,
                            'expires': expires,
                            'days_left': (expires_date - datetime.now()).days
                        })
                except:
                    pass
    
    return render_template('admin.html', 
                          subscriptions=subs, 
                          payments=payments,
                          expiring_soon=expiring_soon)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    email = session.get('user_email', '')
    if email.lower() != OWNER_EMAIL.lower():
        return redirect('/')
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash == ADMIN_PASSWORD_HASH:
            session['admin_authenticated'] = True
            return redirect('/admin')
        else:
            return render_template('admin_login.html', error='Invalid password')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_authenticated', None)
    return redirect('/')

@app.route('/admin/add-subscription', methods=['POST'])
@require_admin
def add_subscription():
    """Add a subscription."""
    email = request.json.get('email', '').strip().lower()
    days = int(request.json.get('days', 30))
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    subs = load_subscriptions()
    from datetime import datetime, timedelta
    expires = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    subs[email] = {
        "status": "active",
        "expires": expires,
        "last_payment": datetime.now().strftime('%Y-%m-%d'),
        "total_payments": subs.get(email, {}).get('total_payments', 0)
    }
    
    save_subscriptions(subs)
    return jsonify({"success": True, "message": f"Added subscription for {email} until {expires}"})

@app.route('/admin/remove-subscription', methods=['POST'])
@require_admin
def remove_subscription():
    """Remove a subscription."""
    email = request.json.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    subs = load_subscriptions()
    if email in subs:
        del subs[email]
        save_subscriptions(subs)
        return jsonify({"success": True, "message": f"Removed subscription for {email}"})
    else:
        return jsonify({"error": "Subscription not found"}), 404

@app.route('/admin/record-payment', methods=['POST'])
@require_admin
def record_payment():
    """Record a payment."""
    data = request.json
    email = data.get('email', '').strip().lower()
    transaction_id = data.get('transaction_id', '').strip()
    amount = data.get('amount', SUBSCRIPTION_PRICE_MONTHLY)
    notes = data.get('notes', '')
    
    if not email or not transaction_id:
        return jsonify({"error": "Email and transaction ID required"}), 400
    
    # Record payment
    payments = load_payments()
    from datetime import datetime
    payments.append({
        "email": email,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "amount": amount,
        "transaction_id": transaction_id,
        "notes": notes
    })
    save_payments(payments)
    
    # Extend subscription
    subs = load_subscriptions()
    if email in subs:
        from datetime import timedelta
        current_expires = subs[email].get('expires', '')
        if current_expires:
            try:
                expires_date = datetime.strptime(current_expires, '%Y-%m-%d')
                if expires_date > datetime.now():
                    new_expires = expires_date + timedelta(days=30)
                else:
                    new_expires = datetime.now() + timedelta(days=30)
            except:
                new_expires = datetime.now() + timedelta(days=30)
        else:
            new_expires = datetime.now() + timedelta(days=30)
        
        subs[email]['expires'] = new_expires.strftime('%Y-%m-%d')
        subs[email]['status'] = 'active'
        subs[email]['last_payment'] = datetime.now().strftime('%Y-%m-%d')
        subs[email]['total_payments'] = subs[email].get('total_payments', 0) + 1
    else:
        from datetime import timedelta
        new_expires = datetime.now() + timedelta(days=30)
        subs[email] = {
            "status": "active",
            "expires": new_expires.strftime('%Y-%m-%d'),
            "last_payment": datetime.now().strftime('%Y-%m-%d'),
            "total_payments": 1
        }
    
    save_subscriptions(subs)
    
    return jsonify({
        "success": True,
        "message": f"Payment recorded and subscription extended until {subs[email]['expires']}"
    })

@app.route('/admin/renew-subscription', methods=['POST'])
@require_admin
def renew_subscription():
    """Renew a subscription by 30 days."""
    email = request.json.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    subs = load_subscriptions()
    if email in subs:
        from datetime import datetime, timedelta
        current_expires = subs[email].get('expires', '')
        if current_expires:
            try:
                expires_date = datetime.strptime(current_expires, '%Y-%m-%d')
                if expires_date > datetime.now():
                    new_expires = expires_date + timedelta(days=30)
                else:
                    new_expires = datetime.now() + timedelta(days=30)
            except:
                new_expires = datetime.now() + timedelta(days=30)
        else:
            new_expires = datetime.now() + timedelta(days=30)
        
        subs[email]['expires'] = new_expires.strftime('%Y-%m-%d')
        subs[email]['status'] = 'active'
        subs[email]['last_renewal'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_subscriptions(subs)
        
        return jsonify({"success": True, "message": f"Renewed {email} until {new_expires}"})
    else:
        return jsonify({"error": "Subscription not found"}), 404

# =============================================================================
# TOKEN UPDATE API
# =============================================================================

@app.route('/api/update-token', methods=['POST'])
@require_subscription
def update_token():
    """Update eBay token. Saves to per-user storage (works on Render). Also updates .env when running locally."""
    try:
        data = request.json
        token = data.get('token', '').strip()
        email = session.get('user_email', '')
        
        if not token:
            return jsonify({"success": False, "error": "Token is required"}), 400
        if not email:
            return jsonify({"success": False, "error": "You must be logged in to save a token."}), 401
        
        # Detect token type
        is_user_token = token.startswith('v^1.1#')
        token_type = "User Token" if is_user_token else "OAuth Refresh Token"
        
        # ALWAYS save to per-user storage (works on Render, enables each user their own eBay)
        tokens = load_user_tokens()
        tokens[email.lower()] = {
            "token": token,
            "type": token_type,
            "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "is_user_token": is_user_token
        }
        save_user_tokens(tokens)
        print(f"[INFO] Token saved for user {email} (Type: {token_type}) - per-user storage")
        
        # When running locally (not Render), also update .env for backward compatibility
        on_render = os.environ.get('RENDER') == 'true'
        if not on_render and os.path.exists('.env'):
            import re
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
            if is_user_token:
                env_content = re.sub(r'EBAY_PRODUCTION_TOKEN=.*', f'EBAY_PRODUCTION_TOKEN={token}', env_content, flags=re.MULTILINE)
                env_content = re.sub(r'USE_OAUTH=.*', 'USE_OAUTH=false', env_content, flags=re.MULTILINE) if "USE_OAUTH=" in env_content else env_content + "USE_OAUTH=false\n"
            else:
                env_content = re.sub(r'EBAY_REFRESH_TOKEN=.*', f'EBAY_REFRESH_TOKEN={token}', env_content, flags=re.MULTILINE)
                env_content = re.sub(r'USE_OAUTH=.*', 'USE_OAUTH=true', env_content, flags=re.MULTILINE) if "USE_OAUTH=" in env_content else env_content + "USE_OAUTH=true\n"
            env_content = re.sub(r'EBAY_ENVIRONMENT=.*', 'EBAY_ENVIRONMENT=production', env_content, flags=re.MULTILINE) if "EBAY_ENVIRONMENT=" in env_content else env_content + "EBAY_ENVIRONMENT=production\n"
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            from dotenv import load_dotenv
            load_dotenv(override=True)
            print(f"[INFO] .env also updated (local mode)")
        
        return jsonify({
            "success": True,
            "message": f"{token_type} saved successfully! The token is now active - no restart needed.",
            "token_type": token_type
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to update token: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/verify-draft', methods=['POST'])
@require_subscription
def verify_draft():
    """Verify if a draft listing exists."""
    data = request.json
    group_key = data.get('groupKey', '').strip()
    
    if not group_key:
        return jsonify({"error": "Group key required"}), 400
    
    try:
        token = _get_effective_token()
        client = eBayAPIClient(token_override=token)
        client._update_headers()
        
        # Check if group exists
        group_result = client.get_inventory_item_group(group_key)
        if not group_result.get('success'):
            return jsonify({
                "success": False,
                "error": f"Group not found: {group_result.get('error')}",
                "groupKey": group_key
            }), 404
        
        group_data = group_result.get('data', {})
        variant_skus = group_data.get('variantSKUs', [])
        
        # Check offers
        offers_info = []
        published_count = 0
        draft_count = 0
        
        for sku in variant_skus[:5]:  # Check first 5
            offer_result = client.get_offer_by_sku(sku)
            if offer_result.get('success'):
                offer = offer_result.get('offer', {})
                offer_id = offer.get('offerId')
                listing_id = offer.get('listingId')
                status = offer.get('status', 'UNKNOWN')
                
                if listing_id:
                    published_count += 1
                else:
                    draft_count += 1
                
                offers_info.append({
                    "sku": sku,
                    "offerId": offer_id,
                    "listingId": listing_id,
                    "status": status,
                    "published": bool(listing_id)
                })
        
        return jsonify({
            "success": True,
            "groupKey": group_key,
            "groupTitle": group_data.get('title', 'N/A'),
            "totalVariants": len(variant_skus),
            "offersChecked": len(offers_info),
            "publishedOffers": published_count,
            "draftOffers": draft_count,
            "offers": offers_info,
            "message": f"Group exists with {len(variant_skus)} variants. {published_count} published, {draft_count} drafts.",
            "sellerHubUnsold": "https://www.ebay.com/sh/account/listings?status=UNSOLD",
            "sellerHubActive": "https://www.ebay.com/sh/account/listings?status=ACTIVE"
        })
        
    except Exception as e:
        print(f"[ERROR] Verify draft error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Auto-kill old Python processes to ensure fresh start
    import subprocess
    import sys
    import os
    
    print("=" * 60)
    print("eBay Card Listing Tool")
    print(f"Server Version: {VERSION}")
    print("=" * 60)
    print()
    print("[STARTUP] ========================================")
    print("[STARTUP] KILLING ALL PYTHON PROCESSES")
    print("[STARTUP] ========================================")
    
    if sys.platform == 'win32':
        # Method 1: taskkill (most reliable)
        try:
            print("[STARTUP] Method 1: taskkill...")
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                         capture_output=True, timeout=5)
            print("[STARTUP] Method 1 completed")
        except Exception as e:
            print(f"[STARTUP] Method 1 failed: {e}")
        
        # Method 2: PowerShell (backup)
        try:
            print("[STARTUP] Method 2: PowerShell...")
            ps_cmd = 'Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force'
            subprocess.run(['powershell', '-Command', ps_cmd], 
                         capture_output=True, timeout=5)
            print("[STARTUP] Method 2 completed")
        except Exception as e:
            print(f"[STARTUP] Method 2 failed: {e}")
        
        # Wait for termination
        print("[STARTUP] Waiting 3 seconds for processes to terminate...")
        time.sleep(3)
        
        # Final check and alert if multiple processes detected
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                                 capture_output=True, text=True, timeout=3)
            remaining = result.stdout.lower().count('python.exe')
            if remaining > 1:
                print("=" * 60)
                print("[ALERT] ========================================")
                print(f"[ALERT] WARNING: {remaining} Python processes detected!")
                print("[ALERT] Multiple Python processes can cause conflicts!")
                print("[ALERT] This may cause incorrect card counts (e.g., 434 cards)")
                print("[ALERT] ========================================")
                print("=" * 60)
                print()
                # Try one more aggressive kill
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                 capture_output=True, timeout=5)
                    time.sleep(2)
                    print("[STARTUP] Attempted additional kill of Python processes")
                except:
                    pass
            elif remaining == 1:
                print("[STARTUP] SUCCESS: Only 1 Python process (this one) - OK")
            else:
                print("[STARTUP] SUCCESS: All Python processes killed")
        except:
            print("[STARTUP] Could not verify kill status")
    else:
        # Linux/Mac
        try:
            subprocess.run(['pkill', '-9', 'python'], capture_output=True, timeout=5)
            time.sleep(2)
            print("[STARTUP] Killed all Python processes")
        except:
            print("[STARTUP] Process check complete (Unix)")
    
    print("[STARTUP] ========================================")
    print()
    
    print()
    print(f"Owner: {OWNER_EMAIL}")
    print(f"Monthly Subscription: ${SUBSCRIPTION_PRICE_MONTHLY}/month (50% off ${SUBSCRIPTION_PRICE_MONTHLY_ORIGINAL})")
    print(f"Yearly Subscription: ${SUBSCRIPTION_PRICE_YEARLY}/year (50% off ${SUBSCRIPTION_PRICE_YEARLY_ORIGINAL})")
    print()
    print("=" * 60)
    print(f"[SERVER] Starting Flask server on http://localhost:5001")
    print(f"[SERVER] Server Version: {VERSION}")
    print(f"[SERVER] Debug mode: ON")
    print("=" * 60)
    print()
    # Run with better error handling
    # Force stdout/stderr to be unbuffered so logs show immediately
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Check if port 5001 is already in use (prevent multiple instances)
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 5001))
        sock.close()
        if result == 0:
            print("=" * 60)
            print("[ALERT] ========================================")
            print("[ALERT] WARNING: Port 5001 is already in use!")
            print("[ALERT] Another Flask server may be running.")
            print("[ALERT] Multiple servers can cause incorrect results!")
            print("[ALERT] ========================================")
            print("=" * 60)
            print()
            print("[STARTUP] Attempting to kill processes and retry...")
            # Try one more kill
            try:
                subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                             capture_output=True, timeout=5)
                time.sleep(3)
                # Check again
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.settimeout(1)
                result2 = sock2.connect_ex(('127.0.0.1', 5001))
                sock2.close()
                if result2 == 0:
                    print("[STARTUP] Port still in use - exiting")
                    sys.exit(1)
                else:
                    print("[STARTUP] Port cleared - continuing")
            except:
                print("[STARTUP] Could not clear port - exiting")
                sys.exit(1)
    except:
        pass
    
    try:
        # Run with use_reloader=False to prevent double processes
        # threaded=True allows multiple requests
        # use_reloader=False is CRITICAL - prevents Flask from spawning child processes
        app.run(debug=True, port=5001, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"[FATAL ERROR] Flask app crashed: {e}")
        import traceback
        traceback.print_exc()
        print("\n[INFO] Attempting to restart...")
        time.sleep(2)
        app.run(debug=True, port=5001, threaded=True, use_reloader=False)
