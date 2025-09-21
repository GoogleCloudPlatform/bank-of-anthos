#!/usr/bin/env python3
"""
Unit tests for invest-svc microservice.
Tests individual components and methods in isolation.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path so we can import invest_src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from invest_src import InvestmentService, app

class TestInvestmentService(unittest.TestCase):
    """Unit tests for InvestmentService class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.service = InvestmentService()
        self.service.db_uri = "postgresql://test:test@localhost:5432/test_db"
        self.service.tier_agent_url = "http://test-agent:8080"
    
    @patch('invest_src.psycopg2.connect')
    def test_get_db_connection_success(self, mock_connect):
        """Test successful database connection."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        result = self.service.get_db_connection()
        
        mock_connect.assert_called_once_with(self.service.db_uri)
        self.assertEqual(result, mock_conn)
    
    @patch('invest_src.psycopg2.connect')
    def test_get_db_connection_failure(self, mock_connect):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception) as context:
            self.service.get_db_connection()
        
        self.assertIn("Connection failed", str(context.exception))
    
    @patch('invest_src.requests.post')
    def test_call_user_tier_agent_success(self, mock_post):
        """Test successful call to user-tier-agent."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tier1_amt": 600.0,
            "tier2_amt": 300.0,
            "tier3_amt": 100.0
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.service.call_user_tier_agent("1234567890", 1000.0)
        
        expected = {
            "tier1_amt": 600.0,
            "tier2_amt": 300.0,
            "tier3_amt": 100.0
        }
        self.assertEqual(result, expected)
        mock_post.assert_called_once_with(
            f"{self.service.tier_agent_url}/allocate",
            json={"account_number": "1234567890", "amount": 1000.0},
            timeout=30
        )
    
    @patch('invest_src.requests.post')
    def test_call_user_tier_agent_failure(self, mock_post):
        """Test user-tier-agent call failure."""
        mock_post.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception) as context:
            self.service.call_user_tier_agent("1234567890", 1000.0)
        
        self.assertIn("User tier agent unavailable", str(context.exception))
    
    @patch('invest_src.requests.post')
    def test_call_user_tier_agent_http_error(self, mock_post):
        """Test user-tier-agent HTTP error response."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.service.call_user_tier_agent("1234567890", 1000.0)
        
        self.assertIn("User tier agent unavailable", str(context.exception))
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_get_user_portfolio_success(self, mock_get_conn):
        """Test successful portfolio retrieval."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([
            {
                'id': 'test-portfolio-id',
                'user_id': 'test-user',
                'total_value': 1000.0,
                'currency': 'USD',
                'tier1_allocation': 60.0,
                'tier2_allocation': 30.0,
                'tier3_allocation': 10.0,
                'tier1_value': 600.0,
                'tier2_value': 300.0,
                'tier3_value': 100.0
            }
        ]))
        mock_cursor.fetchone.return_value = mock_result
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = self.service.get_user_portfolio("test-user")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['user_id'], 'test-user')
        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_get_user_portfolio_not_found(self, mock_get_conn):
        """Test portfolio not found."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        result = self.service.get_user_portfolio("nonexistent-user")
        
        self.assertIsNone(result)
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_create_user_portfolio_success(self, mock_get_conn):
        """Test successful portfolio creation."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        with patch('invest_src.uuid.uuid4', return_value='test-portfolio-id'):
            with patch('invest_src.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = '2024-01-01T00:00:00Z'
                
                result = self.service.create_user_portfolio(
                    "test-user", 1000.0, 600.0, 300.0, 100.0
                )
        
        self.assertEqual(result, 'test-portfolio-id')
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_update_user_portfolio_success(self, mock_get_conn):
        """Test successful portfolio update."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        with patch('invest_src.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = '2024-01-01T00:00:00Z'
            
            self.service.update_user_portfolio(
                "test-portfolio-id", 2000.0, 1200.0, 600.0, 200.0
            )
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_record_transaction_success(self, mock_get_conn):
        """Test successful transaction recording."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        
        with patch('invest_src.uuid.uuid4', return_value='test-transaction-id'):
            with patch('invest_src.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = '2024-01-01T00:00:00Z'
                
                self.service.record_transaction(
                    "test-portfolio-id", "DEPOSIT", 1000.0, 600.0, 300.0, 100.0
                )
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('invest_src.InvestmentService.call_user_tier_agent')
    @patch('invest_src.InvestmentService.get_user_portfolio')
    @patch('invest_src.InvestmentService.create_user_portfolio')
    @patch('invest_src.InvestmentService.record_transaction')
    def test_process_investment_new_user(self, mock_record, mock_create, mock_get_portfolio, mock_call_agent):
        """Test investment processing for new user."""
        # Setup mocks
        mock_call_agent.return_value = {
            "tier1_amt": 600.0,
            "tier2_amt": 300.0,
            "tier3_amt": 100.0
        }
        mock_get_portfolio.return_value = None  # No existing portfolio
        mock_create.return_value = "new-portfolio-id"
        
        result = self.service.process_investment("1234567890", 1000.0)
        
        # Verify calls
        mock_call_agent.assert_called_once_with("1234567890", 1000.0)
        mock_get_portfolio.assert_called_once_with("1234567890")
        mock_create.assert_called_once_with("1234567890", 1000.0, 600.0, 300.0, 100.0)
        mock_record.assert_called_once_with("new-portfolio-id", "DEPOSIT", 1000.0, 600.0, 300.0, 100.0)
        
        # Verify result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], "new-portfolio-id")
        self.assertEqual(result["total_invested"], 1000.0)
        self.assertEqual(result["tier1_amount"], 600.0)
        self.assertEqual(result["tier2_amount"], 300.0)
        self.assertEqual(result["tier3_amount"], 100.0)
    
    @patch('invest_src.InvestmentService.call_user_tier_agent')
    @patch('invest_src.InvestmentService.get_user_portfolio')
    @patch('invest_src.InvestmentService.update_user_portfolio')
    @patch('invest_src.InvestmentService.record_transaction')
    def test_process_investment_existing_user(self, mock_record, mock_update, mock_get_portfolio, mock_call_agent):
        """Test investment processing for existing user."""
        # Setup mocks
        mock_call_agent.return_value = {
            "tier1_amt": 200.0,
            "tier2_amt": 100.0,
            "tier3_amt": 50.0
        }
        mock_get_portfolio.return_value = {
            "id": "existing-portfolio-id",
            "total_value": 1000.0,
            "tier1_value": 600.0,
            "tier2_value": 300.0,
            "tier3_value": 100.0
        }
        
        result = self.service.process_investment("1234567890", 350.0)
        
        # Verify calls
        mock_call_agent.assert_called_once_with("1234567890", 350.0)
        mock_get_portfolio.assert_called_once_with("1234567890")
        mock_update.assert_called_once_with("existing-portfolio-id", 1350.0, 800.0, 400.0, 150.0)
        mock_record.assert_called_once_with("existing-portfolio-id", "DEPOSIT", 350.0, 200.0, 100.0, 50.0)
        
        # Verify result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], "existing-portfolio-id")
        self.assertEqual(result["total_invested"], 350.0)
    
    @patch('invest_src.InvestmentService.call_user_tier_agent')
    def test_process_investment_agent_failure(self, mock_call_agent):
        """Test investment processing when user-tier-agent fails."""
        mock_call_agent.side_effect = Exception("Agent unavailable")
        
        result = self.service.process_investment("1234567890", 1000.0)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Investment processing failed", result["message"])


class TestFlaskApp(unittest.TestCase):
    """Unit tests for Flask application endpoints."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_health_check(self, mock_get_conn):
        """Test health check endpoint."""
        response = self.client.get('/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_readiness_check_success(self, mock_get_conn):
        """Test readiness check endpoint success."""
        mock_conn = Mock()
        mock_get_conn.return_value = mock_conn
        
        response = self.client.get('/ready')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ready")
    
    @patch('invest_src.InvestmentService.get_db_connection')
    def test_readiness_check_failure(self, mock_get_conn):
        """Test readiness check endpoint failure."""
        mock_get_conn.side_effect = Exception("Database unavailable")
        
        response = self.client.get('/ready')
        
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "not ready")
    
    @patch('invest_src.InvestmentService.process_investment')
    def test_invest_endpoint_success(self, mock_process):
        """Test invest endpoint success."""
        mock_process.return_value = {
            "status": "success",
            "portfolio_id": "test-portfolio-id",
            "total_invested": 1000.0,
            "tier1_amount": 600.0,
            "tier2_amount": 300.0,
            "tier3_amount": 100.0,
            "message": "Investment processed successfully"
        }
        
        response = self.client.post('/invest', 
            json={"account_number": "1234567890", "amount": 1000.0},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        mock_process.assert_called_once_with("1234567890", 1000.0)
    
    @patch('invest_src.InvestmentService.process_investment')
    def test_invest_endpoint_failure(self, mock_process):
        """Test invest endpoint failure."""
        mock_process.return_value = {
            "status": "error",
            "message": "Investment processing failed"
        }
        
        response = self.client.post('/invest', 
            json={"account_number": "1234567890", "amount": 1000.0},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "error")
    
    def test_invest_endpoint_missing_data(self):
        """Test invest endpoint with missing JSON data."""
        response = self.client.post('/invest')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("No JSON data provided", data["error"])
    
    def test_invest_endpoint_missing_account_number(self):
        """Test invest endpoint with missing account number."""
        response = self.client.post('/invest', 
            json={"amount": 1000.0},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("account_number is required", data["error"])
    
    def test_invest_endpoint_invalid_amount(self):
        """Test invest endpoint with invalid amount."""
        response = self.client.post('/invest', 
            json={"account_number": "1234567890", "amount": -100.0},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("amount must be a positive number", data["error"])
    
    @patch('invest_src.InvestmentService.get_user_portfolio')
    def test_get_portfolio_success(self, mock_get_portfolio):
        """Test get portfolio endpoint success."""
        mock_portfolio = {
            "id": "test-portfolio-id",
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
        mock_get_portfolio.return_value = mock_portfolio
        
        response = self.client.get('/portfolio/test-user')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["user_id"], "test-user")
        mock_get_portfolio.assert_called_once_with("test-user")
    
    @patch('invest_src.InvestmentService.get_user_portfolio')
    def test_get_portfolio_not_found(self, mock_get_portfolio):
        """Test get portfolio endpoint when portfolio not found."""
        mock_get_portfolio.return_value = None
        
        response = self.client.get('/portfolio/nonexistent-user')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("Portfolio not found", data["error"])


if __name__ == '__main__':
    unittest.main()
