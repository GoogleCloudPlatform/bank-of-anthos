# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
import requests
from typing import Dict, Tuple, Optional
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
USER_PORTFOLIO_DB_URI = os.getenv('USER_PORTFOLIO_DB_URI')
USER_TIER_AGENT_URL = os.getenv('USER_TIER_AGENT_URL', 'http://user-tier-agent:8080')
PORT = int(os.getenv('PORT', 8080))

class InvestmentService:
    """Service for processing investment requests and updating user portfolios."""
    
    def __init__(self):
        self.db_uri = USER_PORTFOLIO_DB_URI
        self.tier_agent_url = USER_TIER_AGENT_URL
    
    def get_db_connection(self):
        """Get database connection to user-portfolio-db."""
        try:
            conn = psycopg2.connect(self.db_uri)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def call_user_tier_agent(self, account_number: str, amount: float) -> Dict[str, float]:
        """
        Call the user-tier-agent to get tier allocation amounts.
        
        Args:
            account_number: User's account number
            amount: Total investment amount
            
        Returns:
            Dictionary with tier1_amt, tier2_amt, tier3_amt
        """
        try:
            payload = {
                "account_number": account_number,
                "amount": amount
            }
            
            logger.info(f"Calling user-tier-agent with payload: {payload}")
            
            response = requests.post(
                f"{self.tier_agent_url}/allocate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Received tier allocation from agent: {result}")
            
            return {
                "tier1_amt": result.get("tier1_amt", 0.0),
                "tier2_amt": result.get("tier2_amt", 0.0),
                "tier3_amt": result.get("tier3_amt", 0.0)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call user-tier-agent: {e}")
            raise Exception(f"User tier agent unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing tier agent response: {e}")
            raise
    
    def get_user_portfolio(self, user_id: str) -> Optional[Dict]:
        """Get existing user portfolio from database."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, user_id, total_value, currency, 
                       tier1_allocation, tier2_allocation, tier3_allocation,
                       tier1_value, tier2_value, tier3_value
                FROM user_portfolios 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get user portfolio: {e}")
            raise
    
    def create_user_portfolio(self, user_id: str, total_value: float, 
                            tier1_amt: float, tier2_amt: float, tier3_amt: float) -> str:
        """Create a new user portfolio."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            portfolio_id = str(uuid.uuid4())
            
            # Calculate allocation percentages
            tier1_allocation = (tier1_amt / total_value) * 100 if total_value > 0 else 0
            tier2_allocation = (tier2_amt / total_value) * 100 if total_value > 0 else 0
            tier3_allocation = (tier3_amt / total_value) * 100 if total_value > 0 else 0
            
            cursor.execute("""
                INSERT INTO user_portfolios 
                (id, user_id, total_value, currency, 
                 tier1_allocation, tier2_allocation, tier3_allocation,
                 tier1_value, tier2_value, tier3_value, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                portfolio_id, user_id, total_value, 'USD',
                tier1_allocation, tier2_allocation, tier3_allocation,
                tier1_amt, tier2_amt, tier3_amt,
                datetime.utcnow(), datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created new portfolio for user {user_id}: {portfolio_id}")
            return portfolio_id
            
        except Exception as e:
            logger.error(f"Failed to create user portfolio: {e}")
            raise
    
    def update_user_portfolio(self, portfolio_id: str, total_value: float,
                            tier1_amt: float, tier2_amt: float, tier3_amt: float):
        """Update existing user portfolio."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Calculate new allocation percentages
            tier1_allocation = (tier1_amt / total_value) * 100 if total_value > 0 else 0
            tier2_allocation = (tier2_amt / total_value) * 100 if total_value > 0 else 0
            tier3_allocation = (tier3_amt / total_value) * 100 if total_value > 0 else 0
            
            cursor.execute("""
                UPDATE user_portfolios 
                SET total_value = %s,
                    tier1_allocation = %s, tier2_allocation = %s, tier3_allocation = %s,
                    tier1_value = %s, tier2_value = %s, tier3_value = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                total_value, tier1_allocation, tier2_allocation, tier3_allocation,
                tier1_amt, tier2_amt, tier3_amt, datetime.utcnow(), portfolio_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated portfolio {portfolio_id}")
            
        except Exception as e:
            logger.error(f"Failed to update user portfolio: {e}")
            raise
    
    def record_transaction(self, portfolio_id: str, transaction_type: str,
                          total_amount: float, tier1_change: float = 0,
                          tier2_change: float = 0, tier3_change: float = 0):
        """Record a portfolio transaction."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            transaction_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO portfolio_transactions 
                (id, portfolio_id, transaction_type, tier1_change, tier2_change, tier3_change,
                 total_amount, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id, portfolio_id, transaction_type,
                tier1_change, tier2_change, tier3_change,
                total_amount, 'COMPLETED', datetime.utcnow(), datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Recorded transaction {transaction_id} for portfolio {portfolio_id}")
            
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")
            raise
    
    def process_investment(self, account_number: str, amount: float) -> Dict:
        """
        Process an investment request.
        
        Args:
            account_number: User's account number
            amount: Investment amount
            
        Returns:
            Dictionary with investment result
        """
        try:
            logger.info(f"Processing investment: account={account_number}, amount={amount}")
            
            # Step 1: Call user-tier-agent to get tier allocations
            tier_allocation = self.call_user_tier_agent(account_number, amount)
            
            tier1_amt = tier_allocation["tier1_amt"]
            tier2_amt = tier_allocation["tier2_amt"]
            tier3_amt = tier_allocation["tier3_amt"]
            
            # Step 2: Get or create user portfolio
            user_id = account_number  # Assuming account_number is the user_id
            portfolio = self.get_user_portfolio(user_id)
            
            if portfolio:
                # Update existing portfolio
                portfolio_id = portfolio["id"]
                new_total = portfolio["total_value"] + amount
                new_tier1 = portfolio["tier1_value"] + tier1_amt
                new_tier2 = portfolio["tier2_value"] + tier2_amt
                new_tier3 = portfolio["tier3_value"] + tier3_amt
                
                self.update_user_portfolio(portfolio_id, new_total, new_tier1, new_tier2, new_tier3)
                
                # Record transaction
                self.record_transaction(
                    portfolio_id, "DEPOSIT", amount, tier1_amt, tier2_amt, tier3_amt
                )
                
                logger.info(f"Updated existing portfolio {portfolio_id}")
                
            else:
                # Create new portfolio
                portfolio_id = self.create_user_portfolio(
                    user_id, amount, tier1_amt, tier2_amt, tier3_amt
                )
                
                # Record transaction
                self.record_transaction(
                    portfolio_id, "DEPOSIT", amount, tier1_amt, tier2_amt, tier3_amt
                )
                
                logger.info(f"Created new portfolio {portfolio_id}")
            
            return {
                "status": "success",
                "portfolio_id": portfolio_id,
                "total_invested": amount,
                "tier1_amount": tier1_amt,
                "tier2_amount": tier2_amt,
                "tier3_amount": tier3_amt,
                "message": "Investment processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to process investment: {e}")
            return {
                "status": "error",
                "message": f"Investment processing failed: {str(e)}"
            }

# Initialize service
investment_service = InvestmentService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check database connection
        conn = investment_service.get_db_connection()
        conn.close()
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "error": str(e)}), 503

@app.route('/invest', methods=['POST'])
def invest():
    """
    Process investment request.
    
    Expected JSON payload:
    {
        "account_number": "string",
        "amount": float
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        account_number = data.get('account_number')
        amount = data.get('amount')
        
        if not account_number:
            return jsonify({"error": "account_number is required"}), 400
        
        if not amount or amount <= 0:
            return jsonify({"error": "amount must be a positive number"}), 400
        
        result = investment_service.process_investment(account_number, amount)
        
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in invest endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/portfolio/<user_id>', methods=['GET'])
def get_portfolio(user_id):
    """Get user portfolio information."""
    try:
        portfolio = investment_service.get_user_portfolio(user_id)
        
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        
        return jsonify(portfolio), 200
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info(f"Starting invest-src service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
