#!/usr/bin/env python3
"""
Simple demo script to run the portfolio frontend with mock services.
This creates a minimal version that shows the portfolio functionality.
"""

import os
import sys
import json
import threading
import time
from flask import Flask, request, jsonify, render_template_string
import requests

# Mock services
def create_mock_services():
    """Create mock backend services for the demo."""
    
    # Mock Investment Manager Service
    investment_app = Flask(__name__)
    portfolios = {}
    transactions = {}
    
    @investment_app.route('/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy"}), 200
    
    @investment_app.route('/api/v1/portfolio/<user_id>', methods=['GET'])
    def get_portfolio(user_id):
        if user_id not in portfolios:
            portfolios[user_id] = {
                "id": f"portfolio-{user_id}",
                "user_id": user_id,
                "total_value": 10000.0,
                "currency": "USD",
                "tier1_allocation": 60.0,
                "tier2_allocation": 30.0,
                "tier3_allocation": 10.0,
                "tier1_value": 6000.0,
                "tier2_value": 3000.0,
                "tier3_value": 1000.0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        return jsonify(portfolios[user_id]), 200
    
    @investment_app.route('/api/v1/portfolio/<user_id>/transactions', methods=['GET'])
    def get_transactions(user_id):
        if user_id not in transactions:
            transactions[user_id] = [
                {
                    "id": "tx-1",
                    "portfolio_id": f"portfolio-{user_id}",
                    "transaction_type": "DEPOSIT",
                    "amount": 5000.0,
                    "tier1_amount": 3000.0,
                    "tier2_amount": 1500.0,
                    "tier3_amount": 500.0,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "id": "tx-2",
                    "portfolio_id": f"portfolio-{user_id}",
                    "transaction_type": "DEPOSIT",
                    "amount": 5000.0,
                    "tier1_amount": 3000.0,
                    "tier2_amount": 1500.0,
                    "tier3_amount": 500.0,
                    "created_at": "2024-01-02T00:00:00Z"
                }
            ]
        return jsonify(transactions[user_id]), 200
    
    @investment_app.route('/api/v1/invest', methods=['POST'])
    def invest():
        data = request.get_json()
        account_number = data.get('account_number', 'demo-user')
        amount = float(data.get('amount', 0))
        
        if account_number not in portfolios:
            portfolios[account_number] = {
                "id": f"portfolio-{account_number}",
                "user_id": account_number,
                "total_value": 0.0,
                "currency": "USD",
                "tier1_allocation": 60.0,
                "tier2_allocation": 30.0,
                "tier3_allocation": 10.0,
                "tier1_value": 0.0,
                "tier2_value": 0.0,
                "tier3_value": 0.0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        
        # Update portfolio
        portfolio = portfolios[account_number]
        portfolio["total_value"] += amount
        portfolio["tier1_value"] += amount * 0.6
        portfolio["tier2_value"] += amount * 0.3
        portfolio["tier3_value"] += amount * 0.1
        portfolio["updated_at"] = "2024-01-03T00:00:00Z"
        
        # Add transaction
        if account_number not in transactions:
            transactions[account_number] = []
        transactions[account_number].append({
            "id": f"tx-{len(transactions[account_number]) + 1}",
            "portfolio_id": portfolio["id"],
            "transaction_type": "DEPOSIT",
            "amount": amount,
            "tier1_amount": amount * 0.6,
            "tier2_amount": amount * 0.3,
            "tier3_amount": amount * 0.1,
            "created_at": "2024-01-03T00:00:00Z"
        })
        
        return jsonify({
            "status": "success",
            "portfolio_id": portfolio["id"],
            "total_invested": amount,
            "tier1_amount": amount * 0.6,
            "tier2_amount": amount * 0.3,
            "tier3_amount": amount * 0.1,
            "message": "Investment processed successfully"
        }), 200
    
    @investment_app.route('/api/v1/withdraw', methods=['POST'])
    def withdraw():
        data = request.get_json()
        account_number = data.get('account_number', 'demo-user')
        amount = float(data.get('amount', 0))
        
        if account_number not in portfolios:
            return jsonify({"error": "Portfolio not found"}), 404
        
        portfolio = portfolios[account_number]
        if portfolio["total_value"] < amount:
            return jsonify({"error": "Insufficient funds"}), 400
        
        # Update portfolio
        portfolio["total_value"] -= amount
        portfolio["tier1_value"] -= amount * 0.6
        portfolio["tier2_value"] -= amount * 0.3
        portfolio["tier3_value"] -= amount * 0.1
        portfolio["updated_at"] = "2024-01-03T00:00:00Z"
        
        # Add transaction
        if account_number not in transactions:
            transactions[account_number] = []
        transactions[account_number].append({
            "id": f"tx-{len(transactions[account_number]) + 1}",
            "portfolio_id": portfolio["id"],
            "transaction_type": "WITHDRAWAL",
            "amount": amount,
            "tier1_amount": amount * 0.6,
            "tier2_amount": amount * 0.3,
            "tier3_amount": amount * 0.1,
            "created_at": "2024-01-03T00:00:00Z"
        })
        
        return jsonify({
            "status": "success",
            "portfolio_id": portfolio["id"],
            "total_withdrawn": amount,
            "tier1_amount": amount * 0.6,
            "tier2_amount": amount * 0.3,
            "tier3_amount": amount * 0.1,
            "message": "Withdrawal processed successfully"
        }), 200
    
    return investment_app

def run_mock_services():
    """Run mock services in background threads."""
    investment_app = create_mock_services()
    
    # Run investment manager service
    investment_app.run(host='0.0.0.0', port=8081, debug=False, use_reloader=False)

def create_demo_frontend():
    """Create a simplified frontend for demo purposes."""
    
    # Read the portfolio template
    with open('src/frontend/templates/portfolio.html', 'r') as f:
        portfolio_template = f.read()
    
    # Create a simple demo frontend
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bank of Anthos - Portfolio Demo</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
            <style>
                .card-button { cursor: pointer; transition: all 0.3s; }
                .card-button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                .tier-card { border-left: 4px solid; }
                .tier-1 { border-left-color: #007bff; }
                .tier-2 { border-left-color: #ffc107; }
                .tier-3 { border-left-color: #dc3545; }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
                <div class="container">
                    <a class="navbar-brand" href="/">Bank of Anthos</a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="/portfolio">
                            <span class="material-icons" style="vertical-align: middle; margin-right: 5px;">trending_up</span>
                            Portfolio
                        </a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-body text-center">
                                <h1 class="card-title">Welcome to Bank of Anthos</h1>
                                <p class="card-text">Portfolio Management Demo</p>
                                <a href="/portfolio" class="btn btn-primary btn-lg">
                                    <span class="material-icons" style="vertical-align: middle; margin-right: 5px;">trending_up</span>
                                    View Portfolio
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    
    @app.route('/portfolio')
    def portfolio():
        # Mock data for demo
        portfolio_data = {
            "id": "portfolio-demo",
            "user_id": "demo-user",
            "total_value": 10000.0,
            "currency": "USD",
            "tier1_allocation": 60.0,
            "tier2_allocation": 30.0,
            "tier3_allocation": 10.0,
            "tier1_value": 6000.0,
            "tier2_value": 3000.0,
            "tier3_value": 1000.0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        transactions_data = [
            {
                "id": "tx-1",
                "portfolio_id": "portfolio-demo",
                "transaction_type": "DEPOSIT",
                "amount": 5000.0,
                "tier1_amount": 3000.0,
                "tier2_amount": 1500.0,
                "tier3_amount": 500.0,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "tx-2",
                "portfolio_id": "portfolio-demo",
                "transaction_type": "DEPOSIT",
                "amount": 5000.0,
                "tier1_amount": 3000.0,
                "tier2_amount": 1500.0,
                "tier3_amount": 500.0,
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
        
        # Simple template rendering
        return render_template_string(portfolio_template, 
                                    portfolio=portfolio_data,
                                    transactions=transactions_data,
                                    account_id="demo-user",
                                    name="Demo User",
                                    bank_name="Bank of Anthos",
                                    format_currency=lambda x: f"${x:,.2f}",
                                    format_timestamp_month=lambda x: "Jan",
                                    format_timestamp_day=lambda x: "01")
    
    return app

def main():
    """Main function to run the demo."""
    print("🚀 Starting Portfolio Management Demo...")
    print("=" * 50)
    
    # Start mock services in background
    print("📡 Starting mock investment manager service...")
    investment_thread = threading.Thread(target=run_mock_services, daemon=True)
    investment_thread.start()
    
    # Wait for services to start
    time.sleep(2)
    
    # Start frontend
    print("🌐 Starting frontend demo...")
    print("📍 Portfolio will be available at: http://localhost:8080/portfolio")
    print("📍 Home page will be available at: http://localhost:8080")
    print("=" * 50)
    print("Press Ctrl+C to stop the demo")
    
    app = create_demo_frontend()
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    main()
