#!/usr/bin/env python3
"""
Mock version of invest_src.py for testing without database dependencies.
This allows us to test the core logic without requiring PostgreSQL.
"""

import os
import json
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify

# Mock psycopg2 for testing
class MockConnection:
    def __init__(self, *args, **kwargs):
        self.cursor_calls = []
        self.commit_calls = 0
        self.close_calls = 0
    
    def cursor(self):
        return MockCursor()
    
    def commit(self):
        self.commit_calls += 1
    
    def close(self):
        self.close_calls += 1

class MockCursor:
    def __init__(self):
        self.execute_calls = []
        self.fetchone_result = None
        self.fetchall_result = []
    
    def execute(self, query, params=None):
        self.execute_calls.append((query, params))
    
    def fetchone(self):
        return self.fetchone_result
    
    def fetchall(self):
        return self.fetchall_result
    
    def close(self):
        pass

# Mock psycopg2 module
class MockPsycopg2:
    @staticmethod
    def connect(*args, **kwargs):
        return MockConnection(*args, **kwargs)

# Replace psycopg2 with mock
import sys
sys.modules['psycopg2'] = MockPsycopg2()

# Now import the actual module
from invest_src import InvestmentService, app

# Override the service to use mock data
class TestInvestmentService(InvestmentService):
    def __init__(self):
        super().__init__()
        self.portfolios = {}  # In-memory storage for testing
        self.transactions = []
    
    def get_db_connection(self):
        return MockConnection()
    
    def get_user_portfolio(self, user_id):
        """Get user portfolio from mock storage."""
        return self.portfolios.get(user_id)
    
    def create_user_portfolio(self, user_id, total_value, tier1_value, tier2_value, tier3_value):
        """Create user portfolio in mock storage."""
        portfolio_id = str(uuid.uuid4())
        portfolio = {
            'id': portfolio_id,
            'user_id': user_id,
            'total_value': total_value,
            'currency': 'USD',
            'tier1_allocation': (tier1_value / total_value) * 100,
            'tier2_allocation': (tier2_value / total_value) * 100,
            'tier3_allocation': (tier3_value / total_value) * 100,
            'tier1_value': tier1_value,
            'tier2_value': tier2_value,
            'tier3_value': tier3_value,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        self.portfolios[user_id] = portfolio
        return portfolio_id
    
    def update_user_portfolio(self, portfolio_id, total_value, tier1_value, tier2_value, tier3_value):
        """Update user portfolio in mock storage."""
        for user_id, portfolio in self.portfolios.items():
            if portfolio['id'] == portfolio_id:
                portfolio['total_value'] = total_value
                portfolio['tier1_value'] = tier1_value
                portfolio['tier2_value'] = tier2_value
                portfolio['tier3_value'] = tier3_value
                portfolio['tier1_allocation'] = (tier1_value / total_value) * 100
                portfolio['tier2_allocation'] = (tier2_value / total_value) * 100
                portfolio['tier3_allocation'] = (tier3_value / total_value) * 100
                portfolio['updated_at'] = datetime.utcnow().isoformat()
                break
    
    def record_transaction(self, portfolio_id, transaction_type, amount, tier1_amount, tier2_amount, tier3_amount):
        """Record transaction in mock storage."""
        transaction = {
            'id': str(uuid.uuid4()),
            'portfolio_id': portfolio_id,
            'transaction_type': transaction_type,
            'amount': amount,
            'tier1_amount': tier1_amount,
            'tier2_amount': tier2_amount,
            'tier3_amount': tier3_amount,
            'created_at': datetime.utcnow().isoformat()
        }
        self.transactions.append(transaction)

# Create test service instance
test_service = TestInvestmentService()

# Override the service in the app
app.config['TESTING'] = True

# Replace the service instance in the app
import invest_src
invest_src.service = test_service

if __name__ == "__main__":
    print("Test service created successfully!")
    print(f"Service has {len(test_service.portfolios)} portfolios")
    print(f"Service has {len(test_service.transactions)} transactions")
