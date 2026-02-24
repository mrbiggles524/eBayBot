#!/usr/bin/env python3
"""Test the quick_list_ui fetch-checklist endpoint (no auth required)."""

import requests
import json

# Test data
API_URL = "http://localhost:5001/api/fetch-checklist"

test_data = {
    "url": "https://www.beckett.com/news/2025-26-topps-chrome-basketball-cards/",
    "type": "base",
    "defaultPrice": 1.00,
    "defaultQty": 0
}

print("=" * 60)
print("TESTING QUICK_LIST_UI FETCH-CHECKLIST ENDPOINT")
print("=" * 60)
print()

print("[1] Fetching checklist...")
print(f"    URL: {test_data['url']}")
print(f"    Type: {test_data['type']}")
print()

try:
    response = requests.post(API_URL, json=test_data, headers={
        "X-UI-Version": "2.3",
        "Content-Type": "application/json"
    })
    
    print(f"    Response status: {response.status_code}")
    print(f"    Content-Type: {response.headers.get('Content-Type', 'unknown')}")
    print()
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"    [OK] Success: {data.get('success')}")
            print(f"    Count: {data.get('count')}")
            print(f"    Source: {data.get('source')}")
            print(f"    Version: {data.get('version')}")
            print(f"    Timestamp: {data.get('timestamp')}")
            print()
            
            if data.get('count', 0) > 300:
                print(f"    [ERROR] Got {data.get('count')} cards but max is 300!")
                print()
                print(f"    First 10 cards:")
                for i, card in enumerate(data.get('cards', [])[:10]):
                    print(f"      {i+1}. {card.get('number')} - {card.get('name')}")
                print()
                print(f"    Last 10 cards:")
                for i, card in enumerate(data.get('cards', [])[-10:]):
                    print(f"      {i+1}. {card.get('number')} - {card.get('name')}")
                print()
                print(f"    Checking for prefixed cards...")
                prefixed = [c for c in data.get('cards', []) if '-' in str(c.get('number', ''))]
                print(f"    Found {len(prefixed)} cards with prefixes!")
                if prefixed:
                    print(f"    First 5 prefixed cards:")
                    for i, card in enumerate(prefixed[:5]):
                        print(f"      {i+1}. {card.get('number')} - {card.get('name')}")
            else:
                print(f"    [OK] Card count OK: {data.get('count')}")
        except json.JSONDecodeError:
            print(f"    [ERROR] Response is not valid JSON!")
            print(f"    Response text (first 1000 chars): {response.text[:1000]}")
    else:
        print(f"    [ERROR] Error: {response.status_code}")
        print(f"    Response: {response.text[:500]}")
        
except Exception as e:
    print(f"    [ERROR] Request error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
