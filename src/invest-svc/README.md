# Invest Service Microservice

The `invest-svc` microservice handles investment processing by integrating with the user-tier-agent and updating the user-portfolio-db.

## Overview

This service processes investment requests by:
1. Receiving investment requests with account number and amount
2. Calling the user-tier-agent to get tier allocation amounts
3. Updating the user-portfolio-db with the investment details

## API Endpoints

### POST /invest
Process an investment request.

**Request Body:**
```json
{
  "account_number": "string",
  "amount": float
}
```

**Response:**
```json
{
  "status": "success",
  "portfolio_id": "uuid",
  "total_invested": 1000.0,
  "tier1_amount": 600.0,
  "tier2_amount": 300.0,
  "tier3_amount": 100.0,
  "message": "Investment processed successfully"
}
```

### GET /portfolio/{user_id}
Get user portfolio information.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "string",
  "total_value": 1000.0,
  "currency": "USD",
  "tier1_allocation": 60.0,
  "tier2_allocation": 30.0,
  "tier3_allocation": 10.0,
  "tier1_value": 600.0,
  "tier2_value": 300.0,
  "tier3_value": 100.0,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### GET /health
Health check endpoint.

### GET /ready
Readiness check endpoint.

## Configuration

### Environment Variables
- `USER_PORTFOLIO_DB_URI`: Database connection string
- `USER_TIER_AGENT_URL`: URL of the user-tier-agent service
- `PORT`: Service port (default: 8080)

### Dependencies
- **user-portfolio-db**: PostgreSQL database for portfolio storage
- **user-tier-agent**: Service for tier allocation calculations

## Database Operations

The service performs the following database operations:

1. **Portfolio Management:**
   - Creates new portfolios for new users
   - Updates existing portfolios with new investments
   - Calculates tier allocation percentages

2. **Transaction Recording:**
   - Records all investment transactions
   - Tracks tier allocation changes
   - Maintains transaction history

## Deployment

### Using Skaffold (Development)
```bash
cd src/invest-svc
skaffold run
```

### Using Kubernetes Manifests
```bash
kubectl apply -f kubernetes-manifests/invest-svc.yaml
```

### Using Kustomize
```bash
kubectl apply -k k8s/overlays/development
```

## Example Usage

### Process Investment
```bash
curl -X POST http://invest-src:8080/invest \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "1234567890",
    "amount": 1000.0
  }'
```

### Get Portfolio
```bash
curl http://invest-src:8080/portfolio/1234567890
```

## Error Handling

The service handles various error conditions:
- Invalid input parameters
- Database connection failures
- User-tier-agent service unavailable
- Portfolio not found

All errors are returned with appropriate HTTP status codes and error messages.
