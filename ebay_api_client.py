"""Improved eBay API client with better error handling and policy management."""
import requests
import time
import json
from typing import Dict, List, Optional
from config import Config

class eBayAPIClient:
    """Enhanced eBay API client with retry logic and policy management."""
    
    def __init__(self, token_override: Optional[str] = None):
        """Optional token_override: per-user token (e.g. from user_tokens.json)."""
        self.config = Config()
        self.config.validate()
        self.base_url = self.config.ebay_api_url
        self.token_override = token_override
        self.token = token_override or self.config.ebay_token
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with current token."""
        # Use per-user token if set
        if self.token_override:
            self.token = self.token_override
        else:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            self.token = self.config.ebay_token
        if not self.token:
            raise ValueError("No eBay token available. Please check your .env file or run OAuth login.")
        
        # Debug: Print token preview (first 50 chars) - only in debug mode
        # print(f"[DEBUG] Using token: {self.token[:50]}... (length: {len(self.token)})")
        
        # Clear any existing headers first to avoid conflicts
        self.session.headers.clear()
        # Set required headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Language": "en-US"  # Explicitly set valid Content-Language
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retries: int = None
    ) -> requests.Response:
        """Make API request with retry logic."""
        retries = retries or self.config.MAX_RETRIES
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params)
                elif method.upper() == 'POST':
                    # For POST requests, log the exact data being sent (especially for offers)
                    if data:
                        import json as json_module
                        try:
                            request_body = json_module.dumps(data, indent=2)
                            
                            # CRITICAL: Check for description in POST requests (create_offer)
                            parsed_data = json_module.loads(request_body)
                            
                            description_found = False
                            description_value = None
                            description_location = None
                            
                            if 'listing' in parsed_data:
                                if 'description' in parsed_data['listing']:
                                    description_found = True
                                    description_value = parsed_data['listing']['description']
                                    description_location = 'listing.description'
                            
                            if 'description' in parsed_data:
                                description_found = True
                                description_value = parsed_data['description']
                                description_location = 'root.description'
                            
                            print(f"[DEBUG] ========== FULL POST REQUEST BODY ==========")
                            print(request_body)
                            print(f"[DEBUG] ===========================================")
                            print(f"[DEBUG] DESCRIPTION CHECK:")
                            print(f"  Found: {description_found}")
                            if description_found:
                                print(f"  Location: {description_location}")
                                print(f"  Value: {description_value[:100] if description_value else 'None'}...")
                                print(f"  Length: {len(description_value) if description_value else 0}")
                                print(f"  Is valid: {bool(description_value and description_value.strip() and len(str(description_value).strip()) >= 50)}")
                            else:
                                print(f"  [ERROR] NO DESCRIPTION FOUND IN POST REQUEST!")
                                print(f"  Available keys: {list(parsed_data.keys())}")
                                if 'listing' in parsed_data:
                                    print(f"  Listing keys: {list(parsed_data['listing'].keys())}")
                        except Exception as e:
                            print(f"[DEBUG] Could not serialize POST request body for logging: {e}")
                    
                    response = self.session.post(url, json=data, params=params)
                    
                    # Log response for POST too
                    if '/offer' in endpoint:
                        print(f"[DEBUG] ========== POST OFFER RESPONSE ==========")
                        print(f"[DEBUG] Status Code: {response.status_code}")
                    try:
                        response_json = response.json()
                        print(json_module.dumps(response_json, indent=2))
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] Response is not valid JSON: {e}")
                        print(f"[DEBUG] Response text (first 1000 chars): {response.text[:1000]}")
                        print(f"[DEBUG] Response headers: {dict(response.headers)}")
                    except Exception as e:
                        print(f"[DEBUG] Error parsing response: {e}")
                        print(response.text[:1000])
                        print(f"[DEBUG] ======================================")
                elif method.upper() == 'PUT':
                    # For PUT requests, log the exact data being sent
                    if data:
                        import json as json_module
                        try:
                            request_body = json_module.dumps(data, indent=2)
                            
                            # CRITICAL: Check for description in request
                            parsed_data = json_module.loads(request_body)
                            
                            # Check for description
                            description_found = False
                            description_value = None
                            description_location = None
                            
                            if 'listing' in parsed_data:
                                if 'description' in parsed_data['listing']:
                                    description_found = True
                                    description_value = parsed_data['listing']['description']
                                    description_location = 'listing.description'
                            
                            if 'description' in parsed_data:
                                description_found = True
                                description_value = parsed_data['description']
                                description_location = 'root.description'
                            
                            print(f"[DEBUG] ========== FULL {method} REQUEST BODY ==========")
                            print(request_body)
                            print(f"[DEBUG] ===========================================")
                            print(f"[DEBUG] DESCRIPTION CHECK:")
                            print(f"  Found: {description_found}")
                            if description_found:
                                print(f"  Location: {description_location}")
                                print(f"  Value: {description_value[:100] if description_value else 'None'}...")
                                print(f"  Length: {len(description_value) if description_value else 0}")
                                print(f"  Is valid: {bool(description_value and description_value.strip() and len(str(description_value).strip()) >= 50)}")
                            else:
                                print(f"  [ERROR] NO DESCRIPTION FOUND IN REQUEST!")
                                print(f"  Available keys: {list(parsed_data.keys())}")
                                if 'listing' in parsed_data:
                                    print(f"  Listing keys: {list(parsed_data['listing'].keys())}")
                            
                            # Check for variationInformation in various locations
                            if 'groupDetails' in parsed_data:
                                print(f"[DEBUG] [OK] groupDetails found in request")
                                if 'variationInformation' in parsed_data['groupDetails']:
                                    print(f"[DEBUG] [OK] groupDetails.variationInformation found")
                                    var_info = parsed_data['groupDetails']['variationInformation']
                                    print(f"[DEBUG] variationInformation content: {json_module.dumps(var_info, indent=2)}")
                                else:
                                    print(f"[DEBUG] [ERROR] variationInformation NOT in groupDetails")
                                    print(f"[DEBUG] groupDetails keys: {list(parsed_data['groupDetails'].keys())}")
                            else:
                                print(f"[DEBUG] [ERROR] groupDetails NOT found in request")
                            
                            # Check inventoryItemGroup
                            if 'inventoryItemGroup' in parsed_data:
                                print(f"[DEBUG] [OK] inventoryItemGroup found")
                                print(f"[DEBUG] inventoryItemGroup keys: {list(parsed_data['inventoryItemGroup'].keys())}")
                            
                            # Check variantSKUs
                            if 'variantSKUs' in parsed_data:
                                print(f"[DEBUG] [OK] variantSKUs found: {len(parsed_data['variantSKUs'])} SKUs")
                            
                        except Exception as e:
                            print(f"[DEBUG] Could not serialize request body for logging: {e}")
                            import traceback
                            traceback.print_exc()
                    response = self.session.put(url, json=data, params=params)
                    
                    # Log full response
                    print(f"[DEBUG] ========== RESPONSE STATUS ==========")
                    print(f"[DEBUG] Status Code: {response.status_code}")
                    print(f"[DEBUG] Response Headers: {dict(response.headers)}")
                    print(f"[DEBUG] Full Response Body:")
                    try:
                        response_json = response.json()
                        print(json_module.dumps(response_json, indent=2))
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] Response is not valid JSON: {e}")
                        print(f"[DEBUG] Response text (first 2000 chars): {response.text[:2000]}")
                        print(f"[DEBUG] Response headers: {dict(response.headers)}")
                    except Exception as e:
                        print(f"[DEBUG] Error parsing response: {e}")
                        print(response.text[:2000])
                    print(f"[DEBUG] ======================================")
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check if response is HTML instead of JSON (common when auth fails or endpoint is wrong)
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type or (response.text and response.text.strip().startswith('<!DOCTYPE')):
                    print(f"[ERROR] ========== HTML RESPONSE DETECTED ==========")
                    print(f"[ERROR] eBay returned HTML instead of JSON!")
                    print(f"[ERROR] Status Code: {response.status_code}")
                    print(f"[ERROR] Content-Type: {content_type}")
                    print(f"[ERROR] This usually means:")
                    print(f"[ERROR]   1. Authentication failed (token expired/invalid)")
                    print(f"[ERROR]   2. Endpoint URL is incorrect")
                    print(f"[ERROR]   3. API base URL is wrong")
                    print(f"[ERROR] Response preview (first 500 chars):")
                    print(response.text[:500])
                    print(f"[ERROR] ===========================================")
                    # Don't try to parse as JSON - return response as-is
                    return response
                
                # Handle 401 Unauthorized - token might be expired
                if response.status_code == 401:
                    print(f"Token expired (401). Attempting to refresh...")
                    if self.config.USE_OAUTH:
                        from ebay_oauth import eBayOAuth
                        oauth = eBayOAuth()
                        refresh_result = oauth.refresh_token()
                        if refresh_result.get('success'):
                            print("Token refreshed successfully!")
                            self._update_headers()
                            if attempt < retries:
                                continue
                        else:
                            print(f"Token refresh failed: {refresh_result.get('error')}")
                    else:
                        print("OAuth not enabled. Please refresh token manually in Step 2.")
                    return response
                
                # Retry on rate limit or server errors
                if response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', self.config.RETRY_DELAY))
                    if attempt < retries:
                        time.sleep(retry_after)
                        continue
                elif response.status_code >= 500 and attempt < retries:  # Server error
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    time.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                raise
        
        return response
    
    def get_fulfillment_policies(self) -> Dict:
        """Get available fulfillment policies. Returns dict with 'policies' and 'error'."""
        try:
            # Add marketplaceId parameter
            response = self._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
            if response.status_code == 200:
                policies = response.json().get('fulfillmentPolicies', [])
                return {'policies': policies, 'error': None}
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get('errors', [{}])[0].get('message', error_text)
                except:
                    pass
                return {'policies': [], 'error': f"HTTP {response.status_code}: {error_text}"}
        except Exception as e:
            return {'policies': [], 'error': str(e)}
    
    def get_payment_policies(self) -> Dict:
        """Get available payment policies. Returns dict with 'policies' and 'error'."""
        try:
            response = self._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
            if response.status_code == 200:
                policies = response.json().get('paymentPolicies', [])
                return {'policies': policies, 'error': None, 'success': True}
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get('errors', [{}])[0].get('message', error_text)
                except:
                    pass
                return {'policies': [], 'error': f"HTTP {response.status_code}: {error_text}", 'success': False}
        except Exception as e:
            return {'policies': [], 'error': str(e), 'success': False}
    
    def get_return_policies(self) -> Dict:
        """Get available return policies. Returns dict with 'policies' and 'error'."""
        try:
            response = self._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
            if response.status_code == 200:
                policies = response.json().get('returnPolicies', [])
                return {'policies': policies, 'error': None, 'success': True}
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get('errors', [{}])[0].get('message', error_text)
                except:
                    pass
                return {'policies': [], 'error': f"HTTP {response.status_code}: {error_text}", 'success': False}
        except Exception as e:
            return {'policies': [], 'error': str(e), 'success': False}
    
    def get_merchant_locations(self) -> Dict:
        """Get available merchant locations. Returns dict with 'locations' and 'error'."""
        try:
            response = self._make_request('GET', '/sell/inventory/v1/location')
            if response.status_code == 200:
                locations = response.json().get('locations', [])
                return {'locations': locations, 'error': None}
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get('errors', [{}])[0].get('message', error_text)
                except:
                    pass
                return {'locations': [], 'error': f"HTTP {response.status_code}: {error_text}"}
        except Exception as e:
            return {'locations': [], 'error': str(e)}
    
    def create_merchant_location(self, merchant_location_key: str, name: str = "Default Location", address: Dict = None) -> Dict:
        """
        Create a merchant location.
        
        Args:
            merchant_location_key: Unique identifier for the location
            name: Name of the location
            address: Address dict with addressLine1, city, stateOrProvince, postalCode, country
            
        Returns:
            Dictionary with success status and location key
        """
        if address is None:
            # Default address (can be updated later)
            address = {
                "addressLine1": "123 Main St",
                "city": "Anytown",
                "stateOrProvince": "CA",
                "postalCode": "12345",
                "country": "US"
            }
        
        location_data = {
            "location": {
                "address": address
            },
            "name": name,
            "locationTypes": ["WAREHOUSE"],
            "merchantLocationStatus": "ENABLED"
        }
        
        try:
            endpoint = f"/sell/inventory/v1/location/{merchant_location_key}"
            response = self._make_request('POST', endpoint, data=location_data)
            
            if response.status_code in [200, 201, 204]:
                return {
                    "success": True,
                    "merchant_location_key": merchant_location_key,
                    "message": "Merchant location created successfully"
                }
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    errors = error_json.get('errors', [])
                    if errors:
                        error_text = errors[0].get('message', error_text)
                except:
                    pass
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_token_scopes(self) -> Dict:
        """
        Verify that the current token has required scopes by making a test API call.
        Returns dict with 'valid', 'has_inventory_scope', and 'error' keys.
        """
        try:
            # Try to access inventory API - if it works, token has sell.inventory scope
            response = self._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 1})
            
            if response.status_code == 200:
                return {
                    'valid': True,
                    'has_inventory_scope': True,
                    'error': None
                }
            elif response.status_code == 403:
                # Check error ID
                try:
                    error_json = response.json()
                    errors = error_json.get('errors', [])
                    if errors and errors[0].get('errorId') == '1100':
                        return {
                            'valid': True,  # Token is valid but missing scope
                            'has_inventory_scope': False,
                            'error': 'Token missing sell.inventory scope (Error ID: 1100)'
                        }
                except:
                    pass
                return {
                    'valid': True,
                    'has_inventory_scope': False,
                    'error': 'Access denied - token may be missing required scopes'
                }
            elif response.status_code == 401:
                return {
                    'valid': False,
                    'has_inventory_scope': False,
                    'error': 'Token is invalid or expired (401 Unauthorized)'
                }
            else:
                return {
                    'valid': True,  # Token might be valid, just can't access this endpoint
                    'has_inventory_scope': None,  # Unknown
                    'error': f'HTTP {response.status_code}: {response.text[:200]}'
                }
        except Exception as e:
            return {
                'valid': None,
                'has_inventory_scope': None,
                'error': str(e)
            }
    
    def get_policy_ids(self) -> Dict[str, str]:
        """Get or use configured policy IDs."""
        policies = {
            'fulfillment_policy_id': self.config.FULFILLMENT_POLICY_ID,
            'base_cards_fulfillment_policy_id': self.config.BASE_CARDS_FULFILLMENT_POLICY_ID,
            'payment_policy_id': self.config.PAYMENT_POLICY_ID,
            'return_policy_id': self.config.RETURN_POLICY_ID,
            'merchant_location_key': self.config.MERCHANT_LOCATION_KEY
        }
        
        # Try to fetch if not configured
        if not policies['fulfillment_policy_id']:
            fulfillment_result = self.get_fulfillment_policies()
            fulfillment_policies = fulfillment_result.get('policies', [])
            if fulfillment_policies:
                policies['fulfillment_policy_id'] = fulfillment_policies[0].get('fulfillmentPolicyId', '')
        
        # If base cards policy not set, default to regular fulfillment policy
        if not policies['base_cards_fulfillment_policy_id']:
            policies['base_cards_fulfillment_policy_id'] = policies['fulfillment_policy_id']
        
        if not policies['payment_policy_id']:
            payment_result = self.get_payment_policies()
            payment_policies = payment_result.get('policies', [])
            if payment_policies:
                policies['payment_policy_id'] = payment_policies[0].get('paymentPolicyId', '')
        
        if not policies['return_policy_id']:
            return_result = self.get_return_policies()
            return_policies = return_result.get('policies', [])
            if return_policies:
                policies['return_policy_id'] = return_policies[0].get('returnPolicyId', '')
        
        if not policies['merchant_location_key']:
            location_result = self.get_merchant_locations()
            locations = location_result.get('locations', [])
            if locations:
                policies['merchant_location_key'] = locations[0].get('merchantLocationKey', '')
        
        return policies
    
    def create_inventory_item(self, sku: str, item_data: Dict) -> Dict:
        """Create or update an inventory item."""
        endpoint = f"/sell/inventory/v1/inventory_item/{sku}"
        response = self._make_request('PUT', endpoint, data=item_data)
        
        if response.status_code in [200, 201, 204]:
            return {"success": True, "sku": sku}
        else:
            # Try to parse error message from JSON
            error_msg = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('message', error_msg)
                        error_id = errors[0].get('errorId', '')
                        if error_id:
                            error_msg = f"{error_msg} (Error ID: {error_id})"
            except:
                pass
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
    
    def get_inventory_item_group(self, group_key: str) -> Dict:
        """Get an inventory item group to verify it exists."""
        endpoint = f"/sell/inventory/v1/inventory_item_group/{group_key}"
        response = self._make_request('GET', endpoint)
        
        if response.status_code == 200:
            try:
                return {"success": True, "data": response.json()}
            except json.JSONDecodeError as e:
                print(f"[ERROR] Response is not valid JSON: {e}")
                print(f"[ERROR] Response text: {response.text[:1000]}")
                return {"success": False, "error": f"Invalid JSON response: {str(e)}", "status_code": response.status_code, "raw_response": response.text[:1000]}
        else:
            error_text = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        error_text = errors[0].get('message', error_text)
            except:
                pass
            return {"success": False, "error": error_text, "status_code": response.status_code}
    
    def delete_inventory_item_group(self, group_key: str) -> Dict:
        """Delete an inventory item group."""
        endpoint = f"/sell/inventory/v1/inventory_item_group/{group_key}"
        response = self._make_request('DELETE', endpoint)
        
        if response.status_code in [200, 204]:
            return {"success": True}
        else:
            error_text = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('message', error_text)
                        return {"success": False, "error": error_msg}
            except:
                pass
            return {"success": False, "error": error_text}
    
    def create_inventory_item_group(self, group_key: str, group_data: Dict) -> Dict:
        """Create or update an inventory item group."""
        # Validate group key format (eBay requires alphanumeric only, max 50 chars)
        import re
        # Clean the group key to ensure it's alphanumeric only
        clean_group_key = re.sub(r'[^A-Z0-9]', '', str(group_key).upper())
        if len(clean_group_key) > 50:
            clean_group_key = clean_group_key[:50]
        if len(clean_group_key) < 1:
            clean_group_key = f"GROUP{int(time.time())}"
        
        if clean_group_key != group_key:
            print(f"[WARNING] Group key cleaned: '{group_key}' -> '{clean_group_key}'")
            group_key = clean_group_key
        
        print(f"[DEBUG] Using group key: {group_key} (length: {len(group_key)}, alphanumeric: {group_key.isalnum()})")
        
        # eBay API: PUT /sell/inventory/v1/inventory_item_group/{inventoryItemGroupKey}
        endpoint = f"/sell/inventory/v1/inventory_item_group/{group_key}"
        
        # Create a clean copy - title should be at ROOT level, not inside inventoryItemGroup
        clean_data = {}
        
        # Copy title from ROOT level (eBay API requirement)
        if 'title' in group_data:
            title_value = group_data['title']
            print(f"[DEBUG] Found title at ROOT level: {repr(title_value)} (type: {type(title_value)})")
            
            if title_value is not None:
                # Ensure it's a string
                if not isinstance(title_value, str):
                    title_value = str(title_value)
                    print(f"[DEBUG] Converted title to string: '{title_value}'")
                
                # Strip and validate
                title_value = title_value.strip()
                
                # Validate length using byte length (eBay uses UTF-8)
                if len(title_value) == 0:
                    print("[ERROR] Title is empty after stripping!")
                else:
                    byte_length = len(title_value.encode('utf-8'))
                    if byte_length > 80:
                        # Truncate if too long
                        title_bytes = title_value.encode('utf-8')[:80]
                        title_value = title_bytes.decode('utf-8', errors='ignore').strip()
                        if not title_value:
                            print("[ERROR] Title became empty after truncation!")
                    
                    if title_value and 1 <= len(title_value) <= 80:
                        # Set at ROOT level - this is the correct location!
                        clean_data['title'] = str(title_value)
                        print(f"[DEBUG] [OK] Title set at ROOT level: '{clean_data['title']}'")
                    else:
                        print(f"[ERROR] Title validation failed: len={len(title_value) if title_value else 0}")
            else:
                print("[ERROR] Title value is None at ROOT level!")
        else:
            print("[WARNING] No 'title' key at ROOT level in group_data")
        
        # Copy variesBy at root level (per eBay API docs - this is the correct location)
        if 'variesBy' in group_data:
            clean_data['variesBy'] = group_data['variesBy']
            if 'specifications' in group_data['variesBy']:
                print(f"[DEBUG] [OK] Copied variesBy at ROOT with {len(group_data['variesBy']['specifications'])} specifications")
        
        # Copy groupDetails if present (for compatibility)
        if 'groupDetails' in group_data:
            clean_data['groupDetails'] = group_data['groupDetails']
            if 'variationInformation' in group_data['groupDetails']:
                print(f"[DEBUG] [OK] Copied groupDetails.variationInformation with {len(group_data['groupDetails']['variationInformation'].get('specifications', []))} specifications")
        
        # Copy inventoryItemGroup (without title - title is at root)
        # CRITICAL: If inventoryItemGroup doesn't exist, create it with description
        if 'inventoryItemGroup' in group_data:
            clean_data['inventoryItemGroup'] = {}
            # Copy aspects (required)
            if 'aspects' in group_data['inventoryItemGroup']:
                clean_data['inventoryItemGroup']['aspects'] = group_data['inventoryItemGroup']['aspects']
            # Copy variesBy container
            if 'variesBy' in group_data['inventoryItemGroup']:
                clean_data['inventoryItemGroup']['variesBy'] = group_data['inventoryItemGroup']['variesBy']
                print(f"[DEBUG] [OK] Copied variesBy container with {len(group_data['inventoryItemGroup']['variesBy'].get('specifications', []))} specifications")
            # CRITICAL: Copy description (REQUIRED for variation listings)
            if 'description' in group_data['inventoryItemGroup']:
                desc_value = group_data['inventoryItemGroup']['description']
                if desc_value and isinstance(desc_value, str) and len(desc_value.strip()) >= 50:
                    clean_data['inventoryItemGroup']['description'] = desc_value
                    print(f"[DEBUG] [CRITICAL] Copied description to inventoryItemGroup (length: {len(desc_value)})")
                    print(f"[DEBUG] Description preview: {desc_value[:100]}...")
                else:
                    print(f"[DEBUG] [WARNING] Description in inventoryItemGroup is invalid (length: {len(desc_value) if desc_value else 0})")
            # Do NOT copy title from inventoryItemGroup - it should be at root level
            # NOTE: imageUrls should be at ROOT level, not in inventoryItemGroup (per eBay API docs)
        else:
            # CRITICAL: If inventoryItemGroup doesn't exist but description is at root, move it
            if 'description' in group_data:
                print(f"[DEBUG] [FIX] Description found at root level - moving to inventoryItemGroup")
                if 'inventoryItemGroup' not in clean_data:
                    clean_data['inventoryItemGroup'] = {}
                desc_value = group_data['description']
                if desc_value and isinstance(desc_value, str) and len(desc_value.strip()) >= 50:
                    clean_data['inventoryItemGroup']['description'] = desc_value
                    print(f"[DEBUG] [CRITICAL] Moved description from root to inventoryItemGroup (length: {len(desc_value)})")
                else:
                    print(f"[DEBUG] [WARNING] Root description is invalid (length: {len(desc_value) if desc_value else 0})")
            else:
                # Create inventoryItemGroup structure if it doesn't exist
                clean_data['inventoryItemGroup'] = {}
                print(f"[DEBUG] [WARNING] No inventoryItemGroup in group_data - created empty structure")
        
        # Copy variantSKUs (required)
        if 'variantSKUs' in group_data:
            clean_data['variantSKUs'] = group_data['variantSKUs']
        
        # Debug: Print the exact JSON being sent
        import json
        json_payload = json.dumps(clean_data, indent=2)
        print(f"[DEBUG] ========== GROUP CREATION REQUEST ==========")
        print(f"[DEBUG] Full group data JSON:")
        print(json_payload)
        print(f"[DEBUG] ===========================================")
        
        # CRITICAL: Check if description is in the JSON
        if '"description"' in json_payload:
            print(f"[DEBUG] [VERIFY] Description field found in JSON payload!")
            # Extract description value
            try:
                parsed = json.loads(json_payload)
                if 'inventoryItemGroup' in parsed and 'description' in parsed['inventoryItemGroup']:
                    desc_val = parsed['inventoryItemGroup']['description']
                    print(f"[DEBUG] [VERIFY] Description value: {desc_val[:100]}...")
                    print(f"[DEBUG] [VERIFY] Description length: {len(desc_val)}")
                else:
                    print(f"[DEBUG] [ERROR] Description field in JSON but not in parsed structure!")
            except:
                print(f"[DEBUG] [WARNING] Could not parse JSON to verify description")
        else:
            print(f"[DEBUG] [CRITICAL ERROR] Description field NOT found in JSON payload!")
            print(f"[DEBUG] [CRITICAL ERROR] This will cause Error 25016!")
        
        # Verify title is actually in the payload
        if 'inventoryItemGroup' in clean_data:
            title_in_data = clean_data['inventoryItemGroup'].get('title')
            print(f"[DEBUG] Title in clean_data: {repr(title_in_data)}")
            print(f"[DEBUG] Title type: {type(title_in_data)}")
            print(f"[DEBUG] Title in JSON: {'\"title\"' in json_payload}")
            if title_in_data:
                print(f"[DEBUG] Title value: '{title_in_data}'")
                print(f"[DEBUG] Title length: {len(title_in_data)}")
                print(f"[DEBUG] Title bytes: {len(title_in_data.encode('utf-8'))}")
        
        # NOTE: imageUrls is REQUIRED at ROOT level for variation listings (per eBay API docs)
        # But we should verify it's at root, not in inventoryItemGroup
        if 'imageUrls' in clean_data:
            print(f"[DEBUG] [OK] imageUrls found at ROOT level: {len(clean_data.get('imageUrls', []))} URLs")
        elif 'inventoryItemGroup' in clean_data and 'imageUrls' in clean_data.get('inventoryItemGroup', {}):
            print(f"[DEBUG] [WARNING] imageUrls found in inventoryItemGroup - should be at ROOT level")
            # Move to root
            image_urls = clean_data['inventoryItemGroup'].pop('imageUrls')
            clean_data['imageUrls'] = image_urls
            print(f"[DEBUG] [FIX] Moved imageUrls to ROOT level")
        
        # CRITICAL: Verify description is present in inventoryItemGroup BEFORE sending
        # This is THE LAST CHANCE to ensure description is in the request
        print(f"[DEBUG] ========== FINAL DESCRIPTION VERIFICATION ==========")
        description_fixed = False
        
        if 'inventoryItemGroup' in clean_data:
            if 'description' in clean_data['inventoryItemGroup']:
                desc = clean_data['inventoryItemGroup']['description']
                if desc and desc.strip() and len(desc.strip()) >= 50:
                    print(f"[DEBUG] [OK] Description in inventoryItemGroup: YES (length: {len(desc)})")
                    print(f"[DEBUG] [OK] Description value: {desc[:100]}...")
                    print(f"[DEBUG] [OK] Description is valid: True")
                else:
                    print(f"[DEBUG] [ERROR] Description is invalid (length: {len(desc) if desc else 0})")
                    print(f"[DEBUG] [FIX] Replacing with valid description...")
                    # Fix it
                    if 'title' in clean_data and ("Topps Chrome" in clean_data['title'] or "Chrome" in clean_data['title']):
                        clean_data['inventoryItemGroup']['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    else:
                        title_val = clean_data.get('title', 'Variation Listing')
                        clean_data['inventoryItemGroup']['description'] = f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    description_fixed = True
                    print(f"[DEBUG] [FIX] Description replaced (new length: {len(clean_data['inventoryItemGroup']['description'])})")
            else:
                print(f"[DEBUG] [CRITICAL ERROR] Description NOT in inventoryItemGroup!")
                print(f"[DEBUG] [CRITICAL ERROR] inventoryItemGroup keys: {list(clean_data['inventoryItemGroup'].keys())}")
                print(f"[DEBUG] [FIX] Adding description now...")
                
                # Try to get it from original data first
                if 'inventoryItemGroup' in group_data and 'description' in group_data['inventoryItemGroup']:
                    original_desc = group_data['inventoryItemGroup']['description']
                    if original_desc and len(original_desc.strip()) >= 50:
                        clean_data['inventoryItemGroup']['description'] = original_desc
                        print(f"[DEBUG] [FIX] Added description from original data (length: {len(original_desc)})")
                        description_fixed = True
                    else:
                        print(f"[DEBUG] [FIX] Original description is invalid, generating new one...")
                        # Generate valid description
                        if 'title' in clean_data and ("Topps Chrome" in clean_data['title'] or "Chrome" in clean_data['title']):
                            clean_data['inventoryItemGroup']['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                        else:
                            title_val = clean_data.get('title', 'Variation Listing')
                            clean_data['inventoryItemGroup']['description'] = f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                        description_fixed = True
                        print(f"[DEBUG] [FIX] Generated description (length: {len(clean_data['inventoryItemGroup']['description'])})")
                else:
                    print(f"[DEBUG] [FIX] No description in original data, generating one...")
                    # Generate valid description
                    if 'title' in clean_data and ("Topps Chrome" in clean_data['title'] or "Chrome" in clean_data['title']):
                        clean_data['inventoryItemGroup']['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    else:
                        title_val = clean_data.get('title', 'Variation Listing')
                        clean_data['inventoryItemGroup']['description'] = f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                    description_fixed = True
                    print(f"[DEBUG] [FIX] Generated description (length: {len(clean_data['inventoryItemGroup']['description'])})")
        else:
            print(f"[DEBUG] [CRITICAL ERROR] inventoryItemGroup not in clean_data!")
            print(f"[DEBUG] [FIX] Creating inventoryItemGroup with description...")
            clean_data['inventoryItemGroup'] = {
                "aspects": group_data.get('inventoryItemGroup', {}).get('aspects', {}),
                "description": group_data.get('inventoryItemGroup', {}).get('description', 
                    f"""{group_data.get('title', 'Variation Listing')}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.""")
            }
            description_fixed = True
            print(f"[DEBUG] [FIX] Created inventoryItemGroup with description")
        
        # Final verification - ABSOLUTE LAST CHANCE to ensure description is valid
        if 'inventoryItemGroup' in clean_data:
            if 'description' in clean_data['inventoryItemGroup']:
                final_desc = clean_data['inventoryItemGroup']['description']
                final_desc_stripped = final_desc.strip() if final_desc else ''
                if len(final_desc_stripped) < 50:
                    print(f"[DEBUG] [CRITICAL] Description is too short ({len(final_desc_stripped)} chars)! Fixing now...")
                    title_val = clean_data.get('title', 'Variation Listing')
                    clean_data['inventoryItemGroup']['description'] = f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
                    description_fixed = True
                    final_desc = clean_data['inventoryItemGroup']['description']
                    print(f"[DEBUG] [FIX] Description replaced with guaranteed valid one (length: {len(final_desc.strip())})")
                
                print(f"[DEBUG] [FINAL] Description confirmed:")
                print(f"  Present: YES")
                print(f"  Value: {final_desc[:100]}...")
                print(f"  Length: {len(final_desc)}")
                print(f"  Valid: {bool(final_desc.strip() and len(final_desc.strip()) >= 50)}")
                if description_fixed:
                    print(f"[DEBUG] [NOTE] Description was fixed/added in this step")
            else:
                print(f"[DEBUG] [CRITICAL ERROR] Description NOT in inventoryItemGroup!")
                print(f"[DEBUG] [FIX] Adding description as absolute last resort...")
                title_val = clean_data.get('title', 'Variation Listing')
                clean_data['inventoryItemGroup']['description'] = f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
                description_fixed = True
                print(f"[DEBUG] [FIX] Added description (length: {len(clean_data['inventoryItemGroup']['description'].strip())})")
        else:
            print(f"[DEBUG] [CRITICAL ERROR] inventoryItemGroup not in clean_data!")
            print(f"[DEBUG] [FIX] Creating inventoryItemGroup with description as absolute last resort...")
            title_val = clean_data.get('title', 'Variation Listing')
            clean_data['inventoryItemGroup'] = {
                "aspects": group_data.get('inventoryItemGroup', {}).get('aspects', {}),
                "description": f"""{title_val}

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.

