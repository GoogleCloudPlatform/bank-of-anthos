#!/usr/bin/env python3
"""
Investment Manager Service
A placeholder service that manages user investment portfolios.
This service will eventually integrate with the invest-svc and user-portfolio-db.
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock data storage (in production, this would be a database)
portfolios = {}
transactions = {}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

@app.route('/ready', methods=['GET'])
def ready():
    """Readiness check endpoint."""
    return jsonify({"status": "ready"}), 200

@app.route('/api/v1/portfolio/<user_id>', methods=['GET'])
def get_portfolio(user_id):
    """Get user portfolio information."""
    if user_id not in portfolios:
        # Create a mock portfolio for new users
        portfolio = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "total_value": 0.0,
            "currency": "USD",
            "tier1_allocation": 60.0,
            "tier2_allocation": 30.0,
            "tier3_allocation": 10.0,
            "tier1_value": 0.0,
            "tier2_value": 0.0,
            "tier3_value": 0.0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        portfolios[user_id] = portfolio
    
    return jsonify(portfolios[user_id]), 200

@app.route('/api/v1/portfolio/<user_id>/transactions', methods=['GET'])
def get_portfolio_transactions(user_id):
    """Get user portfolio transactions."""
    user_transactions = transactions.get(user_id, [])
    return jsonify(user_transactions), 200

@app.route('/api/v1/invest', methods=['POST'])
def invest():
    """Process investment request."""
    try:
        data = request.get_json()
        account_number = data.get('account_number')
        amount = float(data.get('amount', 0))
        
        if not account_number or amount <= 0:
            return jsonify({"error": "Invalid investment data"}), 400
        
        # Get or create portfolio
        if account_number not in portfolios:
            portfolio = {
                "id": str(uuid.uuid4()),
                "user_id": account_number,
                "total_value": 0.0,
                "currency": "USD",
                "tier1_allocation": 60.0,
                "tier2_allocation": 30.0,
                "tier3_allocation": 10.0,
                "tier1_value": 0.0,
                "tier2_value": 0.0,
                "tier3_value": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            portfolios[account_number] = portfolio
        
        # Calculate tier allocations
        tier1_amount = amount * 0.6
        tier2_amount = amount * 0.3
        tier3_amount = amount * 0.1
        
        # Update portfolio
        portfolio = portfolios[account_number]
        portfolio["total_value"] += amount
        portfolio["tier1_value"] += tier1_amount
        portfolio["tier2_value"] += tier2_amount
        portfolio["tier3_value"] += tier3_amount
        portfolio["updated_at"] = datetime.utcnow().isoformat()
        
        # Record transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "portfolio_id": portfolio["id"],
            "transaction_type": "DEPOSIT",
            "amount": amount,
            "tier1_amount": tier1_amount,
            "tier2_amount": tier2_amount,
            "tier3_amount": tier3_amount,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if account_number not in transactions:
            transactions[account_number] = []
        transactions[account_number].append(transaction)
        
        return jsonify({
            "status": "success",
            "portfolio_id": portfolio["id"],
            "total_invested": amount,
            "tier1_amount": tier1_amount,
            "tier2_amount": tier2_amount,
            "tier3_amount": tier3_amount,
            "message": "Investment processed successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/withdraw', methods=['POST'])
def withdraw():
    """Process withdrawal request."""
    try:
        data = request.get_json()
        account_number = data.get('account_number')
        amount = float(data.get('amount', 0))
        
        if not account_number or amount <= 0:
            return jsonify({"error": "Invalid withdrawal data"}), 400
        
        if account_number not in portfolios:
            return jsonify({"error": "Portfolio not found"}), 404
        
        portfolio = portfolios[account_number]
        
        if portfolio["total_value"] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        
        # Calculate proportional withdrawal from each tier
        tier1_withdrawal = amount * (portfolio["tier1_value"] / portfolio["total_value"])
        tier2_withdrawal = amount * (portfolio["tier2_value"] / portfolio["total_value"])
        tier3_withdrawal = amount * (portfolio["tier3_value"] / portfolio["total_value"])
        
        # Update portfolio
        portfolio["total_value"] -= amount
        portfolio["tier1_value"] -= tier1_withdrawal
        portfolio["tier2_value"] -= tier2_withdrawal
        portfolio["tier3_value"] -= tier3_withdrawal
        portfolio["updated_at"] = datetime.utcnow().isoformat()
        
        # Record transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "portfolio_id": portfolio["id"],
            "transaction_type": "WITHDRAWAL",
            "amount": amount,
            "tier1_amount": tier1_withdrawal,
            "tier2_amount": tier2_withdrawal,
            "tier3_amount": tier3_withdrawal,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if account_number not in transactions:
            transactions[account_number] = []
        transactions[account_number].append(transaction)
        
        return jsonify({
            "status": "success",
            "portfolio_id": portfolio["id"],
            "total_withdrawn": amount,
            "tier1_amount": tier1_withdrawal,
            "tier2_amount": tier2_withdrawal,
            "tier3_amount": tier3_withdrawal,
            "message": "Withdrawal processed successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
