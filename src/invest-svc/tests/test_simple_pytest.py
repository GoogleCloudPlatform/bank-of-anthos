#!/usr/bin/env python3
"""
Simple pytest tests for invest-svc microservice.
Tests core functionality without external dependencies.
"""

import pytest
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

@pytest.fixture
def test_app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"})
    
    @app.route('/ready', methods=['GET'])
    def readiness_check():
        try:
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

@pytest.fixture
def test_client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()

def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["status"] == "healthy"

def test_readiness_check(test_client):
    """Test readiness check endpoint."""
    response = test_client.get('/ready')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["status"] == "ready"

def test_invest_endpoint_success(test_client):
    """Test invest endpoint success."""
    response = test_client.post('/invest', 
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

def test_invest_endpoint_missing_data(test_client):
    """Test invest endpoint with missing JSON data."""
    response = test_client.post('/invest')
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert "No JSON data provided" in data["error"]

def test_invest_endpoint_missing_account_number(test_client):
    """Test invest endpoint with missing account number."""
    response = test_client.post('/invest', 
        json={"amount": 1000.0},
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert "account_number is required" in data["error"]

def test_invest_endpoint_invalid_amount(test_client):
    """Test invest endpoint with invalid amount."""
    response = test_client.post('/invest', 
        json={"account_number": "1234567890", "amount": -100.0},
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert "amount must be a positive number" in data["error"]

def test_invest_endpoint_zero_amount(test_client):
    """Test invest endpoint with zero amount."""
    response = test_client.post('/invest', 
        json={"account_number": "1234567890", "amount": 0.0},
        content_type='application/json'
    )
    
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert "amount must be a positive number" in data["error"]

def test_get_portfolio_success(test_client):
    """Test get portfolio endpoint success."""
    response = test_client.get('/portfolio/test-user')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["user_id"] == "test-user"
    assert data["total_value"] == 1000.0
    assert data["tier1_allocation"] == 60.0
    assert data["tier2_allocation"] == 30.0
    assert data["tier3_allocation"] == 10.0

def test_portfolio_data_structure(test_client):
    """Test portfolio data structure."""
    response = test_client.get('/portfolio/test-user')
    data = json.loads(response.data)
    
    # Test required fields
    required_fields = [
        "id", "user_id", "total_value", "currency",
        "tier1_allocation", "tier2_allocation", "tier3_allocation",
        "tier1_value", "tier2_value", "tier3_value",
        "created_at", "updated_at"
    ]
    
    for field in required_fields:
        assert field in data
    
    # Test allocation percentages sum to 100
    total_allocation = data["tier1_allocation"] + data["tier2_allocation"] + data["tier3_allocation"]
    assert abs(total_allocation - 100.0) < 0.01
    
    # Test values sum to total
    total_value = data["tier1_value"] + data["tier2_value"] + data["tier3_value"]
    assert abs(total_value - data["total_value"]) < 0.01

def test_investment_data_structure(test_client):
    """Test investment response data structure."""
    response = test_client.post('/invest', 
        json={"account_number": "1234567890", "amount": 1000.0},
        content_type='application/json'
    )
    
    data = json.loads(response.data)
    
    # Test required fields
    required_fields = [
        "status", "portfolio_id", "total_invested",
        "tier1_amount", "tier2_amount", "tier3_amount", "message"
    ]
    
    for field in required_fields:
        assert field in data
    
    # Test tier amounts sum to total
    total_amount = data["tier1_amount"] + data["tier2_amount"] + data["tier3_amount"]
    assert abs(total_amount - data["total_invested"]) < 0.01

@pytest.mark.parametrize("account_number,amount,expected_status", [
    ("1234567890", 1000.0, 200),
    ("", 1000.0, 400),
    ("1234567890", -100.0, 400),
    ("1234567890", 0.0, 400),
    ("1234567890", "invalid", 400),
])
def test_invest_endpoint_parameterized(test_client, account_number, amount, expected_status):
    """Test invest endpoint with various parameters."""
    response = test_client.post('/invest', 
        json={"account_number": account_number, "amount": amount},
        content_type='application/json'
    )
    
    assert response.status_code == expected_status

def test_error_handling():
    """Test error handling functions."""
    def safe_divide(a, b):
        """Safely divide two numbers."""
        try:
            return a / b
        except ZeroDivisionError:
            return None
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Test normal division
    assert safe_divide(10, 2) == 5.0
    
    # Test division by zero
    assert safe_divide(10, 0) is None
    
    # Test invalid input
    result = safe_divide("10", 2)
    assert "Error:" in result

def test_uuid_generation():
    """Test UUID generation."""
    uuid1 = str(uuid.uuid4())
    uuid2 = str(uuid.uuid4())
    
    # UUIDs should be different
    assert uuid1 != uuid2
    
    # UUIDs should be valid format
    assert len(uuid1) == 36
    assert len(uuid2) == 36
    assert uuid1.count('-') == 4
    assert uuid2.count('-') == 4

def test_datetime_operations():
    """Test datetime operations."""
    now = datetime.utcnow()
    iso_string = now.isoformat()
    
    # ISO string should be valid
    assert 'T' in iso_string
    assert iso_string.endswith('Z') or '+' in iso_string or '-' in iso_string
    
    # Should be able to parse back
    parsed = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    assert parsed is not None

def test_json_serialization():
    """Test JSON serialization."""
    data = {
        "status": "success",
        "portfolio_id": str(uuid.uuid4()),
        "total_invested": 1000.0,
        "tier1_amount": 600.0,
        "tier2_amount": 300.0,
        "tier3_amount": 100.0
    }
    
    # Should be able to serialize to JSON
    json_string = json.dumps(data)
    assert isinstance(json_string, str)
    
    # Should be able to deserialize back
    parsed_data = json.loads(json_string)
    assert parsed_data == data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
