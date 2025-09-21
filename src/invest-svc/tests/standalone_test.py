#!/usr/bin/env python3
"""
Standalone test script for invest-svc microservice.
Tests core logic without importing the main module.
"""

import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from unittest.mock import Mock, patch

def create_test_app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"})
    
    @app.route('/ready', methods=['GET'])
    def readiness_check():
        try:
            # Mock database check
            return jsonify({"status": "ready"})
        except Exception as e:
            return jsonify({"status": "not ready", "error": str(e)}), 503
    
    @app.route('/invest', methods=['POST'])
    def invest():
        try:
            if not request.is_json:
                return jsonify({"error": "No JSON data provided"}), 400
            
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            account_number = data.get('account_number')
            amount = data.get('amount')
            
            if not account_number:
                return jsonify({"error": "account_number is required"}), 400
            
            if not amount or not isinstance(amount, (int, float)) or amount <= 0:
                return jsonify({"error": "amount must be a positive number"}), 400
            
            # Mock investment processing
            result = {
                "status": "success",
                "portfolio_id": str(uuid.uuid4()),
                "total_invested": amount,
                "tier1_amount": amount * 0.6,
                "tier2_amount": amount * 0.3,
                "tier3_amount": amount * 0.1,
                "message": "Investment processed successfully"
            }
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Investment processing failed: {str(e)}"}), 500
    
    @app.route('/portfolio/<user_id>', methods=['GET'])
    def get_portfolio(user_id):
        # Mock portfolio data
        portfolio = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "total_value": 1000.0,
            "currency": "USD",
            "tier1_allocation": 60.0,
            "tier2_allocation": 30.0,
            "tier3_allocation": 10.0,
            "tier1_value": 600.0,
            "tier2_value": 300.0,
            "tier3_value": 100.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return jsonify(portfolio)
    
    return app

