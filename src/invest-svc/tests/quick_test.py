#!/usr/bin/env python3
"""
Quick test script for invest-svc microservice.
Runs basic tests without external dependencies.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from invest_src import InvestmentService, app

def test_service_initialization():
    """Test service initialization."""
    print("Testing service initialization...")
    service = InvestmentService()
    assert service.db_uri is not None
    assert service.tier_agent_url is not None
    print("✅ Service initialization passed")

def test_flask_app_creation():
    """Test Flask app creation."""
    print("Testing Flask app creation...")
    assert app is not None
    assert app.config['TESTING'] == False  # Default value
    print("✅ Flask app creation passed")

@patch('invest_src.requests.post')
def test_tier_agent_call(mock_post):
    """Test user-tier-agent call."""
    print("Testing user-tier-agent call...")
    
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "tier1_amt": 600.0,
        "tier2_amt": 300.0,
        "tier3_amt": 100.0
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    # Test service
    service = InvestmentService()
    service.tier_agent_url = "http://test-agent:8080"
    
    result = service.call_user_tier_agent("1234567890", 1000.0)
    
    assert result["tier1_amt"] == 600.0
    assert result["tier2_amt"] == 300.0
    assert result["tier3_amt"] == 100.0
    print("✅ User-tier-agent call passed")

@patch('invest_src.psycopg2.connect')
def test_database_connection(mock_connect):
    """Test database connection."""
    print("Testing database connection...")
    
    # Mock connection
    mock_conn = Mock()
    mock_connect.return_value = mock_conn
    
    service = InvestmentService()
    service.db_uri = "postgresql://test:test@localhost:5432/test_db"
    
    conn = service.get_db_connection()
    assert conn == mock_conn
    print("✅ Database connection passed")

def test_flask_endpoints():
    """Test Flask endpoints."""
    print("Testing Flask endpoints...")
    
    # Set up test client
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Test health endpoint
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    
    # Test invest endpoint with invalid data
    response = client.post('/invest', json={})
    assert response.status_code == 400
    
    print("✅ Flask endpoints passed")

def test_input_validation():
    """Test input validation."""
    print("Testing input validation...")
    
    service = InvestmentService()
    
    # Test valid inputs
    try:
        service.process_investment("1234567890", 1000.0)
        # Should not raise exception for valid inputs
    except Exception as e:
        # Expected to fail due to missing dependencies, but not due to validation
        assert "account_number" not in str(e).lower()
        assert "amount" not in str(e).lower()
    
    print("✅ Input validation passed")

def test_error_handling():
    """Test error handling."""
    print("Testing error handling...")
    
    service = InvestmentService()
    
    # Test with invalid account number
    result = service.process_investment("", 1000.0)
    assert result["status"] == "error"
    
    # Test with invalid amount
    result = service.process_investment("1234567890", -100.0)
    assert result["status"] == "error"
    
    print("✅ Error handling passed")

def run_all_tests():
    """Run all quick tests."""
    print("=" * 50)
    print("Running quick tests for invest-svc...")
    print("=" * 50)
    
    tests = [
        test_service_initialization,
        test_flask_app_creation,
        test_tier_agent_call,
        test_database_connection,
        test_flask_endpoints,
        test_input_validation,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("🎉 All quick tests passed!")

if __name__ == "__main__":
    run_all_tests()
