#!/usr/bin/env python3
"""Test the fetch-checklist endpoint directly with authentication."""

import requests
import json

# Test credentials
LOGIN_URL = "http://localhost:5001/login"
API_URL = "http://localhost:5001/api/fetch-checklist"

# Test data
test_data = {
    "url": "https://www.beckett.com/news/2025-26-topps-chrome-basketball-cards/",
    "type": "base",
    "defaultPrice": 1.00,
    "defaultQty": 0
}

# Create session to maintain cookies
session = requests.Session()

print("=" * 60)
print("TESTING FETCH-CHECKLIST ENDPOINT")
print("=" * 60)
print()

# Step 1: Login
print("[1] Logging in...")
login_data = {
    "email": "manhattanbreaks@gmail.com",
    "password": "Bobbo2365@ss"
}
try:
    login_response = session.post(LOGIN_URL, json=login_data)
    print(f"    Login status: {login_response.status_code}")
    if login_response.status_code == 200:
        print("    [OK] Login successful")
    else:
        print(f"    [ERROR] Login failed: {login_response.text}")
        exit(1)
except Exception as e:
    print(f"    [ERROR] Login error: {e}")
    exit(1)

print()

# Step 2: Fetch checklist
print("[2] Fetching checklist...")
print(f"    URL: {test_data['url']}")
print(f"    Type: {test_data['type']}")
print()

try:
    response = session.post(API_URL, json=test_data, headers={
        "X-UI-Version": "2.3",
        "Content-Type": "application/json"
    })
    
    print(f"    Response status: {response.status_code}")
    print(f"    Response headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        # Check if response is JSON or HTML
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            print(f"    [ERROR] Response is not JSON! Content-Type: {content_type}")
            print(f"    Response text (first 500 chars): {response.text[:500]}")
            exit(1)
        
        data = response.json()
        print(f"    [OK] Success: {data.get('success')}")
        print(f"    Count: {data.get('count')}")
        print(f"    Source: {data.get('source')}")
        print(f"    Version: {data.get('version')}")
        print(f"    Timestamp: {data.get('timestamp')}")
        print()
        
        if data.get('count', 0) > 300:
            print(f"    [ERROR] Got {data.get('count')} cards but max is 300!")
            print(f"    First 5 cards:")
            for i, card in enumerate(data.get('cards', [])[:5]):
                print(f"      {i+1}. {card.get('number')} - {card.get('name')}")
            print()
            print(f"    Last 5 cards:")
            for i, card in enumerate(data.get('cards', [])[-5:]):
                print(f"      {i+1}. {card.get('number')} - {card.get('name')}")
        else:
            print(f"    [OK] Card count OK: {data.get('count')}")
    else:
        print(f"    [ERROR] Error: {response.status_code}")
        print(f"    Response: {response.text}")
        
except Exception as e:
    print(f"    [ERROR] Request error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
