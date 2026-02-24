"""Test script to check if policies API is working."""
from ebay_api_client import eBayAPIClient
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("Testing eBay Policies API")
print("=" * 70)
print()

client = eBayAPIClient()

# Test token
print("1. Checking token...")
token = client.config.ebay_token
if token:
    print(f"   ✓ Token found: {token[:20]}...")
else:
    print("   ✗ No token found!")
    print("   Please check your .env file or OAuth setup.")
    sys.exit(1)

print()

# Test Payment Policies
print("2. Testing Payment Policies API...")
try:
    resp = client._make_request('GET', '/sell/account/v1/payment_policy', params={'marketplace_id': 'EBAY_US'})
    print(f"   Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        policies = data.get('paymentPolicies', [])
        print(f"   ✓ Found {len(policies)} payment policies")
        for p in policies[:3]:
            print(f"      - {p.get('name')} (ID: {p.get('paymentPolicyId')})")
    else:
        print(f"   ✗ Error: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print()

# Test Shipping Policies
print("3. Testing Shipping/Fulfillment Policies API...")
try:
    resp = client._make_request('GET', '/sell/account/v1/fulfillment_policy', params={'marketplace_id': 'EBAY_US'})
    print(f"   Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        policies = data.get('fulfillmentPolicies', [])
        print(f"   ✓ Found {len(policies)} shipping policies")
        for p in policies[:3]:
            print(f"      - {p.get('name')} (ID: {p.get('fulfillmentPolicyId')})")
    else:
        print(f"   ✗ Error: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print()

# Test Return Policies
print("4. Testing Return Policies API...")
try:
    resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
    print(f"   Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        policies = data.get('returnPolicies', [])
        print(f"   ✓ Found {len(policies)} return policies")
        for p in policies[:3]:
            print(f"      - {p.get('name')} (ID: {p.get('returnPolicyId')}, Returns: {p.get('returnsAccepted')})")
    else:
        print(f"   ✗ Error: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"   ✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("Test Complete")
print("=" * 70)
