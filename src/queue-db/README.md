# Queue Database Service

The `queue-db` service stores investment and withdrawal requests for the Bank of Anthos portfolio management system.

The container base is a standard PostgreSQL image. On startup, it initializes
a database schema and loads test data using the scripts located in the `initdb/`
directory.

## Database Schema

The queue database contains a single `investment_queue` table with the following structure:

- `queue_id`: Primary key (SERIAL)
- `account_number`: Bank account number making the request (VARCHAR(20))
- `tier_1`: Amount to add/remove from Tier 1 (DECIMAL(20, 8))
- `tier_2`: Amount to add/remove from Tier 2 (DECIMAL(20, 8))
- `tier_3`: Amount to add/remove from Tier 3 (DECIMAL(20, 8))
- `uuid`: Unique identifier for the queue entry (VARCHAR(36))
- `status`: Processing status (VARCHAR(20))
- `created_at`: Timestamp when request was created (TIMESTAMP WITH TIME ZONE)
- `updated_at`: Timestamp when request was last updated (TIMESTAMP WITH TIME ZONE)
- `processed_at`: Timestamp when request was processed (TIMESTAMP WITH TIME ZONE)

### Queue Status Values

- **PENDING**: Request is waiting to be processed
- **PROCESSING**: Request is currently being processed
- **COMPLETED**: Request has been successfully processed
- **FAILED**: Request processing failed
- **CANCELLED**: Request was cancelled

### Tier Investment Types

- **Tier 1**: Cryptocurrencies - Immediate settlement
- **Tier 2**: ETFs/Stocks - 36-48 hour settlement
- **Tier 3**: Alternative Investments - Longer settlement

## Environment Variables

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank

- ConfigMap `demo-data-config`:
  - `USE_DEMO_DATA`
    - adds demo queue data to the database when initialized if `True`
    - data is initialized with /src/queue-db/initdb/1-load-testdata.sh

- ConfigMap `queue-db-config`:
  - `POSTGRES_DB`
    - database name
  - `POSTGRES_USER`
    - database username
  - `POSTGRES_PASSWORD`
    - database password
  - `QUEUE_DB_URI`
    - full database connection URI

## Kubernetes Resources

- [deployments/queue-db](/kubernetes-manifests/queue-db.yaml)
- [service/queue-db](/kubernetes-manifests/queue-db.yaml)

## Usage

The queue-db service provides a PostgreSQL database that can be accessed by other services
in the Bank of Anthos ecosystem. Services can connect using the `QUEUE_DB_URI` environment
variable or by connecting to the `queue-db` service on port 5432.

## Testing

Comprehensive unit tests are available in the `tests/` directory:

```bash
# Run all tests
cd tests
./run_tests.sh

# Run Docker-based tests
./test_queue_db_docker.sh

# View SQL test commands
./test_queue_db_sql.sh
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Development

To run the queue-db service locally:

```bash
# Deploy using Skaffold
skaffold dev --module queue-db

# Or deploy directly with kubectl
kubectl apply -f k8s/overlays/development/
```

## Integration

This database communicates with the `user-request-queue-svc` for processing
investment and withdrawal requests. The service can:

- Add new investment/withdrawal requests to the queue
- Update request status as they are processed
- Query pending requests for processing
- Track request history and status changes

## Data Flow

1. User submits investment/withdrawal request
2. Request is added to `investment_queue` with status 'PENDING'
3. `user-request-queue-svc` processes the request
4. Status is updated to 'PROCESSING' then 'COMPLETED' or 'FAILED'
5. `processed_at` timestamp is set when completed
