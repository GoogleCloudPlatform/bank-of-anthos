# Investment Manager Service

A microservice that manages user investment portfolios, providing portfolio information, transaction history, and investment/withdrawal capabilities.

## Overview

The Investment Manager Service acts as a frontend-facing API that manages user investment portfolios. It provides:

- Portfolio information retrieval
- Investment processing
- Withdrawal processing
- Transaction history
- Tier-based fund allocation

## API Endpoints

### Health Checks
- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint

### Portfolio Management
- `GET /api/v1/portfolio/{user_id}` - Get user portfolio information
- `GET /api/v1/portfolio/{user_id}/transactions` - Get portfolio transaction history

### Investment Operations
- `POST /api/v1/invest` - Process investment request
- `POST /api/v1/withdraw` - Process withdrawal request

## Request/Response Examples

### Get Portfolio
```bash
GET /api/v1/portfolio/1234567890
```

Response:
```json
{
  "id": "portfolio-uuid",
  "user_id": "1234567890",
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
```

### Invest Funds
```bash
POST /api/v1/invest
Content-Type: application/json

{
  "account_number": "1234567890",
  "amount": 1000.0
}
```

Response:
```json
{
  "status": "success",
  "portfolio_id": "portfolio-uuid",
  "total_invested": 1000.0,
  "tier1_amount": 600.0,
  "tier2_amount": 300.0,
  "tier3_amount": 100.0,
  "message": "Investment processed successfully"
}
```

### Withdraw Funds
```bash
POST /api/v1/withdraw
Content-Type: application/json

{
  "account_number": "1234567890",
  "amount": 500.0
}
```

Response:
```json
{
  "status": "success",
  "portfolio_id": "portfolio-uuid",
  "total_withdrawn": 500.0,
  "tier1_amount": 300.0,
  "tier2_amount": 150.0,
  "tier3_amount": 50.0,
  "message": "Withdrawal processed successfully"
}
```

## Tier Allocation Strategy

The service uses a fixed allocation strategy:
- **Tier 1 (Conservative)**: 60% of investments
- **Tier 2 (Moderate)**: 30% of investments  
- **Tier 3 (Aggressive)**: 10% of investments

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python investment_manager.py
```

### Docker
```bash
# Build image
docker build -t investment-manager-svc .

# Run container
docker run -p 8080:8080 investment-manager-svc
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f ../../kubernetes-manifests/investment-manager-svc.yaml
```

## Environment Variables

- `PORT`: Service port (default: 8080)

## Future Enhancements

This is currently a placeholder service. Future versions will:

1. **Integrate with invest-svc**: Use the actual investment processing service
2. **Database Integration**: Connect to user-portfolio-db for persistent storage
3. **User-tier-agent Integration**: Use dynamic tier allocation based on user risk profile
4. **Authentication**: Add proper JWT token validation
5. **Error Handling**: Enhanced error handling and logging
6. **Monitoring**: Add metrics and observability

## Architecture

```
Frontend → Investment Manager Service → invest-svc → user-portfolio-db
                ↓
         user-tier-agent (future)
```

The Investment Manager Service serves as a facade that:
- Provides a clean API for the frontend
- Handles user authentication and authorization
- Manages portfolio data retrieval and updates
- Coordinates with backend investment services
