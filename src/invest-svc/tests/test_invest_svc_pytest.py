#!/usr/bin/env python3
"""
Pytest-based tests for invest-svc microservice.
More concise and readable tests using pytest fixtures.
"""

import pytest
import json
from unittest.mock import Mock, patch

def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["status"] == "healthy"

def test_readiness_check_success(test_client, mock_psycopg2_connect, mock_db_connection):
    """Test readiness check endpoint success."""
    mock_conn, mock_cursor = mock_db_connection
    mock_psycopg2_connect.return_value = mock_conn
    
    response = test_client.get('/ready')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["status"] == "ready"

def test_readiness_check_failure(test_client, mock_psycopg2_connect):
    """Test readiness check endpoint failure."""
    mock_psycopg2_connect.side_effect = Exception("Database unavailable")
    
    response = test_client.get('/ready')
    assert response.status_code == 503
    
    data = json.loads(response.data)
    assert data["status"] == "not ready"

def test_invest_endpoint_success(test_client, mock_requests_post, mock_tier_agent_response):
    """Test invest endpoint success."""
    mock_requests_post.return_value = mock_tier_agent_response
    
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

def test_get_portfolio_success(test_client, test_service, sample_portfolio_data, mock_psycopg2_connect, mock_db_connection):
    """Test get portfolio endpoint success."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = sample_portfolio_data
    mock_psycopg2_connect.return_value = mock_conn
    
    response = test_client.get('/portfolio/test-user')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data["user_id"] == "test-user"
    assert data["total_value"] == 1000.0

def test_get_portfolio_not_found(test_client, mock_psycopg2_connect, mock_db_connection):
    """Test get portfolio endpoint when portfolio not found."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    mock_psycopg2_connect.return_value = mock_conn
    
    response = test_client.get('/portfolio/nonexistent-user')
    
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert "Portfolio not found" in data["error"]

def test_call_user_tier_agent_success(test_service, mock_requests_post, mock_tier_agent_response):
    """Test successful call to user-tier-agent."""
    mock_requests_post.return_value = mock_tier_agent_response
    
    result = test_service.call_user_tier_agent("1234567890", 1000.0)
    
    expected = {
        "tier1_amt": 600.0,
        "tier2_amt": 300.0,
        "tier3_amt": 100.0
    }
    assert result == expected
    
    mock_requests_post.assert_called_once_with(
        f"{test_service.tier_agent_url}/allocate",
        json={"account_number": "1234567890", "amount": 1000.0},
        timeout=30
    )

def test_call_user_tier_agent_failure(test_service, mock_requests_post):
    """Test user-tier-agent call failure."""
    mock_requests_post.side_effect = Exception("Network error")
    
    with pytest.raises(Exception) as exc_info:
        test_service.call_user_tier_agent("1234567890", 1000.0)
    
    assert "User tier agent unavailable" in str(exc_info.value)

