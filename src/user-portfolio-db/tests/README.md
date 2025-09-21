# User Portfolio Database Unit Tests

This directory contains comprehensive unit tests for the user-portfolio-db database schema.

## Test Structure

### Test Files
- `01_schema_validation.sql` - Tests table existence, column structure, constraints, indexes, and triggers
- `02_constraint_tests.sql` - Tests data validation constraints and business rules
- `03_functionality_tests.sql` - Tests triggers, views, and foreign key relationships
- `04_performance_tests.sql` - Tests index performance and concurrent access
- `run_all_tests.sql` - Master test runner that executes all tests

### Test Infrastructure
- `Dockerfile.test` - Docker container for isolated testing
- `docker-compose.test.yml` - Docker Compose setup for test database
- `run_tests.sh` - Shell script for running tests with colored output

## Running Tests

### Method 1: Using Docker Compose (Recommended)

1. **Start the test database:**
   ```bash
   cd src/user-portfolio-db/tests
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **Run all tests:**
   ```bash
   ./run_tests.sh
   ```

3. **Stop the test database:**
   ```bash
   docker-compose -f docker-compose.test.yml down -v
   ```

### Method 2: Using Docker directly

1. **Build the test image:**
   ```bash
   cd src/user-portfolio-db/tests
   docker build -f Dockerfile.test -t user-portfolio-db-test .
   ```

2. **Run tests:**
   ```bash
   docker run --rm user-portfolio-db-test
   ```

### Method 3: Using existing PostgreSQL instance

1. **Ensure PostgreSQL is running and accessible**

2. **Create test database:**
   ```bash
   createdb -U postgres test_user_portfolio_db
   ```

3. **Load schema:**
   ```bash
   psql -U postgres -d test_user_portfolio_db -f ../initdb/0-user-portfolio-schema.sql
   ```

4. **Run individual tests:**
   ```bash
   psql -U postgres -d test_user_portfolio_db -f 01_schema_validation.sql
   psql -U postgres -d test_user_portfolio_db -f 02_constraint_tests.sql
   psql -U postgres -d test_user_portfolio_db -f 03_functionality_tests.sql
   psql -U postgres -d test_user_portfolio_db -f 04_performance_tests.sql
   ```

5. **Or run all tests:**
   ```bash
   psql -U postgres -d test_user_portfolio_db -f run_all_tests.sql
   ```

## Test Categories

### 1. Schema Validation Tests
- ✅ All required tables exist
- ✅ Table columns are correctly defined
- ✅ Constraints are properly set up
- ✅ Indexes are created
- ✅ Triggers are functioning
- ✅ Views are accessible

### 2. Constraint Tests
- ✅ Tier allocation must sum to 100%
- ✅ Tier allocations must be between 0-100%
- ✅ Transaction types are validated
- ✅ Data type constraints work

### 3. Functionality Tests
- ✅ Automatic timestamp updates work
- ✅ Portfolio summary view returns correct data
- ✅ Foreign key relationships work
- ✅ Cascade deletes function properly

### 4. Performance Tests
- ✅ Indexes improve query performance
- ✅ Concurrent access is handled correctly
- ✅ Large dataset operations are efficient

## Expected Output

When tests pass, you should see:
```
✓ Schema Validation
✓ Constraint Tests  
✓ Functionality Tests
✓ Performance Tests

Test Summary
============
Total Tests: 4
Passed: 4
Failed: 0

All tests passed! 🎉
```

## Troubleshooting

### Common Issues

1. **Database connection failed:**
   - Ensure PostgreSQL is running
   - Check connection parameters
   - Verify database exists

2. **Permission denied:**
   - Ensure user has proper database permissions
   - Check file permissions on test scripts

3. **Docker issues:**
   - Ensure Docker is running
   - Check if ports are available
   - Try rebuilding the image

### Debug Mode

To see detailed test output, run individual test files:
```bash
psql -U postgres -d test_user_portfolio_db -f 01_schema_validation.sql
```

This will show all NOTICE messages and any errors that occur during testing.
