"""eBay Card Listing Tool - Main Application
Multi-user support with PayPal subscription
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory, make_response
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
import threading

# Safe UTF-8 stdout - can crash in gunicorn/Render if stdout is not TextIOWrapper
try:
    if hasattr(sys.stdout, 'reconfigure') and callable(getattr(sys.stdout, 'reconfigure')):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception as e:
    print(f"[WARN] Could not reconfigure stdout encoding: {e}", flush=True)

# Background job store (shared across requests with --workers 1)
listing_jobs = {}

# =============================================================================
# VERSION - Auto from VERSION file (written at build: 4.<git rev-list count>)
# =============================================================================
def _load_version():
    try:
        p = os.path.join(os.path.dirname(__file__) or '.', 'VERSION')
        with open(p, 'r') as f:
            return f.read().strip() or "4.019"
    except Exception:
        return "4.019"
VERSION = os.environ.get("VERSION", _load_version())

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# =============================================================================
# GLOBAL ERROR HANDLERS - Prevent crashes
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 - JSON for API, HTML for pages."""
    wants_html = not request.path.startswith('/api/')
    if wants_html:
        return (
            '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Not Found - CardPilot</title></head>'
            '<body style="font-family:sans-serif;background:#0a0a14;color:#fff;padding:40px;text-align:center;">'
            '<h1>Page not found</h1><p>The page you requested could not be found.</p>'
            '<p><a href="/" style="color:#00ffff;">Home</a> | <a href="/marketplace" style="color:#00ffff;">Marketplace</a> | <a href="/app" style="color:#00ffff;">App</a></p>'
            '</body></html>', 404
        )
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors gracefully."""
    import traceback
    err_msg = str(error) if error else "Unknown error"
    print(f"[ERROR] Internal server error: {err_msg}")
    traceback.print_exc()
    # Include actual error for API routes so frontend can display it
    return jsonify({
        "error": f"Internal server error: {err_msg}",
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

# Referral program: 20% lifetime commission for referrers
REFERRALS_FILE = "referrals.json"
REFERRAL_COMMISSION_RATE = 0.20  # 20%

# Marketplace - want/for-sale posts from set builders
MARKETPLACE_FILE = "marketplace.json"
MARKETPLACE_SALES_FILE = "marketplace_sales.json"
MARKETPLACE_PENDING_FILE = "marketplace_pending_shipments.json"  # Pending = tracking added, awaiting delivery
MARKETPLACE_REPUTATION_FILE = "marketplace_reputation.json"
MARKETPLACE_BUYER_FEE_PCT = 5.0
MARKETPLACE_SELLER_FEE_PCT = 5.0
MARKETPLACE_STRIKES_BEFORE_SUSPENSION = 3

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

def load_referrals():
    """Load referral data from file."""
    if os.path.exists(REFERRALS_FILE):
        try:
            with open(REFERRALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_referrals(refs):
    """Save referral data to file."""
    with open(REFERRALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(refs, f, indent=2)

def get_referral_code(email):
    """Generate a short referral code from email (6 chars)."""
    h = hashlib.sha256(email.lower().encode()).hexdigest()[:6]
    return h.upper()

def load_marketplace():
    """Load marketplace posts (wants + for_sale)."""
    if os.path.exists(MARKETPLACE_FILE):
        try:
            with open(MARKETPLACE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"wants": [], "for_sale": []}
    return {"wants": [], "for_sale": []}

def save_marketplace(data):
    """Save marketplace data."""
    with open(MARKETPLACE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_marketplace_sales():
    """Load reported marketplace sales for fee tracking."""
    if os.path.exists(MARKETPLACE_SALES_FILE):
        try:
            with open(MARKETPLACE_SALES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_marketplace_sales(sales):
    """Save marketplace sales."""
    with open(MARKETPLACE_SALES_FILE, 'w', encoding='utf-8') as f:
        json.dump(sales, f, indent=2)

def load_marketplace_pending():
    if os.path.exists(MARKETPLACE_PENDING_FILE):
        try:
            with open(MARKETPLACE_PENDING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_marketplace_pending(pending):
    with open(MARKETPLACE_PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(pending, f, indent=2)

def _detect_carrier(tracking_number):
    """Return TrackingMore carrier code from tracking number format."""
    tn = re.sub(r'\s+', '', str(tracking_number or ''))
    if tn.upper().startswith('1Z'):
        return 'ups'
    if tn.startswith('94') and len(tn) >= 20:
        return 'usps'
    if tn.isdigit() and len(tn) in (12, 13, 14, 15, 20, 22):
        if len(tn) in (20, 22) or tn.startswith('94'):
            return 'usps'
        return 'fedex'
    return 'usps'  # default for USPS-style numbers

def _check_tracking_delivered(tracking_number, carrier=None):
    """Check if package is delivered via TrackingMore API. Returns (is_delivered, status_str, error)."""
    key = (os.environ.get('TRACKINGMORE_API_KEY') or '').strip()
    if not key:
        return None, None, "TRACKINGMORE_API_KEY not configured"
    tn = re.sub(r'\s+', '', str(tracking_number or ''))
    if not tn:
        return False, None, "Invalid tracking number"
    car = (carrier or _detect_carrier(tn)).lower()
    try:
        import urllib.request
        url = f"https://api.trackingmore.com/v2/trackings/{car}/{urllib.parse.quote(tn)}"
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Trackingmore-Api-Key', key)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        d = data.get('data') or {}
        status = (d.get('status') or '').lower()
        return status == 'delivered', status, None
    except Exception as e:
        return False, None, str(e)

def load_marketplace_reputation():
    if os.path.exists(MARKETPLACE_REPUTATION_FILE):
        try:
            with open(MARKETPLACE_REPUTATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_marketplace_reputation(data):
    with open(MARKETPLACE_REPUTATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def is_marketplace_suspended(email):
    """True if user has 3+ reports or 3+ negative feedback against them."""
    if not email:
        return False
    rep = load_marketplace_reputation()
    r = rep.get((email or '').lower(), {})
    if r.get("suspended"):
        return True
    reports = r.get("reports_against") or []
    if len(reports) >= MARKETPLACE_STRIKES_BEFORE_SUSPENSION:
        return True
    feedback = r.get("feedback_received") or []
    neg = sum(1 for f in feedback if f.get("rating", 5) <= 2)
    return neg >= MARKETPLACE_STRIKES_BEFORE_SUSPENSION

def get_referrer_from_code(code):
    """Look up referrer email from code. Returns None if not found."""
    refs = load_referrals()
    code_upper = (code or '').strip().upper()
    for referrer_email, data in refs.items():
        if data.get('code', '').upper() == code_upper:
            return referrer_email
    return None

def add_referral_earnings(referrer_email, referred_email, amount_paid):
    """Record 20% commission for referrer when referred user pays."""
    commission = round(float(amount_paid) * REFERRAL_COMMISSION_RATE, 2)
    if commission <= 0:
        return
    refs = load_referrals()
    if referrer_email not in refs:
        refs[referrer_email] = {
            "code": get_referral_code(referrer_email),
            "referred": [],
            "earnings": 0,
            "paid_out": 0,
            "history": []
        }
    if referred_email not in refs[referrer_email]["referred"]:
        refs[referrer_email]["referred"].append(referred_email)
    refs[referrer_email]["earnings"] = round(refs[referrer_email].get("earnings", 0) + commission, 2)
    refs[referrer_email]["history"] = refs[referrer_email].get("history", [])
    refs[referrer_email]["history"].append({
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "referred": referred_email,
        "amount_paid": amount_paid,
        "commission": commission
    })
    save_referrals(refs)
    print(f"[REFERRAL] {referrer_email} earned ${commission} from {referred_email}'s ${amount_paid} payment")

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

@app.route('/health')
def health():
    """Quick health check - used by Render and for debugging."""
    r = jsonify({"status": "ok", "version": _live_version()})
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    r.headers['Expires'] = '0'
    return r

@app.route('/api/image-proxy')
def api_image_proxy():
    """Proxy external card images to avoid CORS/hotlink blocking in previews."""
    import urllib.parse
    import requests as req_lib
    url = request.args.get('url', '')
    if not url:
        return '', 400
    try:
        parsed = urllib.parse.urlparse(urllib.parse.unquote(url))
        host = (parsed.netloc or '').lower()
        allowed = ('ebayimg.com', 'i.ebayimg.com', 'tcdb.com', 'www.tcdb.com')
        if not any(h in host for h in allowed):
            return '', 403
        r = req_lib.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': ''
        }, stream=True)
        r.raise_for_status()
        ct = r.headers.get('Content-Type', 'image/jpeg')
        if 'image/' not in (ct or ''):
            ct = 'image/jpeg'
        return r.content, 200, {'Content-Type': ct, 'Cache-Control': 'public, max-age=300'}
    except Exception as e:
        print(f"[IMAGE-PROXY] Failed for {url[:60]}...: {e}")
        return '', 502

@app.route('/')
def landing():
    """Landing page."""
    try:
        email = session.get('user_email', '')
        return render_template('landing.html', email=email)
    except Exception as e:
        print(f"[ERROR] Error in landing: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/pictures/<path:filename>')
def serve_picture(filename):
    """Serve images from the Pictures folder (case-sensitive on Linux/Render)."""
    try:
        filename = urllib.parse.unquote(filename)
        pictures_dir = os.path.join(os.path.dirname(__file__), 'Pictures')
        if not os.path.exists(pictures_dir):
            pictures_dir = os.path.join(os.path.dirname(__file__), 'pictures')
        return send_from_directory(pictures_dir, filename)
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
            ref = request.form.get('ref', '').strip() or request.form.get('referral', '').strip()
            
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
            
            # Resolve referrer: ref can be email or 6-char code
            referrer_email = None
            if ref:
                if '@' in ref:
                    referrer_email = ref.lower()
                else:
                    referrer_email = get_referrer_from_code(ref)
                if referrer_email == email:
                    referrer_email = None  # Can't refer yourself
            
            # Create new account with 3-day trial
            from datetime import datetime, timedelta
            trial_end = (datetime.now() + timedelta(days=TRIAL_DAYS)).strftime('%Y-%m-%d')
            
            subs[email] = {
                'status': 'trial',
                'trial_ends': trial_end,
                'name': name or '',
                'registered': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'expires': '',  # No paid expiry yet
                'referred_by': referrer_email or ''
            }
            save_subscriptions(subs)
            
            # Ensure referrer is in referrals file (so they get a code)
            if referrer_email:
                refs = load_referrals()
                if referrer_email not in refs:
                    refs[referrer_email] = {
                        "code": get_referral_code(referrer_email),
                        "referred": [],
                        "earnings": 0,
                        "paid_out": 0,
                        "history": []
                    }
                if email not in refs[referrer_email]["referred"]:
                    refs[referrer_email]["referred"].append(email)
                save_referrals(refs)
            
            session['user_email'] = email
            return redirect('/app')
        
        ref = request.args.get('ref', '')
        return render_template('register.html', ref=ref)
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

@app.route('/referral')
def referral():
    """Referral dashboard - share your link, earn 20% for life."""
    email = session.get('user_email', '')
    if not email:
        return redirect('/login')
    refs = load_referrals()
    data = refs.get(email.lower(), {})
    code = data.get('code') or get_referral_code(email)
    if email.lower() not in refs:
        refs[email.lower()] = {
            "code": code,
            "referred": [],
            "earnings": 0,
            "paid_out": 0,
            "history": []
        }
        save_referrals(refs)
    base = request.url_root.rstrip('/')
    referral_link = f"{base}/register?ref={code}"
    history = list(reversed(data.get('history', [])[-20:]))  # Last 20, newest first
    return render_template('referral.html',
        referral_link=referral_link,
        code=code,
        referred=data.get('referred', []),
        earnings=data.get('earnings', 0),
        paid_out=data.get('paid_out', 0),
        history=history,
        commission_rate=int(REFERRAL_COMMISSION_RATE * 100))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/contact')
def contact():
    """Contact page."""
    try:
        return render_template('contact.html')
    except Exception as e:
        print(f"[ERROR] Error in contact: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/shipping')
def shipping():
    """Shipping info - public page. Links to USPS Ground Advantage, eBay labels, Pirate Ship."""
    try:
        email = session.get('user_email', '')
        return render_template('shipping.html', email=email)
    except Exception as e:
        print(f"[ERROR] Error in shipping: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/marketplace', strict_slashes=False)
def marketplace():
    """Marketplace - subscriber bonus. Find cards you need, sell cards you have."""
    try:
        email = session.get('user_email', '')
        if not email:
            return redirect(url_for('login') + '?next=/marketplace')
        if not is_subscribed(email):
            return redirect('/subscribe?msg=Subscribe+to+get+Marketplace+access+free')
        return render_template('marketplace.html',
            email=email,
            buyer_fee_pct=float(os.environ.get('MARKETPLACE_BUYER_FEE_PCT', MARKETPLACE_BUYER_FEE_PCT)),
            seller_fee_pct=float(os.environ.get('MARKETPLACE_SELLER_FEE_PCT', MARKETPLACE_SELLER_FEE_PCT)))
    except Exception as e:
        print(f"[ERROR] Error in marketplace: {e}")
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p>", 500

@app.route('/api/marketplace/want-matches', methods=['POST'])
def api_marketplace_want_matches():
    """Return marketplace wants that match the user's cards. Subscribers only."""
    email = session.get('user_email', '')
    if not email or not is_subscribed(email):
        return jsonify({"error": "Subscription required."}), 403
    try:
        data = request.get_json() or {}
        set_name = (data.get("set_name") or "").strip().lower()
        cards_in = data.get("cards") or []
        if not set_name or not cards_in:
            return jsonify({"matches": []})
        mp = load_marketplace()
        wants = [w for w in (mp.get("wants") or [])
                 if (w.get("email") or "").lower() != email.lower()]
        matches = []
        for card in cards_in:
            cid = card.get("id")
            name = (card.get("name") or "").strip()
            number = str(card.get("number") or "").strip()
            if not cid:
                continue
            matching_wants = []
            for w in wants:
                wset = (w.get("set_name") or "").lower()
                if not wset or (set_name not in wset and wset not in set_name):
                    continue
                cards_text = (w.get("cards") or "").lower()
                if not cards_text:
                    continue
                name_match = name and len(name) > 2 and name.lower() in cards_text
                num_match = number and (number in cards_text or f"#{number}".lower() in cards_text)
                if name_match or num_match:
                    matching_wants.append({"email": w.get("email"), "set_name": w.get("set_name"),
                        "cards": w.get("cards"), "notes": w.get("notes")})
            if matching_wants:
                matches.append({"cardId": cid, "number": number, "name": name, "wants": matching_wants})
        return jsonify({"matches": matches})
    except Exception as e:
        print(f"[ERROR] api_marketplace_want_matches: {e}")
        return jsonify({"error": str(e)}), 500

