"""
Enable seller privileges by opting into SELLING_POLICY_MANAGEMENT program.
This is the programmatic way to enable seller access when the UI doesn't work.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json

def main():
    print("=" * 80)
    print("Enable Seller Privileges via API")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print()
    
    # Step 1: Check current opted-in programs
    print("Step 1: Checking current programs...")
    print()
    
    try:
        response = client._make_request('GET', '/sell/account/v1/program/get_opted_in_programs')
        
        if response.status_code == 200:
            programs = response.json()
            print("[OK] Current opted-in programs:")
            print(json.dumps(programs, indent=2))
            print()
            
            program_types = programs.get('programs', [])
            if program_types:
                print("Already opted into:")
                for prog in program_types:
                    print(f"  - {prog.get('programType', 'Unknown')}")
            else:
                print("Not opted into any programs yet.")
        elif response.status_code == 403:
            print("[WARNING] 403 - Can't check programs (might need seller privileges first)")
        else:
            print(f"[WARNING] Status {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"[WARNING] Could not check programs: {e}")
    
    print()
    print("Step 2: Opting into SELLING_POLICY_MANAGEMENT...")
    print()
    
    # Step 2: Opt into SELLING_POLICY_MANAGEMENT
    try:
        opt_in_data = {
            "programType": "SELLING_POLICY_MANAGEMENT"
        }
        
        response = client._make_request('POST', '/sell/account/v1/program/opt_in', data=opt_in_data)
        
        if response.status_code == 200:
            print("[OK] Successfully opted into SELLING_POLICY_MANAGEMENT!")
            print()
            print("Note: It may take up to 24 hours for the opt-in to process.")
            print("However, it often works immediately. Let's verify...")
            print()
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Verify by checking privileges again
            print("Step 3: Verifying seller privileges...")
            print()
            
            priv_response = client._make_request('GET', '/sell/account/v1/privilege')
            if priv_response.status_code == 200:
                privileges = priv_response.json()
                seller_reg_completed = privileges.get('sellerRegistrationCompleted', False)
                
                if seller_reg_completed:
                    print("[OK] Seller registration is now completed!")
                    print("[OK] You should be able to create listings now!")
                else:
                    print("[INFO] Seller registration still shows as incomplete.")
                    print("This might take a few minutes to update.")
                    print("Try creating a listing - it might work anyway!")
                    
            print()
            print("=" * 80)
            print("Next Steps")
            print("=" * 80)
            print()
            print("1. Try creating a listing again")
            print("2. If it still doesn't work, wait a few minutes and try again")
            print("3. The opt-in might need time to process (up to 24 hours)")
            
        elif response.status_code == 400:
            error_text = response.text
            try:
                error_json = response.json()
                errors = error_json.get('errors', [])
                if errors:
                    error_msg = errors[0].get('message', error_text)
                    print(f"[ERROR] {error_msg}")
                    
                    # Check if already opted in
                    if "already" in error_msg.lower() or "opted" in error_msg.lower():
                        print()
                        print("[INFO] You might already be opted in!")
                        print("Try creating a listing - it should work now.")
            except:
                print(f"[ERROR] HTTP 400: {error_text[:200]}")
                
        elif response.status_code == 403:
            print("[ERROR] 403 - Access denied")
            print()
            print("The token doesn't have permission to opt into programs.")
            print("This might mean:")
            print("1. Token is missing sell.account scope")
            print("2. Account needs seller registration completed first (catch-22)")
            print()
            print("Try getting a new token with explicit scopes:")
            print("  sell.account")
            print("  sell.inventory")
            print("  sell.fulfillment")
            
        elif response.status_code == 500:
            print("[ERROR] HTTP 500 - Server error")
            print()
            print("eBay's sandbox sometimes has issues with this endpoint.")
            print("This is a known issue. Try again in a few minutes.")
            
        else:
            print(f"[ERROR] Status {response.status_code}: {response.text[:500]}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