Ships in penny sleeve and top loader via PWE with eBay tracking.

This is a variation listing where you can select from multiple card options. Each card is individually priced and available in the quantities shown."""
            }
            description_fixed = True
            print(f"[DEBUG] [FIX] Created inventoryItemGroup with description (length: {len(clean_data['inventoryItemGroup']['description'].strip())})")
        
        # ABSOLUTE FINAL CHECK - if description is still missing or invalid, this is a critical error
        if 'inventoryItemGroup' not in clean_data or 'description' not in clean_data.get('inventoryItemGroup', {}) or len(clean_data['inventoryItemGroup']['description'].strip()) < 50:
            print(f"[DEBUG] [CRITICAL ERROR] Description STILL missing or invalid after ALL fixes!")
            print(f"[DEBUG] [CRITICAL ERROR] This WILL cause Error 25016!")
            print(f"[DEBUG] [CRITICAL ERROR] clean_data structure: {list(clean_data.keys())}")
            if 'inventoryItemGroup' in clean_data:
                print(f"[DEBUG] [CRITICAL ERROR] inventoryItemGroup keys: {list(clean_data['inventoryItemGroup'].keys())}")
        
        print(f"[DEBUG] ==============================================")
        
        # CRITICAL: Final check - ensure title is set at ROOT level and not None
        if 'title' not in clean_data or clean_data.get('title') is None:
            print("[ERROR] Title is missing or None at ROOT level! Attempting to get from original data...")
            # Try to get title from original group_data (check both root and inventoryItemGroup)
            if 'title' in group_data:
                original_title = group_data['title']
                if original_title and isinstance(original_title, str) and len(original_title.strip()) > 0:
                    clean_data['title'] = original_title.strip()[:80]
                    print(f"[DEBUG] Force-set title from original ROOT: '{clean_data['title']}'")
            elif 'inventoryItemGroup' in group_data and 'title' in group_data['inventoryItemGroup']:
                # Fallback: get from inventoryItemGroup if it was there
                original_title = group_data['inventoryItemGroup']['title']
                if original_title and isinstance(original_title, str) and len(original_title.strip()) > 0:
                    clean_data['title'] = original_title.strip()[:80]
                    print(f"[DEBUG] Force-set title from inventoryItemGroup (moving to ROOT): '{clean_data['title']}'")
            else:
                print("[ERROR] No valid title found in original data!")
        else:
            # Ensure it's a string and not empty
            title_check = clean_data['title']
            if not isinstance(title_check, str):
                clean_data['title'] = str(title_check)
            if len(clean_data['title']) == 0:
                print("[ERROR] Title is empty! This will cause an error!")
        
        # Log the exact request that will be sent
        print(f"[DEBUG] Request URL: {endpoint}")
        print(f"[DEBUG] Request method: PUT")
        print(f"[DEBUG] Full clean_data structure:")
        print(json.dumps(clean_data, indent=2))
        
        # Verify title one more time before sending (at ROOT level)
        title_check = clean_data.get('title')
        print(f"[DEBUG] Final title check at ROOT level: {repr(title_check)}")
        print(f"[DEBUG] Title type: {type(title_check)}")
        if title_check is None:
            print("[ERROR] Title is None at ROOT level! This should not happen!")
        elif not isinstance(title_check, str):
            print(f"[ERROR] Title is not a string: {type(title_check)}")
        elif len(title_check) == 0:
            print("[ERROR] Title is empty string!")
        else:
            print(f"[DEBUG] [OK] Title is valid at ROOT level: '{title_check}' (length: {len(title_check)})")
        
        # Use PUT method and include group_key in the path, not as query param
        response = self._make_request('PUT', endpoint, data=clean_data)
        
        # CRITICAL: Check response for group creation/update
        print(f"[DEBUG] ========== GROUP CREATION/UPDATE RESPONSE ==========")
        print(f"[DEBUG] Status Code: {response.status_code}")
        print(f"[DEBUG] Response Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201, 204]:
            print(f"[DEBUG] [OK] Group created/updated successfully (status: {response.status_code})")
            try:
                if response.status_code != 204:
                    response_data = response.json()
                    print(f"[DEBUG] Response data keys: {list(response_data.keys())}")
                    if 'inventoryItemGroup' in response_data:
                        resp_group = response_data['inventoryItemGroup']
                        print(f"[DEBUG] Response inventoryItemGroup keys: {list(resp_group.keys())}")
                        if 'description' in resp_group:
                            resp_desc = resp_group['description']
                            print(f"[DEBUG] [OK] Description in response: YES")
                            print(f"[DEBUG] Response description: {resp_desc[:100]}... (length: {len(resp_desc)})")
                        else:
                            print(f"[DEBUG] [NOTE] Description not in response")
                            print(f"[DEBUG] [NOTE] This is normal - eBay may not return description in response")
                            print(f"[DEBUG] [NOTE] But description should still be saved in the group")
                else:
                    print(f"[DEBUG] [NOTE] 204 No Content - group updated but no response body")
                    print(f"[DEBUG] [NOTE] This is normal for PUT requests")
            except Exception as e:
                print(f"[DEBUG] [WARNING] Could not parse response: {e}")
        else:
            print(f"[DEBUG] [ERROR] Group creation/update failed!")
            print(f"[DEBUG] Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"[DEBUG] Error response:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"[DEBUG] Error text: {response.text[:1000]}")
        print(f"[DEBUG] =================================================")
        
        if response.status_code in [200, 201, 204]:
            # 204 No Content means success but no response body
            if response.status_code == 204:
                return {"success": True, "data": {"inventoryItemGroupKey": group_key}}
            return {"success": True, "data": response.json()}
        else:
            error_text = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('message', error_text)
                        error_id = errors[0].get('errorId', '')
                        if error_id:
                            error_msg = f"{error_msg} (Error ID: {error_id})"
                        error_text = error_msg
            except:
                pass
            # Include full error response for debugging
            full_error = error_text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        # Get more details from the error
                        error_details = []
                        for err in errors:
                            error_details.append(f"{err.get('message', 'Unknown error')} (Error ID: {err.get('errorId', 'N/A')})")
                            # Check for parameters that might give more context
                            params = err.get('parameters', [])
                            if params:
                                for param in params:
                                    error_details.append(f"  Parameter: {param.get('name', 'unknown')} = {param.get('value', 'N/A')}")
                        full_error = "\n".join(error_details)
            except:
                pass
            
            return {
                "success": False,
                "error": full_error,
                "status_code": response.status_code,
                "raw_response": response.text[:1000] if hasattr(response, 'text') else None
            }
    
    def get_offer_by_sku(self, sku: str, marketplace_id: str = "EBAY_US") -> Dict:
        """Get an offer by SKU."""
        endpoint = "/sell/inventory/v1/offer"
        params = {"sku": sku, "marketplaceId": marketplace_id}
        response = self._make_request('GET', endpoint, params=params)
        
        if response.status_code == 200:
            data = response.json()
            offers = data.get('offers', [])
            if offers:
                return {"success": True, "offer": offers[0], "offerId": offers[0].get('offerId')}
            return {"success": False, "offer": None, "offerId": None}
        else:
            return {"success": False, "offer": None, "offerId": None}
    
    def create_or_update_offer(self, offer_data: Dict) -> Dict:
        """Create or update an offer. If offer exists, update it; otherwise create it."""
        sku = offer_data.get('sku')
        marketplace_id = offer_data.get('marketplaceId', 'EBAY_US')
        
        if not sku:
            return {
                "success": False,
                "error": {"message": "SKU is required"}
            }
        
        # Check if offer already exists
        existing_offer = self.get_offer_by_sku(sku, marketplace_id)
        
        if existing_offer.get('success') and existing_offer.get('offerId'):
            # Offer exists - update it
            offer_id = existing_offer['offerId']
            print(f"[INFO] Offer already exists for SKU {sku}, updating offer {offer_id}...")
            return self.update_offer(offer_id, offer_data)
        else:
            # Offer doesn't exist - create it
            return self.create_offer(offer_data)
    
    def create_offer(self, offer_data: Dict) -> Dict:
        """Create an offer (listing)."""
        # CRITICAL: Ensure description is present before creating
        print(f"[DEBUG] ========== CREATE OFFER DEBUG ==========")
        print(f"[DEBUG] Offer data keys: {list(offer_data.keys())}")
        
        if 'listing' in offer_data:
            print(f"[DEBUG] Listing object exists")
            print(f"[DEBUG] Listing keys: {list(offer_data['listing'].keys())}")
            listing_desc = offer_data['listing'].get('description', '')
            print(f"[DEBUG] Description from offer_data: {listing_desc[:100] if listing_desc else 'MISSING'}...")
            print(f"[DEBUG] Description length: {len(listing_desc) if listing_desc else 0}")
            
            if not listing_desc or not listing_desc.strip() or len(listing_desc.strip()) < 50:
                print(f"[DEBUG] [FIX] Description missing or too short - adding proper description")
                title = offer_data['listing'].get('title', 'Variation Listing')
                # Use proper description for Topps Chrome
                if "Topps Chrome" in title or "Chrome" in title:
                    listing_desc = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                else:
                    listing_desc = f"{title}. Select your card from the variations below. All cards are in Near Mint or better condition."
                offer_data['listing']['description'] = listing_desc
                print(f"[DEBUG] [FIX] Added description (length: {len(listing_desc)})")
            else:
                description = offer_data['listing']['description']
                print(f"[DEBUG] Description is valid: {description[:50]}... (length: {len(description)})")
        else:
            print(f"[DEBUG] [ERROR] NO LISTING OBJECT IN OFFER_DATA!")
            print(f"[DEBUG] Creating listing object...")
            offer_data['listing'] = {
                "title": offer_data.get('title', 'Variation Listing'),
                "description": """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted.""",
                "listingPolicies": {}
            }
            print(f"[DEBUG] [FIX] Created listing object with description")
        
        print(f"[DEBUG] Final offer_data listing.description: {offer_data.get('listing', {}).get('description', 'MISSING')[:100]}...")
        print(f"[DEBUG] ==========================================")
        
        # CRITICAL: Verify listing object structure before sending
        if 'listing' in offer_data:
            listing_obj = offer_data['listing']
            print(f"[DEBUG] [VERIFY] Listing object structure:")
            print(f"  Has title: {'title' in listing_obj}")
            print(f"  Has description: {'description' in listing_obj}")
            print(f"  Description value: {listing_obj.get('description', 'MISSING')[:50] if listing_obj.get('description') else 'MISSING'}...")
            print(f"  Description length: {len(listing_obj.get('description', ''))}")
            print(f"  Listing keys: {list(listing_obj.keys())}")
        else:
            print(f"[DEBUG] [ERROR] NO LISTING OBJECT IN FINAL offer_data!")
            print(f"[DEBUG] offer_data keys: {list(offer_data.keys())}")
        
        # CRITICAL: For variation listings, eBay requires description in the listing object
        # BUT eBay API may not persist listing object on create - we MUST update after creation
        # Ensure listing object is properly structured
        if 'listing' not in offer_data:
            print(f"[DEBUG] [CRITICAL] NO LISTING OBJECT - Creating it now!")
            offer_data['listing'] = {
                "title": offer_data.get('title', 'Variation Listing'),
                "description": "",
                "listingPolicies": {}
            }
        
        # Ensure description is in listing object
        if 'description' not in offer_data['listing'] or not offer_data['listing']['description']:
            print(f"[DEBUG] [CRITICAL] NO DESCRIPTION IN LISTING - Adding it!")
            title = offer_data['listing'].get('title', offer_data.get('title', 'Variation Listing'))
            if "Topps Chrome" in title or "Chrome" in title:
                offer_data['listing']['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
            else:
                offer_data['listing']['description'] = f"{title}. Select your card from the variations below. All cards are in Near Mint or better condition."
        
        print(f"[DEBUG] [FIX] Ensured listing.description exists (length: {len(offer_data['listing']['description'])})")
        
        # CRITICAL: eBay API for offers may require description at root level, not in listing object
        # Try both locations to ensure it's saved
        if 'listing' in offer_data and 'description' in offer_data['listing']:
            desc = offer_data['listing']['description']
            # Also add at root level as listingDescription (eBay API field name)
            if desc and desc.strip():
                offer_data['listingDescription'] = desc
                print(f"[DEBUG] [FIX] Added listingDescription at root level (length: {len(desc)})")
        
        endpoint = "/sell/inventory/v1/offer"
        print(f"[DEBUG] ========== FINAL OFFER PAYLOAD ==========")
        print(f"[DEBUG] Has 'listing': {'listing' in offer_data}")
        print(f"[DEBUG] Has 'listingDescription' (root): {'listingDescription' in offer_data}")
        print(f"[DEBUG] Has 'description' (root): {'description' in offer_data}")
        if 'listing' in offer_data:
            print(f"[DEBUG] Has 'listing.description': {'description' in offer_data['listing']}")
            if 'description' in offer_data['listing']:
                print(f"[DEBUG] listing.description length: {len(offer_data['listing']['description'])}")
        print(f"[DEBUG] ========================================")
        response = self._make_request('POST', endpoint, data=offer_data)
        
        # After response, check if listing object was accepted
        if response.status_code in [200, 201]:
            try:
                response_data = response.json()
                print(f"[DEBUG] [RESPONSE] Offer created successfully")
                print(f"[DEBUG] [RESPONSE] Response keys: {list(response_data.keys())}")
                if 'listing' in response_data:
                    print(f"[DEBUG] [RESPONSE] Listing object in response: YES")
                    print(f"[DEBUG] [RESPONSE] Listing keys: {list(response_data['listing'].keys())}")
                else:
                    print(f"[DEBUG] [WARNING] Listing object NOT in response (may be normal for unpublished offers)")
            except:
                pass
        
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text}
            
            return {
                "success": False,
                "error": error_data,
                "status_code": response.status_code
            }
    
    def update_offer(self, offer_id: str, offer_data: Dict) -> Dict:
        """Update an existing offer (listing)."""
        endpoint = f"/sell/inventory/v1/offer/{offer_id}"
        
        # Debug: Log what we're sending
        fulfillment_policy_id = offer_data.get('listing', {}).get('listingPolicies', {}).get('fulfillmentPolicyId')
        if fulfillment_policy_id:
            print(f"[DEBUG] Updating offer {offer_id} with fulfillmentPolicyId: {fulfillment_policy_id}")
        else:
            print(f"[WARNING] Updating offer {offer_id} but no fulfillmentPolicyId in offer_data!")
            # Try to get it from nested structure
            if 'listing' in offer_data and isinstance(offer_data['listing'], dict):
                if 'listingPolicies' in offer_data['listing'] and isinstance(offer_data['listing']['listingPolicies'], dict):
                    fulfillment_policy_id = offer_data['listing']['listingPolicies'].get('fulfillmentPolicyId')
                    if fulfillment_policy_id:
                        print(f"[DEBUG] Found fulfillmentPolicyId in nested structure: {fulfillment_policy_id}")
        
        # CRITICAL: Ensure listing object exists with description
        if 'listing' not in offer_data:
            print(f"[DEBUG] [CRITICAL] NO LISTING OBJECT IN UPDATE - Creating it...")
            offer_data['listing'] = {
                "title": offer_data.get('title', 'Variation Listing'),
                "description": "",
                "listingPolicies": {}
            }
        
        # Make sure listingPolicies is properly structured
        if 'listingPolicies' not in offer_data['listing']:
            offer_data['listing']['listingPolicies'] = {}
        
        # CRITICAL: Ensure description is present and valid
        print(f"[DEBUG] ========== UPDATE OFFER {offer_id} DEBUG ==========")
        print(f"[DEBUG] Offer data has 'listing': {'listing' in offer_data}")
            
        if 'listing' in offer_data:
            listing_desc = offer_data['listing'].get('description', '')
            print(f"[DEBUG] Description from offer_data: {listing_desc[:100] if listing_desc else 'MISSING'}...")
            print(f"[DEBUG] Description length: {len(listing_desc) if listing_desc else 0}")
            
            if not listing_desc or not listing_desc.strip() or len(listing_desc.strip()) < 50:
                print(f"[DEBUG] [FIX] Description missing or too short - adding proper description")
                title = offer_data['listing'].get('title', offer_data.get('title', 'Variation Listing'))
                # Use proper description for Topps Chrome
                if "Topps Chrome" in title or "Chrome" in title:
                    listing_desc = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                else:
                    listing_desc = f"{title}. Select your card from the variations below. All cards are in Near Mint or better condition."
                offer_data['listing']['description'] = listing_desc
                print(f"[DEBUG] [FIX] Added description (length: {len(listing_desc)})")
            else:
                description = offer_data['listing']['description']
                print(f"[DEBUG] Description is valid: {description[:50]}... (length: {len(description)})")
            
            # FINAL CHECK before sending
            final_desc = offer_data.get('listing', {}).get('description', '')
            print(f"[DEBUG] FINAL CHECK - Description in offer_data before PUT:")
            print(f"  Present: {bool(final_desc)}")
            print(f"  Value: {final_desc[:100] if final_desc else 'MISSING'}...")
            print(f"  Length: {len(final_desc) if final_desc else 0}")
            print(f"[DEBUG] ================================================")
        
        # CRITICAL: Verify listing object structure before sending
        if 'listing' in offer_data:
            listing_obj = offer_data['listing']
            print(f"[DEBUG] [VERIFY] Listing object structure before PUT:")
            print(f"  Has title: {'title' in listing_obj}")
            print(f"  Has description: {'description' in listing_obj}")
            print(f"  Description value: {listing_obj.get('description', 'MISSING')[:50] if listing_obj.get('description') else 'MISSING'}...")
            print(f"  Description length: {len(listing_obj.get('description', ''))}")
            print(f"  Listing keys: {list(listing_obj.keys())}")
        else:
            print(f"[DEBUG] [ERROR] NO LISTING OBJECT IN FINAL offer_data!")
            print(f"[DEBUG] offer_data keys: {list(offer_data.keys())}")
        
        # CRITICAL: Final check - ensure description is in listing object
        if 'listing' in offer_data:
            if 'description' not in offer_data['listing'] or not offer_data['listing']['description'] or len(offer_data['listing']['description'].strip()) < 50:
                print(f"[DEBUG] [CRITICAL] Description missing in update - adding default")
                title = offer_data['listing'].get('title', offer_data.get('title', 'Variation Listing'))
                if "Topps Chrome" in title or "Chrome" in title:
                    offer_data['listing']['description'] = """If you are new to the Topps basketball scene, Topps Chrome serves as a premium upgrade to the 2025-26 Topps flagship basketball set printed on a chromium stock. Topps announced the base set will run 299 cards, featuring veterans, rookies, and legends.

