# Queue-DB Test Suite

This directory contains comprehensive unit tests for the queue-db microservice.

## Test Files

### `run_tests.sh`
Main test runner script that automatically detects available testing methods and runs appropriate tests.

```bash
./run_tests.sh
```

### `test_queue_db_docker.sh`
Complete Docker-based testing script that:
- Builds the queue-db Docker image
- Starts a test container
- Runs comprehensive schema validation
- Tests constraints, data types, and performance
- Cleans up test containers

```bash
./test_queue_db_docker.sh
```

### `test_queue_db_sql.sh`
SQL command reference script that provides manual testing commands for when Docker is not available.

```bash
./test_queue_db_sql.sh
```

## Test Coverage

### Schema Tests
- ✅ Table existence and structure
- ✅ Primary key and unique constraints
- ✅ Check constraints (status, UUID format)
- ✅ Indexes performance
- ✅ Data types validation

### Data Tests
- ✅ Data loading verification
- ✅ Status distribution (PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED)
- ✅ Null value checks
- ✅ Data integrity validation

### Constraint Tests
- ✅ Status constraint (rejects invalid statuses)
- ✅ UUID format constraint (rejects invalid UUIDs)
- ✅ Negative amounts allowed (for withdrawals)
- ✅ Unique constraint (rejects duplicate UUIDs)

### Performance Tests
- ✅ Index performance analysis
- ✅ Query optimization verification

## Prerequisites

### For Docker Tests
- Docker installed and running
- Access to build Docker images

### For SQL Tests
- PostgreSQL client (psql)
- Access to queue-db database
- Database credentials

## Usage Examples

### Quick Test Run
```bash
cd src/queue-db/tests
./run_tests.sh
```

### Docker-only Tests
```bash
cd src/queue-db/tests
./test_queue_db_docker.sh
```

### Manual SQL Testing
```bash
cd src/queue-db/tests
./test_queue_db_sql.sh
# Copy and paste commands when you have database access
```

## Expected Results

All tests should pass with:
- 19 comprehensive test categories
- 100% constraint validation
- Sub-millisecond query performance
- Clean data integrity checks
- Proper cleanup procedures

## Queue Database Schema

The `investment_queue` table supports:
- **Investments**: Positive values for tier_1, tier_2, tier_3
- **Withdrawals**: Negative values for tier_1, tier_2, tier_3
- **Mixed Operations**: Combination of positive and negative values
- **Status Tracking**: PENDING → PROCESSING → COMPLETED/FAILED/CANCELLED

## Troubleshooting

### Docker Issues
- Ensure Docker daemon is running
- Check available disk space
- Verify Docker permissions

### Database Connection Issues
- Verify database credentials
- Check network connectivity
- Ensure database is running

### Permission Issues
- Make scripts executable: `chmod +x *.sh`
- Check file ownership
- Verify execution permissions
