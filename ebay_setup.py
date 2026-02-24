"""Automatic setup using eBay user ID to fetch all required information."""
import requests
from typing import Dict, List, Optional
from config import Config
from ebay_api_client import eBayAPIClient

class eBayAutoSetup:
    """Automatically fetches and configures all required eBay settings."""
    
    def __init__(self):
        self.config = Config()
        # Don't validate during init - setup might run before login
        try:
            self.api_client = eBayAPIClient()
        except Exception:
            # If validation fails, we'll handle it in setup_from_user_id
            self.api_client = None
    
    def setup_from_user_id(self, user_id: str = None) -> Dict:
        """
        Automatically set up bot configuration from eBay user ID.
        
        Args:
            user_id: eBay user ID (if None, fetches current user)
            
        Returns:
            Dictionary with setup information and configuration
        """
        print("Starting automatic setup from eBay account...")
        
        # Initialize API client if not already done
        if self.api_client is None:
            try:
                self.config.validate(require_token=False)  # Don't require token for setup
                from ebay_api_client import eBayAPIClient
                self.api_client = eBayAPIClient()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to initialize API client. Please login first: {e}"
                }
        
        setup_info = {
            "user_id": user_id,
            "policies": {},
            "locations": {},
            "account_info": {},
            "recommendations": []
        }
        
        # Get current user if not provided (optional - continue even if it fails)
        if not user_id:
            user_info = self.get_current_user()
            if user_info.get('success'):
                user_id = user_info.get('data', {}).get('username')
                setup_info['user_id'] = user_id
                setup_info['account_info'] = user_info.get('data', {})
                print(f"OK: Found user: {user_id}")
            else:
                # User info is optional - continue with setup
                print(f"WARNING: Could not get user information: {user_info.get('error')}")
                print("Continuing with setup (user info is optional)...")
                setup_info['account_info'] = {'error': user_info.get('error')}
        
        # Fetch all policies
        print("\nFetching policies...")
        policies = self.fetch_all_policies()
        setup_info['policies'] = policies
        
        # Fetch locations
        print("\nFetching merchant locations...")
        locations = self.fetch_locations()
        setup_info['locations'] = locations
        
        # Get account preferences
        print("\nFetching account preferences...")
        preferences = self.get_account_preferences()
        setup_info['preferences'] = preferences
        
        # Generate configuration recommendations
        recommendations = self.generate_recommendations(setup_info)
        setup_info['recommendations'] = recommendations
        
        # Save configuration
        config_result = self.save_configuration(setup_info)
        setup_info['config_saved'] = config_result
        
        print("\nOK: Setup complete!")
        print(f"\nRecommended configuration:")
        for rec in recommendations:
            print(f"  {rec}")
        
        return {
            "success": True,
            "setup_info": setup_info
        }
    
    def get_current_user(self) -> Dict:
        """Get current authenticated user information."""
        try:
            response = self.api_client._make_request(
                'GET',
                '/commerce/identity/v1/user'
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def fetch_all_policies(self) -> Dict:
        """Fetch all available policies."""
        policies = {
            "fulfillment": [],
            "payment": [],
            "return": [],
            "errors": {}
        }
        
        # Fulfillment policies
        fulfillment_result = self.api_client.get_fulfillment_policies()
        policies["fulfillment"] = fulfillment_result.get('policies', [])
        if fulfillment_result.get('error'):
            policies["errors"]["fulfillment"] = fulfillment_result['error']
        if policies["fulfillment"]:
            print(f"  OK: Found {len(policies['fulfillment'])} fulfillment policies")
            for policy in policies["fulfillment"][:3]:  # Show first 3
                print(f"    - {policy.get('name', 'Unnamed')} (ID: {policy.get('fulfillmentPolicyId', 'N/A')})")
        elif fulfillment_result.get('error'):
            print(f"  WARNING: Error fetching fulfillment policies: {fulfillment_result['error']}")
        
        # Payment policies
        payment_result = self.api_client.get_payment_policies()
        policies["payment"] = payment_result.get('policies', [])
        if payment_result.get('error'):
            policies["errors"]["payment"] = payment_result['error']
        if policies["payment"]:
            print(f"  OK: Found {len(policies['payment'])} payment policies")
            for policy in policies["payment"][:3]:
                print(f"    - {policy.get('name', 'Unnamed')} (ID: {policy.get('paymentPolicyId', 'N/A')})")
        elif payment_result.get('error'):
            print(f"  WARNING: Error fetching payment policies: {payment_result['error']}")
        
        # Return policies
        return_result = self.api_client.get_return_policies()
        policies["return"] = return_result.get('policies', [])
        if return_result.get('error'):
            policies["errors"]["return"] = return_result['error']
        if policies["return"]:
            print(f"  OK: Found {len(policies['return'])} return policies")
            for policy in policies["return"][:3]:
                print(f"    - {policy.get('name', 'Unnamed')} (ID: {policy.get('returnPolicyId', 'N/A')})")
        elif return_result.get('error'):
            print(f"  WARNING: Error fetching return policies: {return_result['error']}")
        
        return policies
    
    def fetch_locations(self) -> Dict:
        """Fetch merchant locations."""
        location_result = self.api_client.get_merchant_locations()
        locations = location_result.get('locations', [])
        error = location_result.get('error')
        
        if locations:
            print(f"  OK: Found {len(locations)} merchant locations")
            for location in locations:
                print(f"    - {location.get('location', {}).get('locationId', 'N/A')} (Key: {location.get('merchantLocationKey', 'N/A')})")
        elif error:
            print(f"  WARNING: Error fetching merchant locations: {error}")
        else:
            print("  WARNING: No merchant locations found")
        
        return {
            "locations": locations,
            "count": len(locations) if locations else 0,
            "error": error
        }
    
    def get_account_preferences(self) -> Dict:
        """Get account preferences and settings."""
        preferences = {}
        
        # Get seller account preferences
        try:
            response = self.api_client._make_request(
                'GET',
                '/sell/account/v1/selling_limit'
            )
            if response.status_code == 200:
                preferences['selling_limits'] = response.json()
        except Exception:
            pass
        
        # Get account privileges
        try:
            response = self.api_client._make_request(
                'GET',
                '/sell/account/v1/privilege'
            )
            if response.status_code == 200:
                preferences['privileges'] = response.json()
        except Exception:
            pass
        
        return preferences
    
    def generate_recommendations(self, setup_info: Dict) -> List[str]:
        """Generate configuration recommendations."""
        recommendations = []
        
        # Policy recommendations
        policies = setup_info.get('policies', {})
        
        if policies.get('fulfillment'):
            best_fulfillment = self._select_best_policy(policies['fulfillment'])
            if best_fulfillment:
                recommendations.append(
                    f"FULFILLMENT_POLICY_ID={best_fulfillment.get('fulfillmentPolicyId')}"
                )
        
        if policies.get('payment'):
            best_payment = self._select_best_policy(policies['payment'])
            if best_payment:
                recommendations.append(
                    f"PAYMENT_POLICY_ID={best_payment.get('paymentPolicyId')}"
                )
        
        if policies.get('return'):
            best_return = self._select_best_policy(policies['return'])
            if best_return:
                recommendations.append(
                    f"RETURN_POLICY_ID={best_return.get('returnPolicyId')}"
                )
        
        # Location recommendations
        locations = setup_info.get('locations', {}).get('locations', [])
        if locations:
            primary_location = locations[0]
            location_key = primary_location.get('merchantLocationKey')
            if location_key:
                recommendations.append(
                    f"MERCHANT_LOCATION_KEY={location_key}"
                )
        
        # User ID recommendation
        user_id = setup_info.get('user_id')
        if user_id:
            recommendations.append(f"# eBay User ID: {user_id}")
        
        return recommendations
    
    def _select_best_policy(self, policies: List[Dict]) -> Optional[Dict]:
        """Select the best policy (prefer default or most common)."""
        if not policies:
            return None
        
        # Look for default policy
        for policy in policies:
            if policy.get('default', False):
                return policy
        
        # Look for policy with most common name
        for policy in policies:
            name = policy.get('name', '').lower()
            if 'default' in name or 'standard' in name:
                return policy
        
        # Return first policy
        return policies[0]
    
    def save_configuration(self, setup_info: Dict) -> Dict:
        """Save configuration to .env file."""
        import os
        
        env_file = '.env'
        env_example = 'env_example.txt'
        
        # Read existing .env if it exists
        existing_config = {}
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key] = value
        
        # Update with new values
        recommendations = setup_info.get('recommendations', [])
        for rec in recommendations:
            if '=' in rec and not rec.startswith('#'):
                key, value = rec.split('=', 1)
                existing_config[key] = value
        
        # Write updated .env
        try:
            # Read template from env_example if it exists
            template_lines = []
            if os.path.exists(env_example):
                with open(env_example, 'r') as f:
                    template_lines = f.readlines()
            
            # Write .env with updated values
            with open(env_file, 'w') as f:
                for line in template_lines:
                    line_stripped = line.strip()
                    if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                        key = line_stripped.split('=', 1)[0]
                        if key in existing_config:
                            f.write(f"{key}={existing_config[key]}\n")
                        else:
                            f.write(line)
                    else:
                        f.write(line)
                
                # Add any new config values
                for key, value in existing_config.items():
                    if not any(key in line for line in template_lines if '=' in line):
                        f.write(f"{key}={value}\n")
            
            return {
                "success": True,
                "message": f"Configuration saved to {env_file}",
                "file": env_file
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_setup(self) -> Dict:
        """Verify that all required configuration is present."""
        print("Verifying setup...")
        
        issues = []
        warnings = []
        
        # Check policies
        policies = self.api_client.get_policy_ids()
        
        if not policies.get('fulfillment_policy_id'):
            issues.append("FULFILLMENT_POLICY_ID not set")
        else:
            print(f"OK: Fulfillment Policy: {policies['fulfillment_policy_id']}")
        
        if not policies.get('payment_policy_id'):
            issues.append("PAYMENT_POLICY_ID not set")
        else:
            print(f"OK: Payment Policy: {policies['payment_policy_id']}")
        
        if not policies.get('return_policy_id'):
            issues.append("RETURN_POLICY_ID not set")
        else:
            print(f"OK: Return Policy: {policies['return_policy_id']}")
        
        if not policies.get('merchant_location_key'):
            warnings.append("MERCHANT_LOCATION_KEY not set (optional - can be set later)")
        else:
            print(f"OK: Merchant Location: {policies['merchant_location_key']}")
        
        # Check API credentials
        if not self.config.EBAY_APP_ID:
            issues.append("EBAY_APP_ID not set")
        else:
            print(f"OK: App ID configured")
        
        # Check token
        if not self.config.ebay_token:
            issues.append("No valid eBay token (run --login first)")
        else:
            print(f"OK: Authentication token present")
        
        if issues:
            return {
                "success": False,
                "issues": issues,
                "warnings": warnings
            }
        else:
            return {
                "success": True,
                "message": "All required configuration is present",
                "warnings": warnings
            }
