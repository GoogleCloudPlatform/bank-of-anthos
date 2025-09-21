# User Portfolio Database

This directory contains the user portfolio database service for the Bank of Anthos application. The database is designed to manage user portfolios with tier-based fund allocation.

## Database Schema

The database contains the following main tables:

- **user_portfolios**: Stores user portfolio information with tier1, tier2, and tier3 investment amounts
- **portfolio_transactions**: Tracks portfolio allocation changes and deposits/withdrawals
- **portfolio_analytics**: Stores calculated portfolio metrics and analytics

## Fund Tiers

The system supports three simple fund tiers:
- **TIER1**: First tier fund
- **TIER2**: Second tier fund  
- **TIER3**: Third tier fund

Users can allocate their investment amounts across these three tiers, with the constraint that the allocation percentages must sum to 100%.

## Key Features

- Simple tier-based allocation system with three fund tiers (TIER1, TIER2, TIER3)
- Users can only invest in these three predefined tiers
- Allocation percentages must sum to 100% across all tiers
- Transaction tracking for allocation changes and deposits/withdrawals
- Portfolio analytics and performance tracking
- Automatic timestamp updates for all tables

## Deployment

The database can be deployed using Kustomize overlays for different environments:

- Development: `kubectl apply -k k8s/overlays/development`
- Staging: `kubectl apply -k k8s/overlays/staging`
- Production: `kubectl apply -k k8s/overlays/production`

## Configuration

Database configuration is managed through ConfigMaps:
- `user-portfolio-db-config`: Database connection settings
- `environment-config`: General environment settings
- `demo-data-config`: Demo data loading settings
