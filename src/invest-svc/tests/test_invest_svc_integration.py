#!/usr/bin/env python3
"""
Integration tests for invest-svc microservice.
Tests the service with real database connections and external service calls.
"""

import unittest
import os
import sys
import json
import time
import requests
from unittest.mock import patch

# Add the parent directory to the path so we can import invest_src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from invest_src import InvestmentService, app

class TestInvestSvcIntegration(unittest.TestCase):
    """Integration tests for invest-svc microservice."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with test database."""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # Test database configuration
        cls.test_db_uri = os.getenv('TEST_DB_URI', 'postgresql://test:test@localhost:5432/test_invest_db')
        cls.test_tier_agent_url = os.getenv('TEST_TIER_AGENT_URL', 'http://localhost:8081')
        
        # Initialize service with test configuration
        cls.service = InvestmentService()
        cls.service.db_uri = cls.test_db_uri
        cls.service.tier_agent_url = cls.test_tier_agent_url
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clean up test data before each test
        self.cleanup_test_data()
    
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up test data after each test
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """Clean up test data from database."""
        try:
            conn = self.service.get_db_connection()
            cursor = conn.cursor()
            
            # Delete test transactions
            cursor.execute("DELETE FROM portfolio_transactions WHERE portfolio_id IN (SELECT id FROM user_portfolios WHERE user_id LIKE 'test-%')")
            
            # Delete test portfolios
            cursor.execute("DELETE FROM user_portfolios WHERE user_id LIKE 'test-%'")
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not cleanup test data: {e}")
    
    @patch('invest_src.requests.post')
    def test_full_investment_flow_new_user(self, mock_post):
        """Test complete investment flow for a new user."""
        # Mock user-tier-agent response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tier1_amt": 600.0,
            "tier2_amt": 300.0,
            "tier3_amt": 100.0
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        test_user_id = "test-user-new"
        test_amount = 1000.0
        
        # Process investment
        result = self.service.process_investment(test_user_id, test_amount)
        
        # Verify result
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["portfolio_id"])
        self.assertEqual(result["total_invested"], test_amount)
        self.assertEqual(result["tier1_amount"], 600.0)
        self.assertEqual(result["tier2_amount"], 300.0)
        self.assertEqual(result["tier3_amount"], 100.0)
        
        # Verify portfolio was created in database
        portfolio = self.service.get_user_portfolio(test_user_id)
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["user_id"], test_user_id)
        self.assertEqual(portfolio["total_value"], test_amount)
        self.assertEqual(portfolio["tier1_value"], 600.0)
        self.assertEqual(portfolio["tier2_value"], 300.0)
        self.assertEqual(portfolio["tier3_value"], 100.0)
        
        # Verify allocation percentages
        self.assertEqual(portfolio["tier1_allocation"], 60.0)
        self.assertEqual(portfolio["tier2_allocation"], 30.0)
        self.assertEqual(portfolio["tier3_allocation"], 10.0)
    
    @patch('invest_src.requests.post')
    def test_full_investment_flow_existing_user(self, mock_post):
        """Test complete investment flow for an existing user."""
        # Mock user-tier-agent response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tier1_amt": 200.0,
            "tier2_amt": 100.0,
            "tier3_amt": 50.0
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        test_user_id = "test-user-existing"
        initial_amount = 1000.0
        additional_amount = 350.0
        
        # Create initial portfolio
        initial_result = self.service.process_investment(test_user_id, initial_amount)
        self.assertEqual(initial_result["status"], "success")
        
        # Process additional investment
        additional_result = self.service.process_investment(test_user_id, additional_amount)
        
        # Verify additional investment result
        self.assertEqual(additional_result["status"], "success")
        self.assertEqual(additional_result["total_invested"], additional_amount)
        
        # Verify updated portfolio
        portfolio = self.service.get_user_portfolio(test_user_id)
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["total_value"], initial_amount + additional_amount)
        self.assertEqual(portfolio["tier1_value"], 600.0 + 200.0)
        self.assertEqual(portfolio["tier2_value"], 300.0 + 100.0)
        self.assertEqual(portfolio["tier3_value"], 100.0 + 50.0)
    
    def test_database_connection(self):
        """Test database connection and basic operations."""
        try:
            conn = self.service.get_db_connection()
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
            
            cursor.close()
            conn.close()
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
    
    def test_portfolio_creation_and_retrieval(self):
        """Test portfolio creation and retrieval."""
        test_user_id = "test-portfolio-crud"
        test_amount = 500.0
        
        # Create portfolio
        portfolio_id = self.service.create_user_portfolio(
            test_user_id, test_amount, 300.0, 150.0, 50.0
        )
        
        self.assertIsNotNone(portfolio_id)
        
        # Retrieve portfolio
        portfolio = self.service.get_user_portfolio(test_user_id)
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["user_id"], test_user_id)
        self.assertEqual(portfolio["total_value"], test_amount)
        self.assertEqual(portfolio["tier1_value"], 300.0)
        self.assertEqual(portfolio["tier2_value"], 150.0)
        self.assertEqual(portfolio["tier3_value"], 50.0)
    
    def test_portfolio_update(self):
        """Test portfolio update functionality."""
        test_user_id = "test-portfolio-update"
        initial_amount = 500.0
        updated_amount = 1000.0
        
        # Create initial portfolio
        portfolio_id = self.service.create_user_portfolio(
            test_user_id, initial_amount, 300.0, 150.0, 50.0
        )
        
        # Update portfolio
        self.service.update_user_portfolio(
            portfolio_id, updated_amount, 600.0, 300.0, 100.0
        )
        
        # Verify update
        portfolio = self.service.get_user_portfolio(test_user_id)
        self.assertEqual(portfolio["total_value"], updated_amount)
        self.assertEqual(portfolio["tier1_value"], 600.0)
        self.assertEqual(portfolio["tier2_value"], 300.0)
        self.assertEqual(portfolio["tier3_value"], 100.0)
    
    def test_transaction_recording(self):
        """Test transaction recording functionality."""
        test_user_id = "test-transaction"
        test_amount = 1000.0
        
        # Create portfolio
        portfolio_id = self.service.create_user_portfolio(
            test_user_id, test_amount, 600.0, 300.0, 100.0
        )
        
        # Record transaction
        self.service.record_transaction(
            portfolio_id, "DEPOSIT", test_amount, 600.0, 300.0, 100.0
        )
        
        # Verify transaction was recorded
        conn = self.service.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM portfolio_transactions 
            WHERE portfolio_id = %s AND transaction_type = 'DEPOSIT'
        """, (portfolio_id,))
        
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        cursor.close()
        conn.close()
    
    def test_api_endpoints_integration(self):
        """Test API endpoints with real service calls."""
        # Test health check
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        
        # Test readiness check
        response = self.client.get('/ready')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ready")
    
    @patch('invest_src.requests.post')
    def test_api_invest_endpoint_integration(self, mock_post):
        """Test invest API endpoint with mocked external service."""
        # Mock user-tier-agent response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tier1_amt": 600.0,
            "tier2_amt": 300.0,
            "tier3_amt": 100.0
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test invest endpoint
        response = self.client.post('/invest', 
            json={"account_number": "test-api-user", "amount": 1000.0},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_invested"], 1000.0)
        
        # Verify portfolio was created
        portfolio = self.service.get_user_portfolio("test-api-user")
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["total_value"], 1000.0)
    
    def test_error_handling_integration(self):
        """Test error handling with real database operations."""
        # Test with invalid user ID
        result = self.service.process_investment("", 1000.0)
        self.assertEqual(result["status"], "error")
        
        # Test with invalid amount
        result = self.service.process_investment("test-user", -100.0)
        self.assertEqual(result["status"], "error")
    
    def test_database_constraints(self):
        """Test database constraints and validation."""
        test_user_id = "test-constraints"
        
        # Test tier allocation constraint (must sum to 100%)
        try:
            self.service.create_user_portfolio(
                test_user_id, 1000.0, 50.0, 30.0, 25.0  # Sums to 105%
            )
            self.fail("Should have failed due to constraint violation")
        except Exception as e:
            # Expected to fail due to constraint
            self.assertIn("constraint", str(e).lower())
    
    def test_concurrent_operations(self):
        """Test concurrent operations on the same portfolio."""
        test_user_id = "test-concurrent"
        
        # Create initial portfolio
        portfolio_id = self.service.create_user_portfolio(
            test_user_id, 1000.0, 600.0, 300.0, 100.0
        )
        
        # Simulate concurrent updates
        self.service.update_user_portfolio(portfolio_id, 1500.0, 900.0, 450.0, 150.0)
        self.service.update_user_portfolio(portfolio_id, 2000.0, 1200.0, 600.0, 200.0)
        
        # Verify final state
        portfolio = self.service.get_user_portfolio(test_user_id)
        self.assertEqual(portfolio["total_value"], 2000.0)
        self.assertEqual(portfolio["tier1_value"], 1200.0)
        self.assertEqual(portfolio["tier2_value"], 600.0)
        self.assertEqual(portfolio["tier3_value"], 200.0)


class TestInvestSvcPerformance(unittest.TestCase):
    """Performance tests for invest-svc microservice."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.service = InvestmentService()
        self.service.db_uri = os.getenv('TEST_DB_URI', 'postgresql://test:test@localhost:5432/test_invest_db')
        self.service.tier_agent_url = os.getenv('TEST_TIER_AGENT_URL', 'http://localhost:8081')
    
    @patch('invest_src.requests.post')
    def test_bulk_investment_processing(self, mock_post):
        """Test processing multiple investments efficiently."""
        # Mock user-tier-agent response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tier1_amt": 600.0,
            "tier2_amt": 300.0,
            "tier3_amt": 100.0
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Process multiple investments
        start_time = time.time()
        
        for i in range(10):
            result = self.service.process_investment(f"test-bulk-{i}", 1000.0)
            self.assertEqual(result["status"], "success")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance (should complete within reasonable time)
        self.assertLess(processing_time, 10.0)  # Should complete within 10 seconds
        
        # Verify all portfolios were created
        for i in range(10):
            portfolio = self.service.get_user_portfolio(f"test-bulk-{i}")
            self.assertIsNotNone(portfolio)
            self.assertEqual(portfolio["total_value"], 1000.0)


if __name__ == '__main__':
    # Set up test environment
    os.environ['TEST_DB_URI'] = 'postgresql://test:test@localhost:5432/test_invest_db'
    os.environ['TEST_TIER_AGENT_URL'] = 'http://localhost:8081'
    
    unittest.main()
