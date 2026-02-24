"""Check return policies and try to publish a listing."""
from ebay_api_client import eBayAPIClient
from config import Config
import json

config = Config()
client = eBayAPIClient()

print("Checking return policies...")
resp = client._make_request('GET', '/sell/account/v1/return_policy', params={'marketplace_id': 'EBAY_US'})
print(f'Status: {resp.status_code}')

if resp.status_code == 200:
    data = resp.json()
    policies = data.get('returnPolicies', [])
    print(f'Found {len(policies)} return policies:')
    for p in policies[:5]:
        print(f'  - {p.get("name")}: {p.get("returnPolicyId")}')
    
    if policies:
        valid_policy_id = policies[0].get('returnPolicyId')
        print(f'\nUsing return policy: {valid_policy_id}')
        print(f'\nNOTE: Your .env has RETURN_POLICY_ID={config.RETURN_POLICY_ID}')
        print(f'But that policy does not exist. You should update .env to use: {valid_policy_id}')
else:
    print(f'Error: {resp.text[:200]}')
    print('\nNo return policies found. You may need to create one.')
