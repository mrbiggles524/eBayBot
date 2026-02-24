"""eBay OAuth 2.0 authentication."""
import requests
import base64
import json
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional
from config import Config
import os

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback."""
    
    def do_GET(self):
        """Handle OAuth callback."""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            self.server.auth_code = query_params['code'][0]
            self.server.shutdown_flag = True  # Signal to shutdown
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = """
                <html>
                <head>
                    <title>Authentication Successful</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #4CAF50; }
                    </style>
                </head>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                    <p>The token has been saved automatically.</p>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
            self.wfile.flush()
            print("✓ Authorization code received via callback")
        elif 'error' in query_params:
            error = query_params.get('error', ['Unknown error'])[0]
            error_desc = query_params.get('error_description', [''])[0]
            self.server.shutdown_flag = True  # Signal to shutdown
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = f"""
                <html>
                <head>
                    <title>Authentication Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        h1 {{ color: #f44336; }}
                    </style>
                </head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p><strong>Error:</strong> {error}</p>
                    <p>{error_desc}</p>
                    <p>Please try again.</p>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
            self.wfile.flush()
            print(f"✗ Authorization error: {error} - {error_desc}")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = """
                <html>
                <head>
                    <title>Authentication Failed</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #f44336; }
                    </style>
                </head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p>No authorization code received.</p>
                    <p>Please try again.</p>
                </body>
                </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
            print("✗ No authorization code in callback")
    
    def log_message(self, format, *args):
        """Suppress server logs."""
        pass

