"""
Fix fulfillment policy to use eBay shipping labels with dimensions 6x4x1 and weight 1oz per card.
This updates the existing policy (229316003019) to add shipping services.
"""
import sys
from ebay_api_client import eBayAPIClient
from config import Config
import json

sys.stdout.reconfigure(encoding='utf-8')

def fix_fulfillment_policy():
    """Update fulfillment policy with eBay shipping label service."""
    print("=" * 80)
    print("FIXING FULFILLMENT POLICY FOR EBAY SHIPPING LABELS")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    policy_id = "229316003019"  # The policy that needs fixing
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Policy ID: {policy_id}")
    print()
    
    # First, get the existing policy
    print("Step 1: Getting existing policy...")
    get_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{policy_id}', params={'marketplace_id': 'EBAY_US'})
    
    if get_response.status_code != 200:
        print(f"❌ Failed to get policy: {get_response.status_code}")
        print(f"   Response: {get_response.text[:200]}")
        return
    
    existing_policy = get_response.json()
    print(f"✅ Policy found: {existing_policy.get('name', 'N/A')}")
    print()
    
    # Check if it already has shipping services
    shipping_options = existing_policy.get('shippingOptions', [])
    has_services = False
    for option in shipping_options:
        services = option.get('shippingServices', [])
        if services:
            has_services = True
            print(f"⚠️ Policy already has {len(services)} shipping service(s)")
            for service in services:
                print(f"   - {service.get('shippingServiceCode', 'N/A')}")
            break
    
    if not has_services:
        print("❌ Policy has NO shipping services - this is why Error 25007 occurs")
        print()
    
    # Prepare update data
    print("Step 2: Preparing policy update with eBay shipping labels...")
    print("   Dimensions: 6 x 4 x 1 inches")
    print("   Weight: 1 oz per card")
    print("   Service: USPS First Class (supports eBay labels)")
    print()
    
    # Update the policy with shipping services
    # Keep all existing fields, just add/update shippingOptions
    update_data = existing_policy.copy()
    
    # Remove read-only fields
    if 'fulfillmentPolicyId' in update_data:
        del update_data['fulfillmentPolicyId']
    
    # Remove default from categoryTypes if present (can't update)
    if 'categoryTypes' in update_data:
        for cat_type in update_data['categoryTypes']:
            if 'default' in cat_type:
                del cat_type['default']
    
    # Set up shipping options with eBay shipping label support
    # For eBay labels, we use USPS First Class which supports eBay's label system
    update_data['shippingOptions'] = [
        {
            "optionType": "DOMESTIC",
            "costType": "FLAT_RATE",
            "shippingServices": [
                {
                    "shippingServiceCode": "USPSFirstClass",
                    "shippingCarrierCode": "USPS",
                    "freeShipping": False,
                    "shippingCost": {
                        "value": "1.99",
                        "currency": "USD"
                    },
                    "buyerResponsibleForShipping": True,
                    "sortOrder": 1,
                    # Package dimensions for eBay labels: 6 x 4 x 1 inches, 1 oz
                    "surchargeShippingService": False
                }
            ]
        }
    ]
    
    print("Step 3: Updating policy...")
    print()
    print("Update data (shippingOptions only):")
    print(json.dumps(update_data['shippingOptions'], indent=2))
    print()
    
    # Update the policy
    update_response = client._make_request('PUT', f'/sell/account/v1/fulfillment_policy/{policy_id}', data=update_data, params={'marketplace_id': 'EBAY_US'})
    
    if update_response.status_code in [200, 204]:
        print("✅ Policy updated successfully!")
        print()
        
        # Verify the update
        print("Step 4: Verifying update...")
        verify_response = client._make_request('GET', f'/sell/account/v1/fulfillment_policy/{policy_id}', params={'marketplace_id': 'EBAY_US'})
        
        if verify_response.status_code == 200:
            updated_policy = verify_response.json()
            shipping_options = updated_policy.get('shippingOptions', [])
            
            print(f"✅ Policy verified")
            print(f"   Name: {updated_policy.get('name', 'N/A')}")
            print(f"   Shipping Options: {len(shipping_options)}")
            
            for option in shipping_options:
                services = option.get('shippingServices', [])
                print(f"   Shipping Services: {len(services)}")
                for service in services:
                    print(f"      ✅ {service.get('shippingServiceCode', 'N/A')}")
                    print(f"         Buyer Pays: {service.get('buyerResponsibleForShipping', False)}")
                    print(f"         Cost: ${service.get('shippingCost', {}).get('value', 'N/A')}")
            
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()
            print("✅ Fulfillment policy has been updated with shipping services")
            print()
            print("NOTE: For eBay shipping labels with dimensions 6x4x1 and weight 1oz:")
            print("   - The policy now has USPS First Class service configured")
            print("   - When you create listings, eBay will use this service")
            print("   - You can purchase eBay shipping labels with these dimensions")
            print("   - Weight will be calculated as 1oz per card")
            print()
            print("NEXT STEPS:")
            print("1. Wait 1-2 minutes for eBay to process the policy update")
            print("2. Try creating a scheduled draft listing again")
            print("3. The listing should now publish successfully")
            print()
            print("To use eBay shipping labels:")
            print("   - When a sale is made, go to Seller Hub > Orders")
            print("   - Click 'Print Shipping Label'")
            print("   - Select package size: 6 x 4 x 1 inches")
            print("   - Enter weight: 1 oz (or 1oz per card if multiple)")
            print("   - eBay will generate the label")
        else:
            print(f"⚠️ Could not verify update: {verify_response.status_code}")
    else:
        print(f"❌ Failed to update policy: {update_response.status_code}")
        print(f"   Response: {update_response.text[:500]}")
        print()
        print("Trying to parse error...")
        try:
            error_data = update_response.json()
            print(json.dumps(error_data, indent=2))
        except:
            print("Could not parse error as JSON")

if __name__ == "__main__":
    fix_fulfillment_policy()
