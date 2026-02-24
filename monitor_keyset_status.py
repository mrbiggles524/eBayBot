"""
Monitor keyset status and test periodically until it's ready.
"""
import time
import sys
from ebay_api_client import eBayAPIClient
from config import Config
from datetime import datetime

def test_keyset():
    """Test if keyset is working."""
    config = Config()
    client = eBayAPIClient()
    
    # Try a simple API call
    try:
        response = client._make_request('GET', '/sell/inventory/v1/inventory_item', params={'limit': 1})
        
        if response.status_code == 200:
            return True, "Keyset is ENABLED and working!"
        elif response.status_code == 403:
            return False, "Still getting 403 - keyset might still be activating"
        elif response.status_code == 401:
            return False, "Token issue - might need a fresh token"
        else:
            return False, f"Status {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def monitor_keyset(interval_minutes=10, max_attempts=6):
    """Monitor keyset status every N minutes."""
    print("=" * 80)
    print("Keyset Status Monitor")
    print("=" * 80)
    print()
    
    config = Config()
    print(f"Environment: {config.EBAY_ENVIRONMENT.upper()}")
    print(f"Testing every {interval_minutes} minutes")
    print(f"Maximum attempts: {max_attempts}")
    print()
    print("Press Ctrl+C to stop monitoring")
    print()
    print("=" * 80)
    print()
    
    for attempt in range(1, max_attempts + 1):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt}/{max_attempts}")
        print("Testing keyset status...")
        
        is_ready, message = test_keyset()
        
        if is_ready:
            print()
            print("=" * 80)
            print("🎉 SUCCESS! Keyset is READY!")
            print("=" * 80)
            print()
            print(message)
            print()
            print("You can now:")
            print("  1. Create production drafts: python -m streamlit run start.py")
            print("  2. View drafts in eBay Seller Hub")
            print("  3. Start listing your cards!")
            print()
            print("=" * 80)
            return True
        else:
            print(f"  Status: {message}")
            print()
            
            if attempt < max_attempts:
                minutes_left = (max_attempts - attempt) * interval_minutes
                print(f"  Next test in {interval_minutes} minutes...")
                print(f"  (Will test {max_attempts - attempt} more times)")
                print()
                
                # Wait
                for i in range(interval_minutes * 60, 0, -60):
                    mins = i // 60
                    if mins > 0:
                        print(f"  Waiting... {mins} minutes remaining", end='\r')
                    time.sleep(60)
                print()  # New line after countdown
            else:
                print()
                print("=" * 80)
                print("⏳ Keyset not ready yet")
                print("=" * 80)
                print()
                print("After {max_attempts} attempts, keyset is still not ready.")
                print()
                print("Try:")
                print("  1. Get a fresh token from Developer Console")
                print("  2. Update token: python update_production_token.py")
                print("  3. Run this monitor again: python monitor_keyset_status.py")
                print("  4. Or wait longer and test manually")
                print()
    
    return False

if __name__ == "__main__":
    try:
        # Test every 10 minutes, up to 6 times (1 hour total)
        monitor_keyset(interval_minutes=10, max_attempts=6)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        print("You can run this again anytime: python monitor_keyset_status.py")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