def test_get_user_portfolio_success(test_service, mock_psycopg2_connect, mock_db_connection, sample_portfolio_data):
    """Test successful portfolio retrieval."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = sample_portfolio_data
    mock_psycopg2_connect.return_value = mock_conn
    
    result = test_service.get_user_portfolio("test-user")
    
    assert result is not None
    assert result["user_id"] == "test-user"
    assert result["total_value"] == 1000.0

def test_get_user_portfolio_not_found(test_service, mock_psycopg2_connect, mock_db_connection):
    """Test portfolio not found."""
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    mock_psycopg2_connect.return_value = mock_conn
    
    result = test_service.get_user_portfolio("nonexistent-user")
    
    assert result is None

def test_create_user_portfolio_success(test_service, mock_psycopg2_connect, mock_db_connection, mock_uuid, mock_datetime):
    """Test successful portfolio creation."""
    mock_conn, mock_cursor = mock_db_connection
    mock_psycopg2_connect.return_value = mock_conn
    
    result = test_service.create_user_portfolio(
        "test-user", 1000.0, 600.0, 300.0, 100.0
    )
    
    assert result == "test-uuid-123"
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

def test_update_user_portfolio_success(test_service, mock_psycopg2_connect, mock_db_connection, mock_datetime):
    """Test successful portfolio update."""
    mock_conn, mock_cursor = mock_db_connection
    mock_psycopg2_connect.return_value = mock_conn
    
    test_service.update_user_portfolio(
        "test-portfolio-id", 2000.0, 1200.0, 600.0, 200.0
    )
    
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

def test_record_transaction_success(test_service, mock_psycopg2_connect, mock_db_connection, mock_uuid, mock_datetime):
    """Test successful transaction recording."""
    mock_conn, mock_cursor = mock_db_connection
    mock_psycopg2_connect.return_value = mock_conn
    
    test_service.record_transaction(
        "test-portfolio-id", "DEPOSIT", 1000.0, 600.0, 300.0, 100.0
    )
    
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

def test_process_investment_new_user(test_service, mock_requests_post, mock_tier_agent_response, mock_psycopg2_connect, mock_db_connection, mock_uuid, mock_datetime):
    """Test investment processing for new user."""
    mock_requests_post.return_value = mock_tier_agent_response
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None  # No existing portfolio
    mock_psycopg2_connect.return_value = mock_conn
    
    result = test_service.process_investment("1234567890", 1000.0)
    
    assert result["status"] == "success"
    assert result["portfolio_id"] == "test-uuid-123"
    assert result["total_invested"] == 1000.0
    assert result["tier1_amount"] == 600.0
    assert result["tier2_amount"] == 300.0
    assert result["tier3_amount"] == 100.0

def test_process_investment_existing_user(test_service, mock_requests_post, mock_tier_agent_response, mock_psycopg2_connect, mock_db_connection, sample_portfolio_data):
    """Test investment processing for existing user."""
    mock_requests_post.return_value = mock_tier_agent_response
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = sample_portfolio_data
    mock_psycopg2_connect.return_value = mock_conn
    
    result = test_service.process_investment("1234567890", 500.0)
    
    assert result["status"] == "success"
    assert result["portfolio_id"] == "test-portfolio-id"
    assert result["total_invested"] == 500.0

def test_process_investment_agent_failure(test_service, mock_requests_post):
    """Test investment processing when user-tier-agent fails."""
    mock_requests_post.side_effect = Exception("Agent unavailable")
    
    result = test_service.process_investment("1234567890", 1000.0)
    
    assert result["status"] == "error"
    assert "Investment processing failed" in result["message"]

@pytest.mark.parametrize("account_number,amount,expected_status", [
    ("", 1000.0, "error"),
    ("1234567890", -100.0, "error"),
    ("1234567890", 0.0, "error"),
    ("1234567890", 1000.0, "success"),
])
def test_investment_validation(test_service, account_number, amount, expected_status, mock_requests_post, mock_tier_agent_response, mock_psycopg2_connect, mock_db_connection, mock_uuid, mock_datetime):
    """Test investment validation with various inputs."""
    if expected_status == "success":
        mock_requests_post.return_value = mock_tier_agent_response
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None  # No existing portfolio
        mock_psycopg2_connect.return_value = mock_conn
    
    result = test_service.process_investment(account_number, amount)
    
    assert result["status"] == expected_status

def test_database_connection_failure(test_service, mock_psycopg2_connect):
    """Test database connection failure handling."""
    mock_psycopg2_connect.side_effect = Exception("Connection failed")
    
    with pytest.raises(Exception) as exc_info:
        test_service.get_db_connection()
    
    assert "Connection failed" in str(exc_info.value)

def test_tier_agent_http_error(test_service, mock_requests_post):
    """Test user-tier-agent HTTP error response."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 500")
    mock_requests_post.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        test_service.call_user_tier_agent("1234567890", 1000.0)
    
    assert "User tier agent unavailable" in str(exc_info.value)
