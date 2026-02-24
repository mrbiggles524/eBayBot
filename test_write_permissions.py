"""
Test if we can actually CREATE inventory items (write operation).
Read operations work, but write might still be blocked.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import time

def main():
    print("=" * 80)
    print("Test Write Permissions (Create Inventory Item)")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Try to create a simple test inventory item
    test_sku = f"TEST_WRITE_{int(time.time())}"
    
    print(f"Attempting to create test inventory item: {test_sku}")
    print()
    
    test_item = {
        "product": {
            "title": "Test Item for Write Permission Check",
            "aspects": {
                "Brand": ["Test"],
                "Type": ["Test Item"]
            }
        },
        "condition": "NEW",
        "availability": {
            "shipToLocationAvailability": {
                "quantity": 1
            }
        }
    }
    
    try:
        result = client.create_inventory_item(test_sku, test_item)
        
        if result.get('success'):
            print("[OK] Write operation SUCCESSFUL!")
            print("[OK] You CAN create inventory items!")
            print()
            print("This means:")
            print("1. Token has sell.inventory scope")
            print("2. Account has write permissions")
            print("3. The listing creation should work!")
            print()
            print("If listing creation still fails, the issue is in the listing code, not permissions.")
            
            # Clean up - delete the test item
            print()
            print("Cleaning up test item...")
            try:
                delete_response = client._make_request('DELETE', f'/sell/inventory/v1/inventory_item/{test_sku}')
                if delete_response.status_code in [200, 204]:
                    print("[OK] Test item deleted")
            except:
                pass
                
        else:
            error = result.get('error', 'Unknown error')
            status_code = result.get('status_code', 'N/A')
            
            print(f"[ERROR] Write operation FAILED!")
            print(f"Status: {status_code}")
            print(f"Error: {error}")
            print()
            
            if status_code == 403:
                print("This confirms:")
                print("1. Read operations work (we can GET inventory items)")
                print("2. Write operations are blocked (can't CREATE inventory items)")
                print()
                print("Possible causes:")
                print("- sellerRegistrationCompleted is still false")
                print("- Account needs additional seller setup")
                print("- Sandbox account limitations")
                print()
                print("Solutions:")
                print("1. Wait a few minutes - opt-in might still be processing")
                print("2. Try getting a fresh token (run get_fresh_token.py)")
                print("3. Contact eBay Developer Support about sandbox write permissions")
            else:
                print(f"Unexpected error: {error}")
                
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
