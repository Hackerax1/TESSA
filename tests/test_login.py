#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# URL for the test environment
BASE_URL = "http://localhost:5000"  # Change to your server URL if different
TEST_ENDPOINT = f"{BASE_URL}/auth/test-login"
LOGIN_ENDPOINT = f"{BASE_URL}/auth/login"

# Test credentials
admin_user = os.getenv('ADMIN_USER', 'admin')
admin_password = os.getenv('ADMIN_PASSWORD', '')

def test_login_config():
    """Test the login configuration endpoint"""
    print("\n1. Testing login configuration...")
    response = requests.get(TEST_ENDPOINT)
    
    if response.status_code == 200:
        config = response.json()
        print(f"  - Admin user configured: {config.get('admin_user_configured', False)}")
        print(f"  - Admin user: {config.get('admin_user', 'Not available')}")
        print(f"  - Admin password configured: {config.get('admin_password_configured', False)}")
        print(f"  - Content-Type accepted: {config.get('content_type_accepted', 'Not specified')}")
    else:
        print(f"  - Error: {response.status_code} - {response.text}")

def test_login_json():
    """Test login with JSON data"""
    print("\n2. Testing login with JSON data...")
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'username': admin_user,
        'password': admin_password
    }
    
    response = requests.post(LOGIN_ENDPOINT, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if 'token' in result:
            print("  - Login successful! Token received.")
            print(f"  - User ID: {result.get('user_id', 'Not provided')}")
            return True
        else:
            print(f"  - Login failed. Response: {result}")
    else:
        print(f"  - Error: {response.status_code} - {response.text}")
    
    return False

def test_login_form():
    """Test login with form data"""
    print("\n3. Testing login with form data...")
    payload = {
        'username': admin_user,
        'password': admin_password
    }
    
    response = requests.post(LOGIN_ENDPOINT, data=payload)
    
    if response.status_code == 200:
        result = response.json()
        if 'token' in result:
            print("  - Login successful! Token received.")
            print(f"  - User ID: {result.get('user_id', 'Not provided')}")
            return True
        else:
            print(f"  - Login failed. Response: {result}")
    else:
        print(f"  - Error: {response.status_code} - {response.text}")
    
    return False

def test_frontend_fetch():
    """Test login using the same fetch approach as the frontend"""
    print("\n4. Testing login with fetch approach (like frontend)...")
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'username': admin_user,
        'password': admin_password
    }
    
    print(f"  - Using credentials: username={admin_user}, password={'*' * len(admin_password)}")
    
    response = requests.post(LOGIN_ENDPOINT, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if 'token' in result:
            print("  - Login successful! Token received.")
            print(f"  - User ID: {result.get('user_id', 'Not provided')}")
            return True
        else:
            print(f"  - Login failed. Response: {result}")
    else:
        print(f"  - Error: {response.status_code} - {response.text}")
    
    return False

if __name__ == "__main__":
    print("===== PROXMOX NLI LOGIN TEST =====")
    print(f"Testing against: {BASE_URL}")
    
    # Test login configuration
    test_login_config()
    
    # Test login with different methods
    success_json = test_login_json()
    success_form = test_login_form()
    success_fetch = test_frontend_fetch()
    
    print("\n===== TEST RESULTS =====")
    print(f"JSON login: {'SUCCESS' if success_json else 'FAILED'}")
    print(f"Form login: {'SUCCESS' if success_form else 'FAILED'}")
    print(f"Fetch login: {'SUCCESS' if success_fetch else 'FAILED'}")
    
    print("\n===== RECOMMENDATIONS =====")
    if success_json or success_form or success_fetch:
        print("At least one login method worked. The server authentication is functioning.")
        if not success_fetch:
            print("The frontend fetch method failed, which may explain why the login page doesn't work.")
            print("Please check the browser console for any errors when submitting the login form.")
    else:
        print("All login methods failed. Possible issues:")
        print("1. The server might not be running")
        print("2. The ADMIN_USER and ADMIN_PASSWORD environment variables may be incorrect")
        print("3. The authentication handler might not be working properly")