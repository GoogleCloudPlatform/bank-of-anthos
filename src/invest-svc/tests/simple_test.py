#!/usr/bin/env python3
"""
Simple test script for invest-svc microservice.
Tests core functionality without external dependencies.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_functionality():
    """Test basic functionality without database dependencies."""
    print("Testing basic functionality...")
    
    # Test 1: Service initialization
    print("  ✓ Testing service initialization...")
    
    # Mock the psycopg2 import
    with patch.dict('sys.modules', {'psycopg2': Mock()}):
        from invest_src import InvestmentService, app
        
        service = InvestmentService()
        assert service.db_uri is not None
        assert service.tier_agent_url is not None
        print("    ✓ Service initialization passed")
    
    # Test 2: Flask app creation
    print("  ✓ Testing Flask app creation...")
    assert app is not None
    print("    ✓ Flask app creation passed")
    
    # Test 3: Input validation
    print("  ✓ Testing input validation...")
    
    # Test with empty account number
    result = service.process_investment("", 1000.0)
    assert result["status"] == "error"
    assert "account_number" in result["message"].lower()
    
    # Test with negative amount
    result = service.process_investment("1234567890", -100.0)
    assert result["status"] == "error"
    assert "amount" in result["message"].lower()
    
    # Test with zero amount
    result = service.process_investment("1234567890", 0.0)
    assert result["status"] == "error"
    assert "amount" in result["message"].lower()
    
    print("    ✓ Input validation passed")
    
    # Test 4: Flask endpoints
    print("  ✓ Testing Flask endpoints...")
    
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
    
    # Test invest endpoint with missing account number
    response = client.post('/invest', json={"amount": 1000.0})
    assert response.status_code == 400
    
    # Test invest endpoint with invalid amount
    response = client.post('/invest', json={"account_number": "1234567890", "amount": -100.0})
    assert response.status_code == 400
    
    print("    ✓ Flask endpoints passed")
    
    print("  ✓ All basic functionality tests passed!")

def test_mocked_integration():
    """Test integration with mocked dependencies."""
    print("Testing mocked integration...")
    
    with patch.dict('sys.modules', {'psycopg2': Mock()}):
        from invest_src import InvestmentService, app
        
        service = InvestmentService()
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Mock the user-tier-agent call
        with patch('invest_src.requests.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = {
                "tier1_amt": 600.0,
                "tier2_amt": 300.0,
                "tier3_amt": 100.0
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Mock database operations
            with patch.object(service, 'get_user_portfolio', return_value=None):
                with patch.object(service, 'create_user_portfolio', return_value='test-portfolio-id'):
                    with patch.object(service, 'record_transaction'):
                        # Test investment processing
                        result = service.process_investment("1234567890", 1000.0)
                        
                        assert result["status"] == "success"
                        assert result["portfolio_id"] == "test-portfolio-id"
                        assert result["total_invested"] == 1000.0
                        assert result["tier1_amount"] == 600.0
                        assert result["tier2_amount"] == 300.0
                        assert result["tier3_amount"] == 100.0
                        
                        print("    ✓ Mocked investment processing passed")
        
        # Test API endpoint with mocked dependencies
        with patch('invest_src.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "tier1_amt": 600.0,
                "tier2_amt": 300.0,
                "tier3_amt": 100.0
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with patch.object(service, 'get_user_portfolio', return_value=None):
                with patch.object(service, 'create_user_portfolio', return_value='test-portfolio-id'):
                    with patch.object(service, 'record_transaction'):
                        # Test API endpoint
                        response = client.post('/invest', 
                            json={"account_number": "1234567890", "amount": 1000.0},
                            content_type='application/json'
                        )
                        
                        assert response.status_code == 200
                        data = json.loads(response.data)
                        assert data["status"] == "success"
                        assert data["total_invested"] == 1000.0
                        
                        print("    ✓ Mocked API endpoint passed")
        
        print("  ✓ All mocked integration tests passed!")

def test_error_scenarios():
    """Test error handling scenarios."""
    print("Testing error scenarios...")
    
    with patch.dict('sys.modules', {'psycopg2': Mock()}):
        from invest_src import InvestmentService, app
        
        service = InvestmentService()
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test user-tier-agent failure
        with patch('invest_src.requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            result = service.process_investment("1234567890", 1000.0)
            assert result["status"] == "error"
            assert "Investment processing failed" in result["message"]
            
            print("    ✓ User-tier-agent failure handling passed")
        
        # Test database connection failure
        with patch.object(service, 'get_db_connection', side_effect=Exception("Database error")):
            result = service.process_investment("1234567890", 1000.0)
            assert result["status"] == "error"
            assert "Investment processing failed" in result["message"]
            
            print("    ✓ Database connection failure handling passed")
        
        print("  ✓ All error scenario tests passed!")

def run_all_tests():
    """Run all simple tests."""
    print("=" * 60)
    print("Running Simple Tests for invest-svc...")
    print("=" * 60)
    
    tests = [
        test_basic_functionality,
        test_mocked_integration,
        test_error_scenarios
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
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("❌ Some tests failed!")
        sys.exit(1)
    else:
        print("🎉 All simple tests passed!")

if __name__ == "__main__":
    run_all_tests()
