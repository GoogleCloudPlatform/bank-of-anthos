#!/usr/bin/env python3
"""
Simple test script for invest-src microservice.
"""

import requests
import json
import sys

def test_invest_svc():
    """Test the invest-svc service endpoints."""
    
    base_url = "http://localhost:8080"
    
    print("Testing invest-svc microservice...")
    
    # Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test readiness check
    print("\n2. Testing readiness check...")
    try:
        response = requests.get(f"{base_url}/ready")
        print(f"Readiness check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Readiness check failed: {e}")
        return False
    
    # Test investment processing
    print("\n3. Testing investment processing...")
    investment_data = {
        "account_number": "test-account-123",
        "amount": 1000.0
    }
    
    try:
        response = requests.post(
            f"{base_url}/invest",
            json=investment_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Investment response: {response.status_code}")
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Investment test failed: {e}")
        return False
    
    # Test portfolio retrieval
    print("\n4. Testing portfolio retrieval...")
    try:
        response = requests.get(f"{base_url}/portfolio/test-account-123")
        print(f"Portfolio response: {response.status_code}")
        if response.status_code == 200:
            print(f"Portfolio data: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Portfolio error: {response.json()}")
    except Exception as e:
        print(f"Portfolio test failed: {e}")
        return False
    
    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    success = test_invest_svc()
    sys.exit(0 if success else 1)
