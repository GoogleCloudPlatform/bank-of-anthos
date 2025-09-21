# Assets-DB Test Suite

This directory contains comprehensive unit tests for the assets-db microservice.

## Test Files

### `run_tests.sh`
Main test runner script that automatically detects available testing methods and runs appropriate tests.

```bash
./run_tests.sh
```

### `test_assets_db_docker.sh`
Complete Docker-based testing script that:
- Builds the assets-db Docker image
- Starts a test container
- Runs comprehensive schema validation
- Tests constraints, data types, and performance
- Cleans up test containers

```bash
./test_assets_db_docker.sh
```

### `test_assets_db_sql.sh`
SQL command reference script that provides manual testing commands for when Docker is not available.

```bash
./test_assets_db_sql.sh
```

### `validate_assets_schema.sql`
Comprehensive SQL validation script that can be run directly against a PostgreSQL database.

```bash
psql -U assets-admin -d assets-db -f validate_assets_schema.sql
```

## Test Coverage

### Schema Tests
- ✅ Table existence and structure
- ✅ Primary key and unique constraints
- ✅ Check constraints (tier, amount, price)
- ✅ Indexes performance
- ✅ Data types validation

### Data Tests
- ✅ Data loading verification
- ✅ Tier distribution (1, 2, 3)
- ✅ Null value checks
- ✅ Data integrity validation

### Constraint Tests
- ✅ Tier constraint (rejects invalid tiers)
- ✅ Amount constraint (rejects negative values)
- ✅ Price constraint (rejects zero/negative prices)
- ✅ Unique constraint (rejects duplicates)

### Performance Tests
- ✅ Index performance analysis
- ✅ Query optimization verification

## Prerequisites

### For Docker Tests
- Docker installed and running
- Access to build Docker images

### For SQL Tests
- PostgreSQL client (psql)
- Access to assets-db database
- Database credentials

## Usage Examples

### Quick Test Run
```bash
cd src/assets-db/tests
./run_tests.sh
```

### Docker-only Tests
```bash
cd src/assets-db/tests
./test_assets_db_docker.sh
```

### Manual SQL Testing
```bash
cd src/assets-db/tests
./test_assets_db_sql.sh
# Copy and paste commands when you have database access
```

### Direct SQL Validation
```bash
psql -U assets-admin -d assets-db -f src/assets-db/tests/validate_assets_schema.sql
```

## Expected Results

All tests should pass with:
- 19 comprehensive test categories
- 100% constraint validation
- Sub-millisecond query performance
- Clean data integrity checks
- Proper cleanup procedures

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
