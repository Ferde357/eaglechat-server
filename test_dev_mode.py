#!/usr/bin/env python3
"""
Test script to verify development mode functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health endpoint shows dev mode"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        
        if data.get("development_mode"):
            print("✅ Development mode is ENABLED")
        else:
            print("❌ Development mode is DISABLED")
        
        print(f"   Status: {data.get('status')}")
        print(f"   Service: {data.get('service')}")
        print(f"   Version: {data.get('version')}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def test_registration_validation():
    """Test registration validation in dev mode"""
    print("\n🔍 Testing registration validation...")
    
    # Test localhost URL (should work in dev mode)
    test_data = {
        "site_url": "http://localhost:8080",
        "admin_email": "test@example.com", 
        "callback_token": "test123"  # Short token (should work in dev mode)
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/register",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            error_data = response.json()
            # Check if it's the callback verification error (expected)
            if "Failed to verify callback token" in str(error_data):
                print("✅ URL validation passed - failing on callback verification (expected)")
            else:
                print(f"❌ Unexpected validation error: {error_data}")
        else:
            print(f"✅ Registration request accepted (status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")

def test_private_ip_validation():
    """Test private IP validation in dev mode"""
    print("\n🔍 Testing private IP validation...")
    
    test_data = {
        "site_url": "http://192.168.1.100:8080",
        "admin_email": "test@example.com",
        "callback_token": "test123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/register",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            error_data = response.json()
            if "Failed to verify callback token" in str(error_data):
                print("✅ Private IP validation passed - failing on callback verification (expected)")
            else:
                print(f"❌ Unexpected validation error: {error_data}")
        else:
            print(f"✅ Private IP request accepted (status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Private IP test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing EagleChat Development Mode")
    print("=" * 50)
    
    test_health_endpoint()
    test_registration_validation()
    test_private_ip_validation()
    
    print("\n" + "=" * 50)
    print("✅ Development mode testing complete!")
    print("\n💡 To test registration:")
    print("   1. Clear registration in WordPress admin")
    print("   2. Try registering again - should work with localhost URLs")
    print("   3. Make sure FastAPI can reach your WordPress site for callback verification")