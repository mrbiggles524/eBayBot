"""Configuration management for eBay Bot."""
import os
from dotenv import load_dotenv

# Load .env file (will be reloaded when needed)
load_dotenv()

class Config:
    """Configuration class for eBay API and bot settings."""
    
    # eBay API Credentials (properties that read from os.getenv each time)
    @property
    def EBAY_APP_ID(self):
        return os.getenv('EBAY_APP_ID', '')
    
    @property
    def EBAY_DEV_ID(self):
        return os.getenv('EBAY_DEV_ID', '')
    
    @property
    def EBAY_CERT_ID(self):
        return os.getenv('EBAY_CERT_ID', '')
    
    @property
    def EBAY_SANDBOX_TOKEN(self):
        return os.getenv('EBAY_SANDBOX_TOKEN', '')
    
    @property
    def EBAY_PRODUCTION_TOKEN(self):
        return os.getenv('EBAY_PRODUCTION_TOKEN', '')
    
    @property
    def EBAY_ENVIRONMENT(self):
        return os.getenv('EBAY_ENVIRONMENT', 'sandbox')
    
    # OAuth Settings
    @property
    def USE_OAUTH(self):
        return os.getenv('USE_OAUTH', 'true').lower() == 'true'
    
    @property
    def OAUTH_REDIRECT_URI(self):
        # On Render, default to the service URL if not explicitly set
        if os.getenv('RENDER') == 'true' and os.getenv('RENDER_EXTERNAL_URL'):
            return os.getenv('OAUTH_REDIRECT_URI') or f"{os.getenv('RENDER_EXTERNAL_URL')}/callback"
        return os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8080/callback')
    
    # Card Data Source
    @property
    def CARD_DATA_SOURCE(self):
        return os.getenv('CARD_DATA_SOURCE', 'tcgplayer')
    
    @property
    def TCGPLAYER_API_KEY(self):
        return os.getenv('TCGPLAYER_API_KEY', '')
    
    # Default Listing Settings
    @property
    def DEFAULT_CONDITION(self):
        return os.getenv('DEFAULT_CONDITION', 'Like New')
    
    @property
    def DEFAULT_LISTING_TYPE(self):
        return os.getenv('DEFAULT_LISTING_TYPE', 'FixedPriceItem')
    
    @property
    def DEFAULT_DURATION(self):
        return os.getenv('DEFAULT_DURATION', 'GTC')
    
    @property
    def DEFAULT_PAYMENT_METHOD(self):
        return os.getenv('DEFAULT_PAYMENT_METHOD', 'PayPal')
    
    # eBay Policy IDs (optional - will try to fetch if not set)
    @property
    def FULFILLMENT_POLICY_ID(self):
        return os.getenv('FULFILLMENT_POLICY_ID', '')
    
    @property
    def BASE_CARDS_FULFILLMENT_POLICY_ID(self):
        return os.getenv('BASE_CARDS_FULFILLMENT_POLICY_ID', '')
    
    @property
    def PAYMENT_POLICY_ID(self):
        return os.getenv('PAYMENT_POLICY_ID', '')
    
    @property
    def RETURN_POLICY_ID(self):
        return os.getenv('RETURN_POLICY_ID', '')
    
    @property
    def MERCHANT_LOCATION_KEY(self):
        return os.getenv('MERCHANT_LOCATION_KEY', '')
    
    # Retry settings
    @property
    def MAX_RETRIES(self):
        return int(os.getenv('MAX_RETRIES', '3'))
    
    @property
    def RETRY_DELAY(self):
        return float(os.getenv('RETRY_DELAY', '1.0'))
    
    # eBay API Endpoints
    @property
    def ebay_token(self):
        """Get the appropriate eBay token based on environment."""
        # Force reload .env to get latest token
        load_dotenv(override=True)
        
        # Try OAuth token first if enabled
        if self.USE_OAUTH:
            try:
                from ebay_oauth import eBayOAuth
                oauth = eBayOAuth()
                token = oauth.get_access_token()
                if token:
                    return token
            except Exception as e:
                print(f"[DEBUG] OAuth token fetch failed: {e}")
                pass  # Fall back to static token
        
        # Fall back to static token (can be manually set User Token)
        if self.EBAY_ENVIRONMENT == 'production':
            token = self.EBAY_PRODUCTION_TOKEN
            if not token:
                print("[WARNING] EBAY_PRODUCTION_TOKEN is empty")
            return token
        return self.EBAY_SANDBOX_TOKEN
    
    @property
    def ebay_api_url(self):
        """Get the appropriate eBay API URL based on environment."""
        if self.EBAY_ENVIRONMENT == 'production':
            return 'https://api.ebay.com'
        return 'https://api.sandbox.ebay.com'
    
    def validate(self, require_token: bool = True):
        """Validate that required configuration is present."""
        required = ['EBAY_APP_ID', 'EBAY_DEV_ID', 'EBAY_CERT_ID']
        missing = [key for key in required if not getattr(self, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        if require_token and not self.ebay_token:
            if self.USE_OAUTH:
                raise ValueError("No OAuth token found. Please run 'python ebay_bot.py --login' first.")
            else:
                raise ValueError("Missing eBay token for selected environment. Set EBAY_SANDBOX_TOKEN or EBAY_PRODUCTION_TOKEN, or use OAuth login.")