def _enrich_post_with_reputation(post):
    """Add reputation info to a post for display."""
    p = dict(post)
    em = (post.get("email") or "").lower()
    rep = load_marketplace_reputation()
    r = rep.get(em, {})
    reports = r.get("reports_against") or []
    feedback = r.get("feedback_received") or []
    neg_fb = sum(1 for f in feedback if f.get("rating", 5) <= 2)
    suspended = r.get("suspended") or len(reports) >= MARKETPLACE_STRIKES_BEFORE_SUSPENSION or neg_fb >= MARKETPLACE_STRIKES_BEFORE_SUSPENSION
    avg_rating = 0.0
    if feedback:
        avg_rating = sum(f.get("rating", 0) for f in feedback) / len(feedback)
    p["reputation"] = {
        "reports_count": len(reports),
        "negative_feedback_count": neg_fb,
        "avg_rating": round(avg_rating, 1),
        "feedback_count": len(feedback),
        "suspended": suspended,
    }
    return p

@app.route('/api/marketplace/posts')
def api_marketplace_posts():
    """List marketplace posts (subscribers only). Supports filter=wants|forsale and set=..."""
    email = session.get('user_email', '')
    if not email or not is_subscribed(email):
        return jsonify({"error": "Subscription required. Marketplace is free for subscribers."}), 403
    try:
        data = load_marketplace()
        wants = [_enrich_post_with_reputation(w) for w in data.get("wants", [])]
        for_sale = [_enrich_post_with_reputation(s) for s in data.get("for_sale", [])]
        f = request.args.get("filter", "").lower()
        set_filter = request.args.get("set", "").strip().lower()
        if set_filter:
            wants = [w for w in wants if set_filter in (w.get("set_name") or "").lower()]
            for_sale = [s for s in for_sale if set_filter in (s.get("set_name") or "").lower()]
        if f == "wants":
            return jsonify({"wants": wants, "for_sale": []})
        if f == "forsale":
            return jsonify({"wants": [], "for_sale": for_sale})
        return jsonify({"wants": wants, "for_sale": for_sale})
    except Exception as e:
        print(f"[ERROR] api_marketplace_posts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/want', methods=['POST'])
def api_marketplace_want():
    """Add a want post (cards needed). Requires login. Suspended users cannot post."""
    email = session.get('user_email', '')
    if not email:
        return jsonify({"error": "Login required"}), 401
    if is_marketplace_suspended(email):
        return jsonify({"error": "Your account is suspended (3+ reports). Contact support."}), 403
    try:
        data = request.get_json() or {}
        set_name = (data.get("set_name") or "").strip()
        cards = (data.get("cards") or "").strip()
        notes = (data.get("notes") or "").strip()[:500]
        ebay_username = (data.get("ebay_username") or "").strip()[:50]
        if not set_name or not cards:
            return jsonify({"error": "Set name and cards are required"}), 400
        mp = load_marketplace()
        mp.setdefault("wants", [])
        post = {
            "id": str(uuid.uuid4())[:12],
            "email": email.lower(),
            "ebay_username": ebay_username,
            "set_name": set_name[:200],
            "cards": cards[:1000],
            "notes": notes,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        mp["wants"].insert(0, post)
        save_marketplace(mp)
        return jsonify({"success": True, "post": post})
    except Exception as e:
        print(f"[ERROR] api_marketplace_want: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/forsale', methods=['POST'])
def api_marketplace_forsale():
    """Add a for-sale post. Requires login. Suspended users cannot post."""
    email = session.get('user_email', '')
    if not email:
        return jsonify({"error": "Login required"}), 401
    if is_marketplace_suspended(email):
        return jsonify({"error": "Your account is suspended (3+ reports). Contact support."}), 403
    try:
        data = request.get_json() or {}
        set_name = (data.get("set_name") or "").strip()
        cards = (data.get("cards") or "").strip()
        price = (data.get("price") or "").strip()[:100]
        notes = (data.get("notes") or "").strip()[:500]
        ebay_username = (data.get("ebay_username") or "").strip()[:50]
        if not set_name or not cards:
            return jsonify({"error": "Set name and cards are required"}), 400
        mp = load_marketplace()
        mp.setdefault("for_sale", [])
        post = {
            "id": str(uuid.uuid4())[:12],
            "email": email.lower(),
            "ebay_username": ebay_username,
            "set_name": set_name[:200],
            "cards": cards[:1000],
            "price": price or "Best offer",
            "notes": notes,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        mp["for_sale"].insert(0, post)
        save_marketplace(mp)
        return jsonify({"success": True, "post": post})
    except Exception as e:
        print(f"[ERROR] api_marketplace_forsale: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/report-sale', methods=['POST'])
def api_marketplace_report_sale():
    """Report a completed marketplace sale for fee tracking. Subscribers only."""
    email = session.get('user_email', '')
    if not email or not is_subscribed(email):
        return jsonify({"error": "Subscription required."}), 403
    try:
        data = request.get_json() or {}
        seller_email = (data.get("seller_email") or "").strip().lower()
        buyer_email = (data.get("buyer_email") or "").strip().lower()
        amount = float(data.get("amount") or 0)
        description = (data.get("description") or "").strip()[:500]
        if not seller_email or not buyer_email or amount <= 0:
            return jsonify({"error": "Seller email, buyer email, and amount (>0) are required"}), 400
        # Reporter must be seller or buyer
        if email.lower() not in (seller_email, buyer_email):
            return jsonify({"error": "You must be the seller or buyer to report this sale"}), 403
        sales = load_marketplace_sales()
        buyer_fee = amount * (MARKETPLACE_BUYER_FEE_PCT / 100)
        seller_fee = amount * (MARKETPLACE_SELLER_FEE_PCT / 100)
        total_fee = buyer_fee + seller_fee
        sale = {
            "id": str(uuid.uuid4())[:12],
            "seller_email": seller_email,
            "buyer_email": buyer_email,
            "amount": round(amount, 2),
            "buyer_fee": round(buyer_fee, 2),
            "seller_fee": round(seller_fee, 2),
            "total_fee": round(total_fee, 2),
            "description": description,
            "reported_by": email.lower(),
            "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        sales.append(sale)
        save_marketplace_sales(sales)
        return jsonify({"success": True, "sale": sale, "total_fee": sale["total_fee"]})
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid amount"}), 400
    except Exception as e:
        print(f"[ERROR] api_marketplace_report_sale: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/report-shipment', methods=['POST'])
def api_marketplace_report_shipment():
    """Report a shipment (tracking + amount). When tracking shows delivered, sale auto-completes."""
    email = session.get('user_email', '')
    if not email or not is_subscribed(email):
        return jsonify({"error": "Subscription required."}), 403
    try:
        data = request.get_json() or {}
        tracking = (data.get("tracking_number") or "").strip().replace(" ", "")
        buyer_email = (data.get("buyer_email") or "").strip().lower()
        amount = float(data.get("amount") or 0)
        if not tracking or not buyer_email or amount <= 0:
            return jsonify({"error": "Tracking number, buyer email, and amount (>0) are required"}), 400
        if buyer_email == email.lower():
            return jsonify({"error": "You cannot sell to yourself"}), 400
        pending = load_marketplace_pending()
        for p in pending:
            if (p.get("tracking_number", "").replace(" ", "") == tracking and
                p.get("seller_email") == email.lower()):
                return jsonify({"error": "This tracking is already reported"}), 400
        rec = {
            "id": str(uuid.uuid4())[:12],
            "tracking_number": tracking,
            "seller_email": email.lower(),
            "buyer_email": buyer_email,
            "amount": round(amount, 2),
            "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "pending",
            "last_checked": None,
        }
        pending.append(rec)
        save_marketplace_pending(pending)
        # Try immediate check if API key exists
        delivered, status, _ = _check_tracking_delivered(tracking)
        if delivered:
            _complete_pending_sale(rec)
            return jsonify({"success": True, "shipment": rec, "delivered": True, "message": "Already delivered! Sale recorded."})
        return jsonify({"success": True, "shipment": rec, "delivered": False})
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid amount"}), 400
    except Exception as e:
        print(f"[ERROR] api_marketplace_report_shipment: {e}")
        return jsonify({"error": str(e)}), 500

def _complete_pending_sale(rec):
    """Move pending shipment to completed sales (fee tracking) and remove from pending."""
    pending = load_marketplace_pending()
    pid = rec.get("id")
    pending = [p for p in pending if p.get("id") != pid]
    save_marketplace_pending(pending)
    amount = float(rec.get("amount") or 0)
    buyer_fee = amount * (MARKETPLACE_BUYER_FEE_PCT / 100)
    seller_fee = amount * (MARKETPLACE_SELLER_FEE_PCT / 100)
    sale = {
        "id": str(uuid.uuid4())[:12],
        "seller_email": rec.get("seller_email", ""),
        "buyer_email": rec.get("buyer_email", ""),
        "amount": round(amount, 2),
        "buyer_fee": round(buyer_fee, 2),
        "seller_fee": round(seller_fee, 2),
        "total_fee": round(buyer_fee + seller_fee, 2),
        "description": f"Auto-completed from tracking {rec.get('tracking_number', '')}",
        "reported_by": "tracking_delivered",
        "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    sales = load_marketplace_sales()
    sales.append(sale)
    save_marketplace_sales(sales)
    return sale

@app.route('/api/marketplace/check-tracking', methods=['POST'])
def api_marketplace_check_tracking():
    """Check all pending shipments; auto-complete those delivered. Call from cron or UI."""
    email = session.get('user_email', '')
    if not email or not is_subscribed(email):
        return jsonify({"error": "Subscription required."}), 403
    try:
        pending = load_marketplace_pending()
        completed = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        completed_ids = set()
        for rec in list(pending):
            tn = (rec.get("tracking_number") or "").replace(" ", "")
            if not tn:
                continue
            delivered, status, err = _check_tracking_delivered(tn)
            if delivered:
                sale = _complete_pending_sale(rec)
                completed.append({"tracking": tn, "amount": sale.get("amount"), "total_fee": sale.get("total_fee")})
                completed_ids.add(rec.get("id"))
            else:
                rec["last_checked"] = now
                rec["status"] = status or "pending"
        pending = [p for p in pending if p.get("id") not in completed_ids]
        save_marketplace_pending(pending)
        return jsonify({"success": True, "completed": completed, "checked": len(pending) + len(completed_ids)})
    except Exception as e:
        print(f"[ERROR] api_marketplace_check_tracking: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/pending')
def api_marketplace_pending():
    """List pending shipments for current user (as seller or buyer)."""
    email = session.get('user_email', '')
    if not email or not is_subscribed(email):
        return jsonify({"error": "Subscription required."}), 403
    em = email.lower()
    pending = [p for p in load_marketplace_pending() if p.get("seller_email") == em or p.get("buyer_email") == em]
    tracking_configured = bool((os.environ.get('TRACKINGMORE_API_KEY') or '').strip())
    return jsonify({"pending": pending, "tracking_configured": tracking_configured})

@app.route('/api/marketplace/report', methods=['POST'])
def api_marketplace_report():
    """Report a user: no_payment, no_ship, not_as_described. 3 strikes = suspended."""
    email = session.get('user_email', '')
    if not email:
        return jsonify({"error": "Login required"}), 401
    try:
        data = request.get_json() or {}
        target_email = (data.get("target_email") or "").strip().lower()
        report_type = (data.get("report_type") or "").strip().lower()
        if report_type not in ("no_payment", "no_ship", "not_as_described"):
            return jsonify({"error": "Invalid report type. Use: no_payment, no_ship, not_as_described"}), 400
        if not target_email:
            return jsonify({"error": "Target email required"}), 400
        if target_email == email.lower():
            return jsonify({"error": "You cannot report yourself"}), 400
        rep = load_marketplace_reputation()
        entry = rep.setdefault(target_email, {"reports_against": [], "feedback_received": []})
        reports = entry.get("reports_against") or []
        # Prevent same reporter reporting twice for same type (per target) - allow multiple reports from different users
        from_email = email.lower()
        for r in reports:
            if r.get("from_email") == from_email and r.get("type") == report_type:
                return jsonify({"error": "You already reported this user for this issue"}), 400
        reports.append({"from_email": from_email, "type": report_type, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
        entry["reports_against"] = reports
        if len(reports) >= MARKETPLACE_STRIKES_BEFORE_SUSPENSION:
            entry["suspended"] = True
            entry["suspended_reason"] = f"{len(reports)} reports (3-strike rule)"
        rep[target_email] = entry
        save_marketplace_reputation(rep)
        return jsonify({"success": True, "strikes": len(reports), "suspended": entry.get("suspended", False)})
    except Exception as e:
        print(f"[ERROR] api_marketplace_report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/feedback', methods=['POST'])
def api_marketplace_feedback():
    """Leave feedback for a user (rating 1-5). 3 negative (<=2) = contributes to suspension."""
    email = session.get('user_email', '')
    if not email:
        return jsonify({"error": "Login required"}), 401
    try:
        data = request.get_json() or {}
        target_email = (data.get("target_email") or "").strip().lower()
        rating = int(data.get("rating") or 0)
        role = (data.get("role") or "").strip().lower()  # "buyer" or "seller" - what they were in the deal
        comment = (data.get("comment") or "").strip()[:300]
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be 1-5"}), 400
        if not target_email:
            return jsonify({"error": "Target email required"}), 400
        if target_email == email.lower():
            return jsonify({"error": "You cannot leave feedback for yourself"}), 400
        rep = load_marketplace_reputation()
        entry = rep.setdefault(target_email, {"reports_against": [], "feedback_received": []})
        feedback_list = entry.get("feedback_received") or []
        from_email = email.lower()
        if any(f.get("from_email") == from_email for f in feedback_list):
            return jsonify({"error": "You already left feedback for this user"}), 400
        feedback_list.append({
            "from_email": from_email,
            "rating": rating,
            "role": role or "unknown",
            "comment": comment,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        entry["feedback_received"] = feedback_list
        # Count negative feedback (<=2) - 3 negative = suspension
        neg_count = sum(1 for f in feedback_list if f.get("rating", 5) <= 2)
        if neg_count >= MARKETPLACE_STRIKES_BEFORE_SUSPENSION:
            entry["suspended"] = True
            entry["suspended_reason"] = f"{neg_count} negative feedback"
        rep[target_email] = entry
        save_marketplace_reputation(rep)
        return jsonify({"success": True, "negative_count": neg_count, "suspended": entry.get("suspended", False)})
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid rating"}), 400
    except Exception as e:
        print(f"[ERROR] api_marketplace_feedback: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/marketplace/delete', methods=['POST'])
def api_marketplace_delete():
    """Delete own post. Requires login."""
    email = session.get('user_email', '')
    if not email:
        return jsonify({"error": "Login required"}), 401
    try:
        data = request.get_json() or {}
        post_id = (data.get("id") or "").strip()
        post_type = (data.get("type") or "").lower()
        if not post_id or post_type not in ("want", "forsale"):
            return jsonify({"error": "Invalid request"}), 400
        mp = load_marketplace()
        key = "wants" if post_type == "want" else "for_sale"
        lst = mp.get(key, [])
        orig_len = len(lst)
        mp[key] = [p for p in lst if not (p.get("id") == post_id and (p.get("email") or "").lower() == email.lower())]
        if len(mp[key]) == orig_len:
            return jsonify({"error": "Post not found or you can't delete it"}), 404
        save_marketplace(mp)
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] api_marketplace_delete: {e}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/guide')
def guide_page():
    """Interactive guide / ad for social media sharing."""
    return render_template('guide.html')

def _live_version():
    """Re-read VERSION from disk so updates apply without server restart."""
    try:
        return os.environ.get("VERSION") or open(os.path.join(os.path.dirname(__file__) or '.', 'VERSION')).read().strip() or VERSION
    except Exception:
        return VERSION

@app.route('/app')
def app_page():
    """Main application page (requires subscription)."""
    try:
        email = session.get('user_email', '')
        if not email:
            return redirect('/login')
        
        v = _live_version()
        # Owner always has access
        if email.lower() == OWNER_EMAIL.lower():
            resp = make_response(render_template('app.html', email=email, version=v))
        elif not is_subscribed(email):
            return redirect('/subscribe')
        else:
            resp = make_response(render_template('app.html', email=email, version=v))
        
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        return resp
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
                        # Base with prefixes: after all plain numbers, then by prefix, then number.
                        # Bowman Baseball: 1..100 first, then BP-1..BP-150 (not interleaved).
                        # Bowman Draft: BD-* then BDC-* (prefix groups, not number-interleaved).
                        try:
                            num_val = int(num_part)
                        except ValueError:
                            import re
                            num_match = re.search(r'\d+', num_part)
                            num_val = int(num_match.group()) if num_match else 0
                        return (1, prefix, num_val, num)
                elif num.isdigit():
                    # Plain veterans first (group 0), before any BP-/BD-/etc. prefixes
                    return (0, '', int(num), num)
                else:
                    # Try to extract first number
                    import re
                    match = re.search(r'\d+', num)
                    if match:
                        return (2, '', int(match.group()), num)
                    return (999, '', 0, num)
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

        # Apply bundled preset + user draft (price/qty persistence)
        preset_applied = None
        draft_applied = False
        checklist_id = None
        preset_set_name = None
        try:
            from features.static_presets import (
                find_matching_preset,
                filter_cards_by_preset,
                merge_preset_into_cards,
            )
            from features.checklist_drafts import (
                ChecklistDraftManager,
                checklist_id_from_url,
                merge_draft_into_cards,
            )
            checklist_id = checklist_id_from_url(url, checklist_type)
            preset = find_matching_preset(url, checklist_type)
            if preset:
                if preset.get('filter'):
                    before = len(formatted_cards)
                    formatted_cards = filter_cards_by_preset(formatted_cards, preset['filter'])
                    print(f"[APP] Preset filter: {before} -> {len(formatted_cards)} cards")
                formatted_cards = merge_preset_into_cards(formatted_cards, preset.get('cards', []))
                preset_applied = preset.get('id') or preset.get('name')
                if preset.get('setName'):
                    preset_set_name = preset['setName']
                print(f"[APP] Applied bundled preset: {preset_applied}")
            email = session.get('user_email', '')
            dm = ChecklistDraftManager(user_email=email)
            draft = dm.load_draft(checklist_id)
            if draft and draft.get('cards'):
                formatted_cards = merge_draft_into_cards(formatted_cards, draft['cards'])
                draft_applied = True
                print(f"[APP] Merged server draft for {checklist_id}")
        except Exception as preset_err:
            print(f"[APP] Preset/draft merge warning: {preset_err}")
        
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

        if preset_set_name:
            set_name = preset_set_name
        
        # Simple logging - no restrictive validation
        formatted_count = len(formatted_cards)
        has_prefix = any('-' in str(c.get('number', '')) for c in formatted_cards) if formatted_cards else False
        print(f"[APP] ========================================")
        print(f"[APP] BEFORE RETURNING:")
        print(f"[APP] Checklist type: {checklist_type}")
        print(f"[APP] Formatted cards count: {formatted_count}")
        print(f"[APP] Format: {'PREFIXED' if has_prefix else 'PLAIN NUMBERS'}")
        print(f"[APP] ========================================")
        
        formatted_count = len(formatted_cards)
        response_data = {
            "success": True,
            "cards": formatted_cards,
            "count": formatted_count,
            "setName": set_name,
            "source": "beckett" if 'beckett.com' in url else ("cardsmiths" if 'cardsmithsbreaks.com' in url else "universal"),
            "checklistType": checklist_type,
            "checklistId": checklist_id,
            "presetApplied": preset_applied,
            "draftApplied": draft_applied,
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

def _run_listing_job(job_id, job_data):
    """Background worker: create listing and store result. Avoids HTTP timeout."""
    global listing_jobs
    try:
        from config import Config
        from dotenv import load_dotenv
        load_dotenv(override=True)
        config = Config()
        token = job_data['token']
        listing_manager = eBayListingManager(token_override=token)
        if job_data.get('shipping_id'):
            listing_manager.policies['fulfillment_policy_id'] = job_data['shipping_id']
        if job_data.get('payment_id'):
            listing_manager.policies['payment_policy_id'] = job_data['payment_id']
        if job_data.get('return_id'):
            listing_manager.policies['return_policy_id'] = job_data['return_id']
        
        result = listing_manager.create_variation_listing(
            cards=job_data['listing_cards'],
            title=job_data['set_name'][:80],
            sport=job_data.get('sport') or None,
            description=job_data['description'] or f"<p><strong>{job_data['set_name']}</strong></p><p>Select your card from the dropdown menu.</p>",
            category_id="261328",
            price=job_data['base_price'],
            quantity=1,
            condition="Near Mint",
            images=[job_data['image_url']] if job_data.get('image_url') else None,
            publish=True,
            fulfillment_policy_id=job_data.get('shipping_id'),
            use_base_cards_policy=None,
            schedule_draft=False,
            schedule_hours=0
        )
        
        if result.get('success'):
            group_key = result.get('group_key') or result.get('groupKey')
            base_url = "https://www.ebay.com" if config.EBAY_ENVIRONMENT == 'production' else "https://sandbox.ebay.com"
            final_status = "scheduled" if result.get('scheduled') else ("published" if result.get('publish', True) else "draft")
            response_data = {
                "success": True,
                "groupKey": group_key,
                "setName": job_data['set_name'],
                "cardsCreated": len(job_data['listing_cards']),
                "status": final_status,
                "listingId": result.get('listing_id') or result.get('listingId'),
                "listingUrl": result.get('ebay_url', '') or result.get('seller_hub_url', '') or f"{base_url}/sh/account/listings",
                "sellerHubActive": result.get('seller_hub_active') or f"{base_url}/sh/account/listings?status=ACTIVE",
                "sellerHubScheduled": result.get('seller_hub_scheduled') or f"{base_url}/sh/lst/scheduled",
                "scheduled": result.get('scheduled', False),
                "message": result.get('message', 'Listing created successfully'),
            }
            listing_jobs[job_id] = {"status": "completed", "result": response_data}
        else:
            err = result.get('error', 'Unknown error')
            listing_jobs[job_id] = {"status": "failed", "error": err, "error_code": result.get('error_code'), "group_key": result.get('group_key')}
    except Exception as e:
        import traceback
        traceback.print_exc()
        listing_jobs[job_id] = {"status": "failed", "error": str(e)}

@app.route('/api/list-status/<job_id>')
@require_subscription
def list_status(job_id):
    """Poll for background listing job result."""
    job = listing_jobs.get(job_id, {})
    if not job:
        return jsonify({"status": "unknown", "error": "Job not found or expired"}), 404
    return jsonify(job)

@app.route('/api/list', methods=['POST'])
@require_subscription
def create_listing():
    """Start listing creation as background job (returns immediately to avoid 30s timeout)."""
    data = request.json or {}
    
    try:
        set_name = data.get('setName', 'Card Set')
        sport = data.get('sport', '').strip()
        description = data.get('description', '')
        cards = data.get('cards', [])
        from features.image_utils import sanitize_image_url, DEFAULT_PLACEHOLDER_IMAGE
        image_url = sanitize_image_url(data.get('imageUrl', ''))
        payment_id = data.get('paymentPolicyId', '').strip() or None  # Default to None (Managed by eBay)
        shipping_id = data.get('shippingPolicyId')
        return_id = data.get('returnPolicyId')
        
        if not cards:
            return jsonify({"error": "No cards provided"}), 400
        
        valid_cards = [c for c in cards if int(c.get('quantity', 0)) > 0]
        if not valid_cards:
            return jsonify({"error": "No cards with quantity > 0. Cards with quantity 0 are excluded from listings."}), 400
        
        listing_cards = []
        prices = {}
        for card in valid_cards:
            img = sanitize_image_url(
                card.get('imageUrl') or card.get('image_url', '') or image_url,
                allow_placeholder=True,
            ) or DEFAULT_PLACEHOLDER_IMAGE
            card_data = {
                'name': card.get('name', ''),
                'number': str(card.get('number', '')),
                'quantity': int(card.get('quantity', 1)),
                'team': card.get('team', ''),
                'image_url': img,
                'imageUrl': img  # Both keys for downstream compatibility
            }
            listing_cards.append(card_data)
            price = float(card.get('price', 1.00))
            if card_data['name']:
                prices[card_data['name']] = price
        
        base_price = list(prices.values())[0] if len(set(prices.values())) == 1 else prices
        token = _get_effective_token()
        if not token:
            return jsonify({"error": "No eBay token. Please complete Step 2 (Login)."}), 401
        
        job_id = str(uuid.uuid4())
        job_data = {
            'token': token,
            'set_name': set_name,
            'sport': sport,
            'description': description,
            'listing_cards': listing_cards,
            'base_price': base_price,
            'image_url': image_url,
            'shipping_id': shipping_id,
            'payment_id': payment_id,
            'return_id': return_id,
        }
        listing_jobs[job_id] = {"status": "processing"}
        threading.Thread(target=_run_listing_job, args=(job_id, job_data)).start()
        return jsonify({"job_id": job_id, "status": "processing"})
    
    except Exception as e:
        print(f"[ERROR] Exception in create_listing: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

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

def _group_payments_by_email(payments):
    """Convert payments list to dict grouped by email for template."""
    grouped = {}
    for p in (payments or []):
        if isinstance(p, dict):
            email = p.get('email', '')
            if email not in grouped:
                grouped[email] = []
            grouped[email].append(p)
    return grouped

@app.route('/admin')
@require_admin
def admin():
    """Admin panel."""
    subs = load_subscriptions()
    payments_raw = load_payments()
    payments = _group_payments_by_email(payments_raw) if isinstance(payments_raw, list) else (payments_raw or {})
    referrals = load_referrals()
    
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
                          expiring_soon=expiring_soon,
                          referrals=referrals,
                          commission_rate=int(REFERRAL_COMMISSION_RATE * 100))

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
    
    # Referral commission: 20% for referrer (lifetime)
    referred_by = subs.get(email, {}).get('referred_by', '')
    if referred_by:
        add_referral_earnings(referred_by, email, amount)
    
    return jsonify({
        "success": True,
        "message": f"Payment recorded and subscription extended until {subs[email]['expires']}"
    })

@app.route('/admin/mark-referral-paid', methods=['POST'])
@require_admin
def mark_referral_paid():
    """Mark a payout to a referrer (increases their paid_out)."""
    data = request.json
    referrer_email = data.get('referrer_email', '').strip().lower()
    amount = float(data.get('amount', 0))
    if not referrer_email:
        return jsonify({"error": "Referrer email required"}), 400
    refs = load_referrals()
    if referrer_email not in refs:
        return jsonify({"error": "Referrer not found"}), 404
    refs[referrer_email]['paid_out'] = round(refs[referrer_email].get('paid_out', 0) + amount, 2)
    save_referrals(refs)
    return jsonify({"success": True, "message": f"Marked ${amount} paid to {referrer_email}"})

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

# =============================================================================
# EXTENDED FEATURES API
# =============================================================================

@app.route('/api/fetch-images', methods=['POST'])
@require_subscription
def api_fetch_images():
    """Auto-fetch card images from Beckett/Cardsmiths/eBay."""
    print(f"[FETCH-IMAGES] Request received", flush=True)
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Ensure .env loaded (Render uses env vars, local uses .env)
        serp_ok = bool((os.environ.get('SERPAPI_KEY') or '').strip())
        print(f"[FETCH-IMAGES] SERPAPI_KEY {'set' if serp_ok else 'NOT set'}", flush=True)
        from features.card_images import CardImageFetcher
        import re
        data = request.json or {}
        cards = data.get('cards', [])
        set_name = (data.get('setName') or '').strip()
        source_url = data.get('sourceUrl', '') or ''
        first = (cards[0].get('name'), cards[0].get('number')) if cards else (None, None)
        print(f"[FETCH-IMAGES] Cards: {len(cards)}, setName: '{set_name}', first: {first}", flush=True)
        if not set_name and source_url:
            m = re.search(r'/([a-z0-9\-]+?)(?:-hobby|-blaster|-retail|/)?$', source_url.lower())
            if m:
                slug = m.group(1)
                set_name = slug.replace('-', ' ').replace('  ', ' ').strip().title()
                print(f"[FETCH-IMAGES] Extracted setName from URL: '{set_name}'", flush=True)
        fetcher = CardImageFetcher()
        updated = fetcher.fetch_images_for_cards(cards, set_name, source_url)
        ph = getattr(fetcher, 'placeholder', '')
        with_img = sum(1 for c in updated if (c.get('image_url') or c.get('imageUrl')) and (c.get('image_url') or c.get('imageUrl')) != ph)
        print(f"[FETCH-IMAGES] Done: {with_img}/{len(updated)} cards with images (v{VERSION})", flush=True)
        resp = {"success": True, "cards": updated, "version": VERSION, "withImages": with_img}
        if with_img < len(updated) and not os.environ.get('SERPAPI_KEY', '').strip():
            resp["hint"] = "Add SERPAPI_KEY in .env (or Render env) for better image fetch. Free at serpapi.com"
        return jsonify(resp)
    except Exception as e:
        print(f"[FETCH-IMAGES] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/market-price', methods=['POST'])
@require_subscription
def api_market_price():
    """Look up sold prices for a card."""
    try:
        from features.market_prices import MarketPriceLookup
        data = request.json
        name = data.get('playerName', '')
        set_name = data.get('setName', '')
        number = data.get('cardNumber', '')
        lookup = MarketPriceLookup()
        result = lookup.get_ebay_sold_prices(name, set_name, number if number else None)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/apply-market-pricing', methods=['POST'])
@require_subscription
def api_apply_market_pricing():
    """For cards with qty>0: lookup eBay sold via SerpAPI. Max 15. Returns updated cards."""
    try:
        import time
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        from features.market_prices import MarketPriceLookup
        data = request.json or {}
        cards = data.get('cards', [])
        set_name = data.get('setName', '') or ''
        lookup = MarketPriceLookup()
        lookup_count = 0
        max_lookups = 15
        updated_count = 0
        no_results = []
        debug_msg = None
        for card in cards:
            if lookup_count >= max_lookups:
                continue
            name = card.get('name', '')
            number = str(card.get('number', ''))
            parallel_type = card.get('parallelType') or card.get('parallel_type') or ''
            result = lookup.get_ebay_sold_prices(name, set_name, number if number else None, parallel_type)
            if result.get('_debug') and debug_msg is None:
                debug_msg = result['_debug']
            lookup_count += 1
            suggested = result.get('suggested') or result.get('median') or result.get('avg') or result.get('last_sold') or result.get('min')
            if suggested and 0.25 < suggested < 10000:
                card['price'] = round(suggested, 2)
                updated_count += 1
            else:
                card['price'] = 1.0
                updated_count += 1
                no_results.append(name or 'Unknown')
            time.sleep(0.2)
        resp = {"success": True, "cards": cards, "updated": updated_count}
        if no_results:
            resp["no_results"] = no_results[:10]
        if debug_msg:
            resp["debug"] = debug_msg
        if not os.environ.get('SERPAPI_KEY', '').strip() and no_results:
            hint = "Add SERPAPI_KEY in Render Dashboard → Environment (or .env locally). Free at serpapi.com"
            resp["hint"] = hint
        return jsonify(resp)
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e), "debug": traceback.format_exc()[:500]}), 500

@app.route('/api/checklist-draft', methods=['GET', 'POST', 'DELETE'])
@require_subscription
def api_checklist_draft():
    """Save/load price-qty drafts keyed by checklist URL + type."""
    try:
        from features.checklist_drafts import ChecklistDraftManager, checklist_id_from_url
        email = session.get('user_email', '')
        dm = ChecklistDraftManager(user_email=email)
        if request.method == 'GET':
            url = request.args.get('url', '')
            ctype = request.args.get('type', 'base')
            cid = request.args.get('checklistId') or checklist_id_from_url(url, ctype)
            draft = dm.load_draft(cid)
            return jsonify({"success": True, "checklistId": cid, "draft": draft})
        elif request.method == 'POST':
            data = request.json or {}
            url = data.get('url', '')
            ctype = data.get('type', 'base')
            cid = data.get('checklistId') or checklist_id_from_url(url, ctype)
            cards = data.get('cards', [])
            meta = data.get('meta') or {}
            dm.save_draft(cid, cards, meta=meta)
            return jsonify({"success": True, "checklistId": cid})
        else:
            cid = request.args.get('checklistId', '')
            if cid:
                dm.delete_draft(cid)
            return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/presets', methods=['GET', 'POST', 'DELETE'])
@require_subscription
def api_presets():
    """CRUD for saved checklist presets."""
    try:
        from features.presets import PresetManager
        email = session.get('user_email', '')
        pm = PresetManager(user_email=email)
        if request.method == 'GET':
            return jsonify({"success": True, "presets": pm.list_presets()})
        elif request.method == 'POST':
            data = request.json
            pm.save_preset(
                name=data.get('name', ''),
                url=data.get('url', ''),
                checklist_type=data.get('type', 'base'),
                filters=data.get('filters')
            )
            return jsonify({"success": True})
        else:
            name = request.args.get('name', '')
            if name:
                pm.delete_preset(name)
            return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/apply-tiered-pricing', methods=['POST'])
@require_subscription
def api_apply_tiered_pricing():
    """Apply smart tiered pricing to cards."""
    try:
        from features.tiered_pricing import TieredPricingEngine
        data = request.json
        cards = data.get('cards', [])
        engine = TieredPricingEngine(
            base_price=float(data.get('basePrice', 1.00)),
            rookie_markup_pct=float(data.get('rookieMarkup', 50)),
            insert_markup_pct=float(data.get('insertMarkup', 30)),
            parallel_markup_pct=float(data.get('parallelMarkup', 25)),
            auto_price=float(data.get('autoPrice', 5.00))
        )
        updated = engine.apply_tiered_pricing(cards)
        return jsonify({"success": True, "cards": updated})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/templates', methods=['GET', 'POST', 'DELETE'])
@require_subscription
def api_templates():
    """CRUD for listing templates."""
    try:
        from features.listing_templates import ListingTemplateManager
        email = session.get('user_email', '')
        tm = ListingTemplateManager(user_email=email)
        if request.method == 'GET':
            return jsonify({"success": True, "templates": tm.list_templates()})
        elif request.method == 'POST':
            data = request.json
            tm.save_template(
                name=data.get('name', ''),
                title_template=data.get('titleTemplate', ''),
                description=data.get('description', ''),
                default_price=float(data.get('defaultPrice', 1.00)),
                images=data.get('images'),
                meta=data.get('meta')
            )
            return jsonify({"success": True})
        else:
            name = request.args.get('name', '')
            if name:
                tm.delete_template(name)
            return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/check-duplicates', methods=['POST'])
@require_subscription
def api_check_duplicates():
    """Check for potentially duplicate listings."""
    try:
        from features.duplicate_detection import DuplicateDetector
        data = request.json
        title = data.get('title', '')
        existing = data.get('existingListings', [])
        detector = DuplicateDetector()
        matches = detector.check_duplicates(title, existing, threshold=float(data.get('threshold', 0.6)))
        return jsonify({"success": True, "matches": [{"listing": m[0], "score": m[1]} for m in matches]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
@require_subscription
def api_analytics():
    """Get sales analytics summary."""
    try:
        from features.analytics import AnalyticsDashboard
        email = session.get('user_email', '')
        payments = load_payments()
        user_payments = [p for p in (payments if isinstance(payments, list) else []) if isinstance(p, dict) and p.get('email') == email]
        dashboard = AnalyticsDashboard(payments_data=user_payments)
        days = int(request.args.get('days', 30))
        summary = dashboard.get_sales_summary(days=days, user_email=email)
        best = dashboard.get_best_sellers(limit=10)
        return jsonify({"success": True, "summary": summary, "bestSellers": best})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/grading-aspects', methods=['POST'])
@require_subscription
def api_grading_aspects():
    """Get eBay item specifics for graded cards."""
    try:
        from features.grading import GradingHelper
        data = request.json
        helper = GradingHelper()
        aspects = helper.get_aspects_for_graded(
            grader=data.get('grader', 'PSA'),
            grade=data.get('grade', '10'),
            cert_number=data.get('certNumber')
        )
        return jsonify({"success": True, "aspects": aspects, "titleSuffix": helper.suggest_title_suffix(data.get('grader', 'PSA'), data.get('grade', '10'))})
    except Exception as e:
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
    # Auto-kill old Python processes to ensure fresh start (skip when LOCAL_DEV=1)
    import subprocess
    import sys
    import os
    
    local_dev = os.environ.get('LOCAL_DEV', '').lower() in ('1', 'true', 'yes')
    
    print("=" * 60)
    print("eBay Card Listing Tool")
    print(f"Server Version: {VERSION}")
    print("=" * 60)
    print()
    
    if not local_dev:
        print("[STARTUP] ========================================")
        print("[STARTUP] KILLING ALL PYTHON PROCESSES")
        print("[STARTUP] ========================================")
    else:
        print("[STARTUP] LOCAL_DEV=1 - Skipping process kill (safe for development)")
    
    if not local_dev and sys.platform == 'win32':
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
    elif not local_dev:
        # Linux/Mac
        try:
            subprocess.run(['pkill', '-9', 'python'], capture_output=True, timeout=5)
            time.sleep(2)
            print("[STARTUP] Killed all Python processes")
        except:
            print("[STARTUP] Process check complete (Unix)")
    
    if not local_dev:
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
    
    # Check if port 5001 is already in use
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 5001))
        sock.close()
        if result == 0:
            if local_dev:
                # Kill existing server on 5001 so we can start fresh
                try:
                    import subprocess as sp
                    if sys.platform == 'win32':
                        out = sp.run(['netstat', '-ano'], capture_output=True, text=True, timeout=5)
                        for line in out.stdout.splitlines():
                            if ':5001' in line and 'LISTENING' in line:
                                parts = line.split()
                                pid = parts[-1]
                                if pid.isdigit():
                                    print(f"[STARTUP] Killing existing server PID {pid} on port 5001...")
                                    sp.run(['taskkill', '/F', '/PID', pid], capture_output=True, timeout=5)
                                    time.sleep(4)  # Wait for socket release (TIME_WAIT)
                                    break
                    else:
                        out = sp.run(['lsof', '-ti', ':5001'], capture_output=True, text=True, timeout=5)
                        if out.stdout.strip():
                            pid = out.stdout.strip().split()[0]
                            print(f"[STARTUP] Killing existing server PID {pid}...")
                            sp.run(['kill', '-9', pid], capture_output=True, timeout=5)
                            time.sleep(4)
                except Exception as e:
                    print(f"[STARTUP] Could not kill existing process: {e}")
                # Re-check port
                sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock2.settimeout(1)
                result2 = sock2.connect_ex(('127.0.0.1', 5001))
                sock2.close()
                if result2 == 0:
                    print("[STARTUP] Port 5001 still in use after kill - exiting.")
                    sys.exit(1)
                print("[STARTUP] Port 5001 cleared, continuing...")
            else:
                # Non-local: aggressive kill
                print("=" * 60)
                print("[ALERT] Port 5001 is already in use! Attempting to clear...")
                print("=" * 60)
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'] if sys.platform == 'win32' else ['pkill', '-9', 'python'],
                                 capture_output=True, timeout=5)
                    time.sleep(3)
                    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock2.settimeout(1)
                    result2 = sock2.connect_ex(('127.0.0.1', 5001))
                    sock2.close()
                    if result2 == 0:
                        print("[STARTUP] Port still in use - exiting")
                        sys.exit(1)
                except Exception:
                    sys.exit(1)
    except Exception:
        pass
    
    # Reloader disabled - causes port conflicts on restart; user stops/restarts manually
    use_reloader = False
    try:
        app.run(debug=True, port=5001, threaded=True, use_reloader=use_reloader)
    except Exception as e:
        print(f"[FATAL ERROR] Flask app crashed: {e}")
        import traceback
        traceback.print_exc()
        print("\n[INFO] Attempting to restart...")
        time.sleep(2)
        app.run(debug=True, port=5001, threaded=True, use_reloader=use_reloader)