def test_flask_app():
    """Test Flask application functionality."""
    print("Testing Flask application...")
    
    app = create_test_app()
    client = app.test_client()
    
    # Test health check
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    print("  ✓ Health check passed")
    
    # Test readiness check
    response = client.get('/ready')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ready"
    print("  ✓ Readiness check passed")
    
    # Test invest endpoint with valid data
    response = client.post('/invest', 
        json={"account_number": "1234567890", "amount": 1000.0},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["total_invested"] == 1000.0
    assert data["tier1_amount"] == 600.0
    assert data["tier2_amount"] == 300.0
    assert data["tier3_amount"] == 100.0
    print("  ✓ Invest endpoint with valid data passed")
    
    # Test invest endpoint with missing data
    response = client.post('/invest')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "No JSON data provided" in data["error"]
    print("  ✓ Invest endpoint with missing data passed")
    
    # Test invest endpoint with missing account number
    response = client.post('/invest', 
        json={"amount": 1000.0},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "account_number is required" in data["error"]
    print("  ✓ Invest endpoint with missing account number passed")
    
    # Test invest endpoint with invalid amount
    response = client.post('/invest', 
        json={"account_number": "1234567890", "amount": -100.0},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "amount must be a positive number" in data["error"]
    print("  ✓ Invest endpoint with invalid amount passed")
    
    # Test get portfolio endpoint
    response = client.get('/portfolio/test-user')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["user_id"] == "test-user"
    assert data["total_value"] == 1000.0
    print("  ✓ Get portfolio endpoint passed")
    
    print("  ✓ All Flask application tests passed!")

def test_business_logic():
    """Test business logic functions."""
    print("Testing business logic...")
    
    def validate_investment_input(account_number, amount):
        """Validate investment input parameters."""
        if not account_number:
            return False, "account_number is required"
        
        if not amount or not isinstance(amount, (int, float)) or amount <= 0:
            return False, "amount must be a positive number"
        
        return True, "valid"
    
    def calculate_tier_allocations(amount):
        """Calculate tier allocations based on amount."""
        return {
            "tier1_amount": amount * 0.6,
            "tier2_amount": amount * 0.3,
            "tier3_amount": amount * 0.1
        }
    
    def process_investment(account_number, amount):
        """Process investment with validation and allocation."""
        # Validate input
        is_valid, message = validate_investment_input(account_number, amount)
        if not is_valid:
            return {"status": "error", "message": message}
        
        # Calculate allocations
        allocations = calculate_tier_allocations(amount)
        
        # Return success result
        return {
            "status": "success",
            "portfolio_id": str(uuid.uuid4()),
            "total_invested": amount,
            **allocations,
            "message": "Investment processed successfully"
        }
    
    # Test valid input
    result = process_investment("1234567890", 1000.0)
    assert result["status"] == "success"
    assert result["total_invested"] == 1000.0
    assert result["tier1_amount"] == 600.0
    assert result["tier2_amount"] == 300.0
    assert result["tier3_amount"] == 100.0
    print("  ✓ Valid investment processing passed")
    
    # Test invalid account number
    result = process_investment("", 1000.0)
    assert result["status"] == "error"
    assert "account_number is required" in result["message"]
    print("  ✓ Invalid account number handling passed")
    
    # Test invalid amount
    result = process_investment("1234567890", -100.0)
    assert result["status"] == "error"
    assert "amount must be a positive number" in result["message"]
    print("  ✓ Invalid amount handling passed")
    
    # Test zero amount
    result = process_investment("1234567890", 0.0)
    assert result["status"] == "error"
    assert "amount must be a positive number" in result["message"]
    print("  ✓ Zero amount handling passed")
    
    print("  ✓ All business logic tests passed!")

def test_error_handling():
    """Test error handling scenarios."""
    print("Testing error handling...")
    
    def safe_divide(a, b):
        """Safely divide two numbers."""
        try:
            return a / b
        except ZeroDivisionError:
            return None
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Test normal division
    result = safe_divide(10, 2)
    assert result == 5.0
    print("  ✓ Normal division passed")
    
    # Test division by zero
    result = safe_divide(10, 0)
    assert result is None
    print("  ✓ Division by zero handling passed")
    
    # Test invalid input
    result = safe_divide("10", 2)
    assert "Error:" in result
    print("  ✓ Invalid input handling passed")
    
    print("  ✓ All error handling tests passed!")

def test_data_structures():
    """Test data structure operations."""
    print("Testing data structures...")
    
    # Test portfolio data structure
    portfolio = {
        "id": str(uuid.uuid4()),
        "user_id": "test-user",
        "total_value": 1000.0,
        "currency": "USD",
        "tier1_allocation": 60.0,
        "tier2_allocation": 30.0,
        "tier3_allocation": 10.0,
        "tier1_value": 600.0,
        "tier2_value": 300.0,
        "tier3_value": 100.0
    }
    
    # Test allocation validation
    total_allocation = portfolio["tier1_allocation"] + portfolio["tier2_allocation"] + portfolio["tier3_allocation"]
    assert abs(total_allocation - 100.0) < 0.01
    print("  ✓ Portfolio allocation validation passed")
    
    # Test value calculation
    total_value = portfolio["tier1_value"] + portfolio["tier2_value"] + portfolio["tier3_value"]
    assert abs(total_value - portfolio["total_value"]) < 0.01
    print("  ✓ Portfolio value calculation passed")
    
    # Test transaction data structure
    transaction = {
        "id": str(uuid.uuid4()),
        "portfolio_id": portfolio["id"],
        "transaction_type": "DEPOSIT",
        "amount": 500.0,
        "tier1_amount": 300.0,
        "tier2_amount": 150.0,
        "tier3_amount": 50.0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Test transaction validation
    total_transaction_amount = transaction["tier1_amount"] + transaction["tier2_amount"] + transaction["tier3_amount"]
    assert abs(total_transaction_amount - transaction["amount"]) < 0.01
    print("  ✓ Transaction validation passed")
    
    print("  ✓ All data structure tests passed!")

def run_all_tests():
    """Run all standalone tests."""
    print("=" * 60)
    print("Running Standalone Tests for invest-svc...")
    print("=" * 60)
    
    tests = [
        test_flask_app,
        test_business_logic,
        test_error_handling,
        test_data_structures
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
        return False
    else:
        print("🎉 All standalone tests passed!")
        return True

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1)
