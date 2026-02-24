"""
Try every possible way to find a return policy ID.
"""
from ebay_api_client import eBayAPIClient
from config import Config
import json
import re

def main():
    print("=" * 80)
    print("Find Return Policy - All Methods")
    print("=" * 80)
    print()
    
    config = Config()
    client = eBayAPIClient()
    
    # Method 1: Try to get account privileges - might have default policies
    print("Method 1: Checking account privileges...")
    try:
        response = client._make_request('GET', '/sell/account/v1/privilege')
        if response.status_code == 200:
            privileges = response.json()
            print(f"  Account privileges retrieved")
            # Check if there's any policy info here
            print(f"  Data: {json.dumps(privileges, indent=2)[:500]}")
    except Exception as e:
        print(f"  [SKIP] {e}")
    
    print()
    
    # Method 2: Try to get opted-in programs
    print("Method 2: Checking opted-in programs...")
    try:
        response = client._make_request('GET', '/sell/account/v1/program/get_opted_in_programs')
        if response.status_code == 200:
            programs = response.json()
            print(f"  Programs: {json.dumps(programs, indent=2)[:300]}")
    except Exception as e:
        print(f"  [SKIP] {e}")
    
    print()
    
    # Method 3: Try Trading API to get seller account (might have policy info)
    print("Method 3: Trying Trading API...")
    try:
        # Trading API endpoint for GetUser
        response = client._make_request('GET', '/Trading', params={
            'callname': 'GetUser',
            'version': '967',
            'siteid': '0'
        })
        if response.status_code == 200:
            print(f"  [OK] Got Trading API response")
            print(f"  Response: {response.text[:300]}")
    except Exception as e:
        print(f"  [SKIP] {e}")
    
    print()
    
    # Method 4: Try to create a minimal offer and see what error we get
    print("Method 4: This won't help find the ID, but...")
    print("  The best approach is to try creating a listing and see the exact error.")
    print("  eBay might tell us what return policy ID format it expects.")
    
    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()
    print("Since we can't find return policies via API, try this:")
    print()
    print("1. The code is now set to try WITHOUT a return policy")
    print("2. Try creating a listing - it will likely fail with Error 25009")
    print("3. BUT - the error message might give us more clues")
    print()
    print("OR - if you have a working listing ID or SKU from your successful listings,")
    print("I can try to extract the return policy from that specific listing.")
    print()
    print("Do you have a listing ID or SKU from one of your working listings?")
    print("If so, I can query that specific listing to get its return policy ID.")

if __name__ == "__main__":
    main()