Select your card from the variations below. Each card is listed as a separate variation option.

All cards are in Near Mint or better condition unless otherwise noted."""
                else:
                    offer_data['listing']['description'] = f"{title}. Select your card from the variations below. All cards are in Near Mint or better condition."
                print(f"[DEBUG] [FIX] Added description to update payload (length: {len(offer_data['listing']['description'])})")
        
        # CRITICAL: Also add listingDescription at root level for update
        if 'listing' in offer_data and 'description' in offer_data['listing']:
            desc = offer_data['listing']['description']
            if desc and desc.strip():
                offer_data['listingDescription'] = desc
                print(f"[DEBUG] [FIX] Added listingDescription to update payload (length: {len(desc)})")
        
        print(f"[DEBUG] [FINAL] Update payload has listing.description: {'listing' in offer_data and 'description' in offer_data.get('listing', {})}")
        print(f"[DEBUG] [FINAL] Update payload has listingDescription (root): {'listingDescription' in offer_data}")
        response = self._make_request('PUT', endpoint, data=offer_data)
        
        # After response, log what was returned
        if response.status_code in [200, 204]:
            print(f"[DEBUG] [RESPONSE] Offer updated successfully (status: {response.status_code})")
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"[DEBUG] [RESPONSE] Response keys: {list(response_data.keys())}")
                    if 'listing' in response_data:
                        print(f"[DEBUG] [RESPONSE] Listing object in response: YES")
                        listing_resp = response_data['listing']
                        print(f"[DEBUG] [RESPONSE] Listing has description: {'description' in listing_resp}")
                        if 'description' in listing_resp:
                            print(f"[DEBUG] [RESPONSE] Description length: {len(listing_resp['description'])}")
                    else:
                        print(f"[DEBUG] [WARNING] Listing object NOT in response")
                        print(f"[DEBUG] [NOTE] This is normal - eBay may not return listing object in PUT response")
                        print(f"[DEBUG] [NOTE] But the listing object should still be saved for publishing")
                except Exception as e:
                    print(f"[DEBUG] [RESPONSE] Could not parse response: {e}")
        else:
            print(f"[DEBUG] [ERROR] Update failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"[DEBUG] [ERROR] Error response: {json.dumps(error_data, indent=2)[:500]}")
            except:
                print(f"[DEBUG] [ERROR] Error text: {response.text[:500]}")
        
        if response.status_code in [200, 204]:
            # 204 No Content means success but no response body
            if response.status_code == 204:
                return {"success": True, "data": {"offerId": offer_id}}
            return {"success": True, "data": response.json()}
        else:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text}
            
            return {
                "success": False,
                "error": error_data,
                "status_code": response.status_code
            }
    
    def publish_offer(self, offer_id: str) -> Dict:
        """Publish an offer to make it live."""
        endpoint = f"/sell/inventory/v1/offer/{offer_id}/publish"
        
        # eBay publish endpoint doesn't accept description in the request
        # The description must already be in the offer
        # Try publishing directly
        response = self._make_request('POST', endpoint)
        
        if response.status_code in [200, 201]:
            try:
                return {"success": True, "data": response.json()}
            except json.JSONDecodeError as e:
                print(f"[ERROR] Response is not valid JSON: {e}")
                print(f"[ERROR] Response text: {response.text[:1000]}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {str(e)}",
                    "status_code": response.status_code,
                    "raw_response": response.text[:1000]
                }
        else:
            # If Error 25016, try one more time after a longer wait
            if '25016' in response.text:
                print(f"[RETRY] Error 25016 detected, waiting 15 seconds and retrying...")
                import time
                time.sleep(15)
                
                # Try one more time
                response = self._make_request('POST', endpoint)
                if response.status_code in [200, 201]:
                    try:
                        return {"success": True, "data": response.json()}
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Retry response is not valid JSON: {e}")
                        return {
                            "success": False,
                            "error": f"Invalid JSON response on retry: {str(e)}",
                            "status_code": response.status_code,
                            "raw_response": response.text[:1000]
                        }
            
            error_text = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        error_text = errors[0].get('message', error_text)
            except json.JSONDecodeError:
                # If error response is not JSON, use raw text
                pass
            except:
                pass
            
            return {
                "success": False,
                "error": error_text,
                "status_code": response.status_code
            }
    
    def publish_offer_by_inventory_item_group(self, group_key: str, marketplace_id: str = "EBAY_US") -> Dict:
        """Publish a variation listing using the inventory item group key."""
        endpoint = "/sell/inventory/v1/offer/publish_by_inventory_item_group"
        data = {
            "inventoryItemGroupKey": group_key,
            "marketplaceId": marketplace_id
        }
        
        print(f"[INFO] Publishing variation listing group: {group_key}")
        
        # Simple approach: Just publish directly
        # Description should already be set when group was created
        response = self._make_request('POST', endpoint, data=data)
        
        # Check if response is HTML (authentication/endpoint error)
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type or (response.text and response.text.strip().startswith('<!DOCTYPE')):
            error_msg = "eBay returned an HTML page instead of JSON. This usually means:\n"
            error_msg += "1. Your access token is expired or invalid - refresh it in Step 2\n"
            error_msg += "2. The API endpoint is incorrect\n"
            error_msg += "3. You're not authenticated properly\n\n"
            error_msg += f"Response preview: {response.text[:500]}"
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code,
                "raw_response": response.text[:1000],
                "is_html": True
            }
        
        if response.status_code in [200, 201]:
            try:
                response_data = response.json()
                listing_id = response_data.get('listingId') or response_data.get('listing_id')
                return {
                    "success": True,
                    "listing_id": listing_id,
                    "data": response_data
                }
            except json.JSONDecodeError as e:
                print(f"[ERROR] Publish response is not valid JSON: {e}")
                print(f"[ERROR] Response text: {response.text[:1000]}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response from eBay: {str(e)}. Response may be HTML or malformed.",
                    "status_code": response.status_code,
                    "raw_response": response.text[:1000]
                }
        else:
            error_text = response.text
            try:
                error_json = response.json()
                if isinstance(error_json, dict):
                    errors = error_json.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('message', error_text)
                        error_id = errors[0].get('errorId', '')
                        if error_id:
                            error_msg = f"{error_msg} (Error ID: {error_id})"
                        error_text = error_msg
            except json.JSONDecodeError as e:
                print(f"[ERROR] Error response is not valid JSON: {e}")
                print(f"[ERROR] Response text: {error_text[:1000]}")
                error_text = f"Invalid JSON in error response: {str(e)}. Raw response: {error_text[:500]}"
            except:
                pass
            
            return {
                "success": False,
                "error": error_text,
                "status_code": response.status_code,
                "raw_response": response.text[:1000] if hasattr(response, 'text') else None
            }
    
    def _debug_fulfillment_policy_error(self, group_key: str) -> Dict:
        """Get detailed debugging information for fulfillment policy errors."""
        debug_info = {
            "group_key": group_key,
            "policies_checked": [],
            "offers_checked": [],
            "issues_found": []
        }
        
        try:
            # 1. Get the group to find associated SKUs
            group_result = self.get_inventory_item_group(group_key)
            if not group_result.get('success'):
                debug_info["issues_found"].append(f"Could not get inventory item group: {group_result.get('error', 'Unknown')}")
                return debug_info
            
            group_data = group_result.get('data', {})
            variant_skus = []
            
            # First, try to get SKUs directly from variantSKUs field (most reliable)
            if 'variantSKUs' in group_data:
                variant_skus = group_data['variantSKUs']
                debug_info["issues_found"].append(f"Found {len(variant_skus)} SKUs from variantSKUs field")
            
            # Extract SKUs from the group - try different possible structures
            if not variant_skus and 'variants' in group_data:
                for variant in group_data['variants']:
                    sku = variant.get('sku') or variant.get('SKU')
                    if sku:
                        variant_skus.append(sku)
            if not variant_skus and 'inventoryItems' in group_data:
                for item in group_data['inventoryItems']:
                    sku = item.get('sku') or item.get('SKU')
                    if sku:
                        variant_skus.append(sku)
            
            # If we still can't find SKUs, try to get them from offers endpoint
            if not variant_skus:
                # Try to get offers for the marketplace to find SKUs
                try:
                    offers_response = self._make_request('GET', '/sell/inventory/v1/offer', params={'limit': 20})
                    if offers_response.status_code == 200:
                        offers_data = offers_response.json()
                        offers = offers_data.get('offers', [])
                        # Get SKUs from offers that match this group key
                        for offer in offers:
                            offer_group_key = offer.get('inventoryItemGroupKey')
                            if offer_group_key == group_key:
                                sku = offer.get('sku')
                                if sku:
                                    variant_skus.append(sku)
                except Exception as e:
                    debug_info["issues_found"].append(f"Could not get offers: {str(e)}")
            
            if not variant_skus:
                debug_info["issues_found"].append("Could not find any SKUs associated with this group")
            
            # 2. Check each offer's fulfillment policy
            for sku in variant_skus[:3]:  # Check first 3 to avoid too many API calls
                offer_info = {"sku": sku, "policy_id": None, "policy_valid": False, "issues": []}
                
                # Get offer by SKU
                offer_result = self.get_offer_by_sku(sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offer = offer_result['offer']
                    offer_id = offer.get('offerId')
                    offer_info["offer_id"] = offer_id
                    
                    # Get fulfillment policy ID from offer
                    listing_policies = offer.get('listing', {}).get('listingPolicies', {})
                    fulfillment_policy_id = listing_policies.get('fulfillmentPolicyId')
                    offer_info["policy_id"] = fulfillment_policy_id
                    
                    if fulfillment_policy_id:
                        # Check the policy
                        policy_response = self._make_request('GET', f'/sell/account/v1/fulfillment_policy/{fulfillment_policy_id}')
                        if policy_response.status_code == 200:
                            policy = policy_response.json()
                            policy_name = policy.get('name', 'Unknown')
                            shipping_options = policy.get('shippingOptions', [])
                            
                            offer_info["policy_name"] = policy_name
                            offer_info["shipping_options_count"] = len(shipping_options)
                            
                            if shipping_options:
                                offer_info["policy_valid"] = True
                                # Check each shipping option
                                for opt in shipping_options:
                                    services = opt.get('shippingServices', [])
                                    if not services:
                                        offer_info["issues"].append(f"Option {opt.get('optionType')} has no shipping services")
                                    else:
                                        for svc in services:
                                            svc_code = svc.get('shippingServiceCode', 'N/A')
                                            carrier = svc.get('shippingCarrierCode', 'N/A')
                                            cost = svc.get('shippingCost', {})
                                            cost_value = cost.get('value', 'N/A')
                                            buyer_responsible = svc.get('buyerResponsibleForShipping', None)
                                            
                                            service_info = f"{svc_code} ({carrier})"
                                            if cost_value != 'N/A':
                                                service_info += f" - ${cost_value}"
                                            if buyer_responsible is not None:
                                                service_info += f" - Buyer Pays: {buyer_responsible}"
                                            
                                            offer_info["services"] = offer_info.get("services", [])
                                            offer_info["services"].append(service_info)
                                            
                                            # Check if buyerResponsibleForShipping is False (this could be the issue)
                                            if buyer_responsible is False:
                                                offer_info["issues"].append(f"Service {svc_code} has buyerResponsibleForShipping=False (seller pays). eBay may require buyer to pay for Trading Cards.")
                            else:
                                offer_info["issues"].append("Policy has no shipping options")
                        else:
                            offer_info["issues"].append(f"Could not get policy: HTTP {policy_response.status_code}")
                    else:
                        offer_info["issues"].append("No fulfillmentPolicyId in offer")
                
                debug_info["offers_checked"].append(offer_info)
            
            # 3. Check config policy with detailed shipping service info
            config_policy_id = self.config.FULFILLMENT_POLICY_ID
            if config_policy_id:
                policy_response = self._make_request('GET', f'/sell/account/v1/fulfillment_policy/{config_policy_id}')
                if policy_response.status_code == 200:
                    policy = policy_response.json()
                    shipping_options = policy.get('shippingOptions', [])
                    
                    # Extract detailed service information
                    services_detail = []
                    buyer_responsible_issues = []
                    for opt in shipping_options:
                        for svc in opt.get('shippingServices', []):
                            svc_code = svc.get('shippingServiceCode', 'N/A')
                            carrier = svc.get('shippingCarrierCode', 'N/A')
                            cost = svc.get('shippingCost', {})
                            cost_value = cost.get('value', 'N/A')
                            buyer_responsible = svc.get('buyerResponsibleForShipping', None)
                            
                            service_info = {
                                "code": svc_code,
                                "carrier": carrier,
                                "cost": cost_value,
                                "buyer_pays": buyer_responsible
                            }
                            services_detail.append(service_info)
                            
                            # Flag if buyerResponsibleForShipping is False
                            if buyer_responsible is False:
                                buyer_responsible_issues.append(f"{svc_code} has buyerResponsibleForShipping=False")
                    
                    policy_info = {
                        "policy_id": config_policy_id,
                        "policy_name": policy.get('name'),
                        "has_shipping_options": len(shipping_options) > 0,
                        "shipping_options_count": len(shipping_options),
                        "services": [s["code"] for s in services_detail],
                        "services_detail": services_detail,
                        "buyer_responsible_issues": buyer_responsible_issues
                    }
                    
                    if buyer_responsible_issues:
                        policy_info["warning"] = "Some services have buyerResponsibleForShipping=False. eBay may require buyer to pay for Trading Cards category."
                    
                    debug_info["policies_checked"].append(policy_info)
                else:
                    debug_info["issues_found"].append(f"Config policy {config_policy_id} not found: HTTP {policy_response.status_code}")
            
        except Exception as e:
            debug_info["issues_found"].append(f"Debug error: {str(e)}")
        
        return debug_info
    
    def _debug_return_policy_error(self, group_key: str) -> Dict:
        """Get detailed debugging information for return policy errors (Error 25009)."""
        debug_info = {
            "group_key": group_key,
            "return_policies_checked": [],
            "offers_checked": [],
            "issues_found": []
        }
        
        try:
            # Get the group to find associated SKUs
            group_result = self.get_inventory_item_group(group_key)
            if not group_result.get('success'):
                debug_info["issues_found"].append(f"Could not get inventory item group: {group_result.get('error', 'Unknown')}")
                return debug_info
            
            group_data = group_result.get('data', {})
            variant_skus = group_data.get('variantSKUs', [])
            
            if not variant_skus:
                debug_info["issues_found"].append("No variant SKUs found in group")
                return debug_info
            
            debug_info["issues_found"].append(f"Found {len(variant_skus)} SKUs from variantSKUs field")
            
            # Check return policy ID from config
            return_policy_id = self.config.RETURN_POLICY_ID
            if return_policy_id:
                debug_info["return_policies_checked"].append({
                    "policy_id": return_policy_id,
                    "source": "config",
                    "in_offers": False
                })
            
            # Check each offer's return policy
            for sku in variant_skus[:3]:  # Check first 3
                offer_info = {"sku": sku, "return_policy_id": None, "issues": []}
                
                offer_result = self.get_offer_by_sku(sku)
                if offer_result.get('success') and offer_result.get('offer'):
                    offer = offer_result['offer']
                    offer_id = offer.get('offerId')
                    offer_info["offer_id"] = offer_id
                    
                    # Check for return policy in offer
                    listing_policies = offer.get('listing', {}).get('listingPolicies', {})
                    root_policies = offer.get('listingPolicies', {})
                    
                    return_policy_in_offer = listing_policies.get('returnPolicyId') or root_policies.get('returnPolicyId')
                    offer_info["return_policy_id"] = return_policy_in_offer
                    
                    if not return_policy_in_offer:
                        offer_info["issues"].append("No returnPolicyId in offer")
                    elif return_policy_in_offer != return_policy_id:
                        offer_info["issues"].append(f"Return policy ID mismatch: offer has {return_policy_in_offer}, config has {return_policy_id}")
                
                debug_info["offers_checked"].append(offer_info)
            
            # Print summary
            print(f"\n[DEBUG] Return Policy Debug Summary:")
            print(f"  Config RETURN_POLICY_ID: {return_policy_id}")
            print(f"  Offers checked: {len(debug_info['offers_checked'])}")
            for offer_info in debug_info["offers_checked"]:
                print(f"    SKU {offer_info['sku']}: returnPolicyId = {offer_info.get('return_policy_id', 'NOT SET')}")
                if offer_info.get('issues'):
                    for issue in offer_info['issues']:
                        print(f"      ISSUE: {issue}")
            
        except Exception as e:
            debug_info["issues_found"].append(f"Exception during debug: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return debug_info
