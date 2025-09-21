# Assets Database Service

The `assets-db` service stores investment asset data for the Bank of Anthos portfolio management system.

The container base is a standard PostgreSQL image. On startup, it initializes
a database schema and loads test data using the scripts located in the `initdb/`
directory.

## Database Schema

The assets database contains a single `assets` table with the following structure:

- `asset_id`: Primary key (SERIAL)
- `tier_number`: Investment tier (1, 2, or 3)
- `asset_name`: Unique asset identifier (VARCHAR(64))
- `amount`: Available units for investment (DECIMAL(20, 8))
- `price_per_unit`: Current price per unit in USD (DECIMAL(20, 2))
- `last_updated`: Timestamp of last update (TIMESTAMP WITH TIME ZONE)

### Asset Tiers

- **Tier 1**: Most liquid assets (Cryptocurrencies) - Immediate settlement
- **Tier 2**: Medium liquidity (ETFs, Stocks) - 36-48 hour settlement
- **Tier 3**: Less liquid investments (Real Estate, Private Equity) - Longer settlement

## Environment Variables

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank

- ConfigMap `demo-data-config`:
  - `USE_DEMO_DATA`
    - adds demo asset data to the database when initialized if `True`
    - data is initialized with /src/assets-db/initdb/1-load-testdata.sh

- ConfigMap `assets-db-config`:
  - `POSTGRES_DB`
    - database name
  - `POSTGRES_USER`
    - database username
  - `POSTGRES_PASSWORD`
    - database password
  - `ASSETS_DB_URI`
    - full database connection URI

## Kubernetes Resources

- [deployments/assets-db](/kubernetes-manifests/assets-db.yaml)
- [service/assets-db](/kubernetes-manifests/assets-db.yaml)

## Usage

The assets-db service provides a PostgreSQL database that can be accessed by other services
in the Bank of Anthos ecosystem. Services can connect using the `ASSETS_DB_URI` environment
variable or by connecting to the `assets-db` service on port 5432.

## Testing

Comprehensive unit tests are available in the `tests/` directory:

```bash
# Run all tests
cd tests
./run_tests.sh

# Run Docker-based tests
./test_assets_db_docker.sh

# View SQL test commands
./test_assets_db_sql.sh
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Development

To run the assets-db service locally:

```bash
# Deploy using Skaffold
skaffold dev --module assets-db

# Or deploy directly with kubectl
kubectl apply -f k8s/overlays/development/
```