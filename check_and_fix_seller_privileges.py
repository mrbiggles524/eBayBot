"""
Check seller privileges and opt into required programs.
This will help restore the working state from when listing creation worked.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Check and Fix Seller Privileges")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Step 1: Check seller privileges
    print("Step 1: Checking seller privileges...")
    print()
    
    try:
        response = client._make_request('GET', '/sell/account/v1/privilege')
        
        if response.status_code == 200:
            privileges = response.json()
            print("[OK] Got seller privileges info:")
            print(json.dumps(privileges, indent=2))
            print()
            
            seller_reg_completed = privileges.get('sellerRegistrationCompleted', False)
            selling_limit = privileges.get('sellingLimit', {})
            
            print(f"Seller Registration Completed: {seller_reg_completed}")
            print(f"Selling Limit: {selling_limit}")
            print()
            
            if not seller_reg_completed:
                print("[ERROR] Seller registration is NOT completed!")
                print()
                print("Solution:")
                print("1. Go to: https://sandbox.ebay.com")
                print("2. Sign in with: TESTUSER_manbot")
                print("3. Complete seller registration")
                print("4. Come back and run this script again")
                return
            else:
                print("[OK] Seller registration is completed!")
                
        elif response.status_code == 403:
            print("[ERROR] 403 - Can't check privileges (same issue)")
            print()
            print("This confirms the account needs seller privileges.")
            print("You need to complete seller registration in sandbox.")
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("Next Steps")
    print("=" * 80)
    print()
    print("Since listing creation worked earlier, the account HAD seller privileges.")
    print("Now it doesn't. You need to:")
    print()
    print("1. Go to: https://sandbox.ebay.com")
    print("2. Sign in with: TESTUSER_manbot")
    print("3. Complete seller registration (if prompted)")
    print("4. Opt into business policies (if needed)")
    print("5. Get a new token after completing setup")
    print("6. Try creating listing again")
    print()
    print("The account might have lost seller status, or needs to be re-registered.")

if __name__ == "__main__":
    main()
