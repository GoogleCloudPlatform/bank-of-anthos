#!/usr/bin/env python3
"""
Pytest configuration and fixtures for invest-svc tests.
"""

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import invest_src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from invest_src import InvestmentService, app

@pytest.fixture
def test_app():
    """Create a test Flask application."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the Flask application."""
    return test_app.test_client()

@pytest.fixture
def test_service():
    """Create a test InvestmentService instance."""
    service = InvestmentService()
    service.db_uri = os.getenv('TEST_DB_URI', 'postgresql://test:test@localhost:5432/test_invest_db')
    service.tier_agent_url = os.getenv('TEST_TIER_AGENT_URL', 'http://localhost:8081')
    return service

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor

@pytest.fixture
def mock_tier_agent_response():
    """Mock user-tier-agent response."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "tier1_amt": 600.0,
        "tier2_amt": 300.0,
        "tier3_amt": 100.0
    }
    mock_response.raise_for_status.return_value = None
    return mock_response

@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "id": "test-portfolio-id",
        "user_id": "test-user",
        "total_value": 1000.0,
        "currency": "USD",
        "tier1_allocation": 60.0,
        "tier2_allocation": 30.0,
        "tier3_allocation": 10.0,
        "tier1_value": 600.0,
        "tier2_value": 300.0,
        "tier3_value": 100.0,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def sample_investment_request():
    """Sample investment request data for testing."""
    return {
        "account_number": "1234567890",
        "amount": 1000.0
    }

@pytest.fixture
def sample_investment_response():
    """Sample investment response data for testing."""
    return {
        "status": "success",
        "portfolio_id": "test-portfolio-id",
        "total_invested": 1000.0,
        "tier1_amount": 600.0,
        "tier2_amount": 300.0,
        "tier3_amount": 100.0,
        "message": "Investment processed successfully"
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ['TEST_DB_URI'] = 'postgresql://test:test@localhost:5432/test_invest_db'
    os.environ['TEST_TIER_AGENT_URL'] = 'http://localhost:8081'
    yield
    # Cleanup after test
    if 'TEST_DB_URI' in os.environ:
        del os.environ['TEST_DB_URI']
    if 'TEST_TIER_AGENT_URL' in os.environ:
        del os.environ['TEST_TIER_AGENT_URL']

@pytest.fixture
def mock_requests_post():
    """Mock requests.post for testing external service calls."""
    with patch('invest_src.requests.post') as mock_post:
        yield mock_post

@pytest.fixture
def mock_psycopg2_connect():
    """Mock psycopg2.connect for testing database operations."""
    with patch('invest_src.psycopg2.connect') as mock_connect:
        yield mock_connect

@pytest.fixture
def mock_uuid():
    """Mock uuid.uuid4 for testing."""
    with patch('invest_src.uuid.uuid4') as mock_uuid:
        mock_uuid.return_value = 'test-uuid-123'
        yield mock_uuid

@pytest.fixture
def mock_datetime():
    """Mock datetime.utcnow for testing."""
    with patch('invest_src.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = '2024-01-01T00:00:00Z'
        yield mock_datetime
