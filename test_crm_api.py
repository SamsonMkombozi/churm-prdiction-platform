#!/usr/bin/env python3
"""
Test CRM API Response
Run this to see what the Habari CRM API actually returns
"""

import requests
import json

CRM_API_URL = "https://palegreen-porpoise-596991.hostingersite.com/Web_CRM/api.php"

print("=" * 60)
print("TESTING HABARI CRM API")
print("=" * 60)

# Test 1: Get customers
print("\n1. Testing customers endpoint...")
try:
    response = requests.get(f"{CRM_API_URL}?table=customers", timeout=30)
    print(f"   Status Code: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    
    try:
        data = response.json()
        print(f"   Response Type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"   Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"   List Length: {len(data)}")
            if len(data) > 0:
                print(f"   First Item Type: {type(data[0])}")
                if isinstance(data[0], dict):
                    print(f"   First Item Keys: {list(data[0].keys())}")
        
        print("\n   Raw Response (first 500 chars):")
        print("   " + json.dumps(data, indent=2)[:500])
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        print(f"   Raw text: {response.text[:200]}")
        
except requests.exceptions.RequestException as e:
    print(f"   ❌ Request failed: {e}")

# Test 2: Get payments
print("\n2. Testing payments endpoint...")
try:
    response = requests.get(f"{CRM_API_URL}?table=payments", timeout=30)
    print(f"   Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(f"   Response Type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"   Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"   List Length: {len(data)}")
            
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        
except requests.exceptions.RequestException as e:
    print(f"   ❌ Request failed: {e}")

# Test 3: Get tickets
print("\n3. Testing tickets endpoint...")
try:
    response = requests.get(f"{CRM_API_URL}?table=tickets", timeout=30)
    print(f"   Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(f"   Response Type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"   Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"   List Length: {len(data)}")
            
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        
except requests.exceptions.RequestException as e:
    print(f"   ❌ Request failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)