class eBayOAuth:
    """Handles eBay OAuth 2.0 authentication."""
    
    def __init__(self):
        self.config = Config()
        self.sandbox_auth_url = "https://auth.sandbox.ebay.com/oauth2/authorize"
        self.production_auth_url = "https://auth.ebay.com/oauth2/authorize"
        self.sandbox_token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        self.production_token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        # Use redirect URI from config, fallback to default
        self.redirect_uri = self.config.OAUTH_REDIRECT_URI or "http://localhost:8080/callback"
        self.token_file = ".ebay_token.json"
    
    @property
    def auth_url(self):
        """Get the appropriate auth URL based on environment."""
        if self.config.EBAY_ENVIRONMENT == 'production':
            return self.production_auth_url
        return self.sandbox_auth_url
    
    @property
    def token_url(self):
        """Get the appropriate token URL based on environment."""
        if self.config.EBAY_ENVIRONMENT == 'production':
            return self.production_token_url
        return self.sandbox_token_url
    
    def get_authorization_url(self, scopes: list = None) -> str:
        """
        Generate the authorization URL for user login.
        
        Args:
            scopes: List of OAuth scopes (defaults to required scopes for listing)
            
        Returns:
            Authorization URL
        """
        if scopes is None:
            scopes = [
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.account",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
            ]
        
        params = {
            "client_id": self.config.EBAY_APP_ID,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes)
        }
        
        url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        return url
    
    def login(self, open_browser: bool = True) -> Dict:
        """
        Perform OAuth login flow.
        
        Args:
            open_browser: Whether to automatically open browser
            
        Returns:
            Dictionary with token information
        """
        print("Starting eBay OAuth login...")
        print(f"Environment: {self.config.EBAY_ENVIRONMENT}")
        
        # Generate authorization URL
        auth_url = self.get_authorization_url()
        print(f"\nPlease visit this URL to authorize the application:")
        print(f"{auth_url}\n")
        
        if open_browser:
            try:
                webbrowser.open(auth_url)
                print("Browser opened. Please authorize the application...")
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print("Please copy and paste the URL above into your browser.")
        
        # Start local server to receive callback
        print(f"Waiting for authorization callback on {self.redirect_uri}...")
        print("Make sure to complete the authorization in your browser and wait for the redirect...")
        
        server = None
        try:
            server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
            server.timeout = 1  # Short timeout for checking
            server.auth_code = None
            server.shutdown_flag = False
            
            # Wait for callback with timeout handling
            import time
            start_time = time.time()
            timeout_seconds = 300  # 5 minutes total
            
            while not server.shutdown_flag and (time.time() - start_time) < timeout_seconds:
                try:
                    server.handle_request()
                    if server.auth_code:
                        break
                except OSError as e:
                    if "Address already in use" in str(e):
                        return {
                            "success": False,
                            "error": "Port 8080 is already in use. Please close other applications using this port."
                        }
                    raise
                except Exception as e:
                    # Ignore timeout exceptions, continue waiting
                    if "timed out" not in str(e).lower():
                        raise
                    time.sleep(0.1)  # Small delay before next check
            
            # Shutdown server gracefully
            if server:
                try:
                    server.server_close()
                except:
                    pass
            
            if not server.auth_code:
                return {
                    "success": False,
                    "error": "No authorization code received. Login timed out or was cancelled. Please try again and complete the authorization within 5 minutes."
                }
            
            print("Authorization code received. Exchanging for access token...")
            
            # Exchange authorization code for access token
            return self.exchange_code_for_token(server.auth_code)
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            if server:
                try:
                    server.server_close()
                except:
                    pass
            return {
                "success": False,
                "error": "Login cancelled by user."
            }
        except Exception as e:
            if server:
                try:
                    server.server_close()
                except:
                    pass
            return {
                "success": False,
                "error": f"Error during OAuth callback: {str(e)}"
            }
    
    def exchange_code_for_token(self, auth_code: str) -> Dict:
        """
        Exchange authorization code for access token.
        
        Args:
            auth_code: Authorization code from OAuth callback
            
        Returns:
            Dictionary with token information
        """
        # Create Basic Auth header
        credentials = f"{self.config.EBAY_APP_ID}:{self.config.EBAY_CERT_ID}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        # Debug logging
        print(f"[DEBUG] Token exchange request:")
        print(f"  URL: {self.token_url}")
        print(f"  Redirect URI: {self.redirect_uri}")
        print(f"  Client ID: {self.config.EBAY_APP_ID[:20]}...")
        print(f"  Code: {auth_code[:20]}...")
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data, timeout=30)
            
            # Check for server errors
            if response.status_code == 500:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    error_data = {"error_description": response.text}
                
                return {
                    "success": False,
                    "error": error_data,
                    "error_type": "server_error",
                    "message": "eBay authorization server is temporarily unavailable. Please try again in a few minutes."
                }
            
            # Check for HTTP errors before parsing JSON
            if response.status_code != 200:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    error_data = {"error_description": response.text}
                
                error_type = error_data.get('error', 'unknown_error')
                error_desc = error_data.get('error_description', 'Unknown error')
                
                # Provide specific guidance for common errors
                if error_type == 'unauthorized_client':
                    error_desc += "\n\n🔧 **FIX: OAuth client not found**\n"
                    error_desc += "This means your APP_ID or CERT_ID is incorrect.\n"
                    error_desc += "1. Check your .env file - verify EBAY_APP_ID and EBAY_CERT_ID\n"
                    error_desc += "2. Make sure you're using PRODUCTION keys, not Sandbox keys\n"
                    error_desc += "3. Go to eBay Developer Portal → My Account → Application Keys\n"
                    error_desc += "4. Copy the correct App ID (Client ID) and Cert ID (Client Secret)\n"
                    error_desc += "5. Update your .env file and restart the application\n"
                elif error_type == 'invalid_request':
                    error_desc += "\n\n💡 **Common causes:**\n"
                    error_desc += f"- Redirect URI mismatch. Current: `{self.redirect_uri}`\n"
                    error_desc += "- Make sure this exact URI is registered in eBay Developer Console\n"
                    error_desc += "- For Sandbox: Use `http://localhost:8080/callback`\n"
                    error_desc += "- Check that redirect URI matches exactly (including http vs https)\n"
                
                return {
                    "success": False,
                    "error": error_data,
                    "error_type": error_type,
                    "message": error_desc
                }
            
            response.raise_for_status()
            
            token_data = response.json()
            
            # Save token to file
            self.save_token(token_data)
            
            print("[OK] Login successful! Token saved.")
            
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in"),
                "refresh_token": token_data.get("refresh_token"),
                "scope": token_data.get("scope")
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": {"error_description": "Request timed out. eBay servers may be slow. Please try again."},
                "error_type": "timeout"
            }
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (400, 401, etc.)
            error_data = {}
            try:
                if e.response is not None:
                    error_data = e.response.json()
            except:
                if e.response is not None:
                    error_data = {"error_description": e.response.text}
            
            error_type = error_data.get('error', 'unknown_error')
            error_desc = error_data.get('error_description', str(e))
            
            # Provide specific guidance for common errors
            if error_type == 'unauthorized_client':
                error_desc += "\n\n🔧 **FIX: OAuth client not found**\n"
                error_desc += "This means your APP_ID or CERT_ID is incorrect.\n"
                error_desc += "1. Check your .env file - verify EBAY_APP_ID and EBAY_CERT_ID\n"
                error_desc += "2. Make sure you're using PRODUCTION keys, not Sandbox keys\n"
                error_desc += "3. Go to eBay Developer Portal → My Account → Application Keys\n"
                error_desc += "4. Copy the correct App ID (Client ID) and Cert ID (Client Secret)\n"
                error_desc += "5. Update your .env file and restart the application\n"
            elif error_type == 'invalid_request':
                error_desc += "\n\n💡 **Common causes:**\n"
                error_desc += f"- Redirect URI mismatch. Current: `{self.redirect_uri}`\n"
                error_desc += "- Make sure this exact URI is registered in eBay Developer Console\n"
                error_desc += "- For Sandbox: Use `http://localhost:8080/callback`\n"
                error_desc += "- Check that redirect URI matches exactly (including http vs https)\n"
            
            return {
                "success": False,
                "error": error_data,
                "error_type": error_type,
                "message": error_desc
            }
        except requests.exceptions.RequestException as e:
            error_msg = {}
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg = e.response.json()
                except:
                    error_msg = {"error_description": e.response.text if hasattr(e.response, 'text') else str(e)}
            else:
                error_msg = {"error_description": str(e)}
            
            return {
                "success": False,
                "error": error_msg,
                "error_type": "request_error"
            }
    
    def refresh_token(self, refresh_token: str = None) -> Dict:
        """
        Refresh an access token using refresh token.
        
        Args:
            refresh_token: Refresh token (if None, loads from saved token)
            
        Returns:
            Dictionary with new token information
        """
        if refresh_token is None:
            token_data = self.load_token()
            if not token_data or 'refresh_token' not in token_data:
                return {
                    "success": False,
                    "error": "No refresh token available. Please login again."
                }
            refresh_token = token_data['refresh_token']
        
        # Create Basic Auth header
        credentials = f"{self.config.EBAY_APP_ID}:{self.config.EBAY_CERT_ID}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": "https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.marketing"
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Update saved token
            saved_token = self.load_token() or {}
            saved_token.update({
                "access_token": token_data.get("access_token"),
                "expires_in": token_data.get("expires_in"),
                "token_type": token_data.get("token_type")
            })
            self.save_token(saved_token)
            
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "token_type": token_data.get("token_type"),
                "expires_in": token_data.get("expires_in")
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to refresh token: {e}"
            if hasattr(e.response, 'text'):
                error_msg += f" - {e.response.text}"
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_access_token(self, auto_refresh: bool = True) -> Optional[str]:
        """
        Get current access token, refreshing if needed.
        
        Args:
            auto_refresh: Whether to automatically refresh expired tokens
            
        Returns:
            Access token or None
        """
        token_data = self.load_token()
        
        if not token_data:
            return None
        
        # Check if token is expired (with 5 minute buffer)
        import time
        if 'expires_at' in token_data:
            if time.time() >= token_data['expires_at'] - 300:
                if auto_refresh:
                    print("Token expired. Refreshing...")
                    refresh_result = self.refresh_token()
                    if refresh_result.get('success'):
                        return refresh_result.get('access_token')
                return None
        
        return token_data.get('access_token')
    
    def save_token(self, token_data: Dict):
        """Save token data to file."""
        import time
        if 'expires_in' in token_data:
            token_data['expires_at'] = time.time() + token_data['expires_in']
        
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
    
    def load_token(self) -> Optional[Dict]:
        """Load token data from file."""
        if not os.path.exists(self.token_file):
            return None
        
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def logout(self):
        """Remove saved token (logout)."""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            print("Logged out. Token removed.")
        else:
            print("No saved token found.")
