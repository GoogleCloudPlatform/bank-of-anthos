# Portfolio Agent Service

The `portfolioagent` service provides AI-powered portfolio management capabilities with human-in-the-loop (HITL) workflows and guardrails for financial trading operations.

## Features

- **AI-Powered Portfolio Management**: Intelligent portfolio analysis and recommendations
- **Human-in-the-Loop Workflows**: All sensitive operations require human approval
- **Compliance Guardrails**: Built-in risk and compliance checking
- **Secure Trading**: JWT-authenticated trading operations with pre-checks

## Available Tools

1. **read_boa_balances**: Read current balances from Bank of Anthos accounts
2. **analyze_portfolio_risk**: Risk analysis for portfolio decisions
3. **check_portfolio_compliance**: Compliance validation for trades
4. **execute_trade**: Execute trades with pre-checks

## Environment Variables

- `VERSION`: Service version
- `PORT`: Service port (default: 8080)
- `ENABLE_TRACING`: Enable OpenTelemetry tracing
- `ENABLE_METRICS`: Enable metrics collection

## API

The service exposes a gRPC API with the following methods:

- `ProposeAction`: Analyze user query and propose trading actions
- `ConfirmAction`: Execute previously proposed and approved actions

## Security

- JWT-based authentication for all operations
- Sensitive tools require pre-approval and compliance checks
- Risk scoring prevents high-risk operations
- Human confirmation required for all trades

## Deployment

The service is deployed using Skaffold with Kubernetes manifests:

```bash
# Deploy in development
skaffold dev --profile development

# Deploy specific service
skaffold dev --module portfolioagent
```