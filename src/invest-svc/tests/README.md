# Invest-SVC Testing Guide

This directory contains comprehensive tests for the invest-svc microservice, including unit tests, integration tests, and performance tests.

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── test_invest_svc_unit.py        # Unit tests (unittest framework)
├── test_invest_svc_pytest.py      # Unit tests (pytest framework)
├── test_invest_svc_integration.py # Integration tests
├── run_tests.py                   # Test runner script
├── requirements-test.txt          # Test dependencies
├── Dockerfile.test                # Docker image for testing
├── docker-compose.test.yml        # Docker Compose for test environment
├── mock-tier-agent.conf           # Mock tier agent configuration
└── README.md                      # This file
```

## Test Types

### 1. Unit Tests
- **Framework**: unittest + pytest
- **Coverage**: Individual methods and functions
- **Mocking**: External dependencies (database, user-tier-agent)
- **Files**: `test_invest_svc_unit.py`, `test_invest_svc_pytest.py`

### 2. Integration Tests
- **Framework**: unittest
- **Coverage**: End-to-end workflows with real database
- **Dependencies**: Test database, mock external services
- **File**: `test_invest_svc_integration.py`

### 3. Performance Tests
- **Framework**: pytest with benchmark plugin
- **Coverage**: Response times, throughput, resource usage
- **File**: `test_invest_svc_pytest.py::TestInvestSvcPerformance`

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (for integration tests)
- Docker and Docker Compose (for containerized testing)

### Install Dependencies
```bash
cd src/invest-svc/tests
pip install -r requirements-test.txt
```

### Run Tests

#### Option 1: Using Test Runner Script
```bash
# Run all tests
python run_tests.py --all

# Run specific test types
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --pytest

# Run with coverage
python run_tests.py --pytest --coverage

# Run in parallel
python run_tests.py --pytest --parallel
```

#### Option 2: Using pytest directly
```bash
# Run pytest tests
pytest test_invest_svc_pytest.py -v

# Run with coverage
pytest test_invest_svc_pytest.py --cov=invest_src --cov-report=html

# Run specific test
pytest test_invest_svc_pytest.py::test_health_check -v
```

#### Option 3: Using unittest
```bash
# Run unit tests
python -m unittest test_invest_svc_unit.py -v

# Run integration tests
python test_invest_svc_integration.py
```

## Docker-Based Testing

### Using Docker Compose
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up --build

# Run tests in container
docker-compose -f docker-compose.test.yml run test-runner

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

### Using Docker directly
```bash
# Build test image
docker build -f Dockerfile.test -t invest-svc-test .

# Run tests
docker run --rm invest-svc-test

# Run with environment variables
docker run --rm -e TEST_DB_URI=postgresql://test:test@host.docker.internal:5432/test_invest_db invest-svc-test
```

## Test Configuration

### Environment Variables
- `TEST_DB_URI`: Test database connection string
- `TEST_TIER_AGENT_URL`: Mock tier agent URL
- `PYTHONPATH`: Python path for imports

### Test Database Setup
The integration tests require a PostgreSQL database. You can use:
- Local PostgreSQL instance
- Docker container
- Cloud database (for CI/CD)

### Mock Services
- **user-tier-agent**: Mocked with nginx returning fixed responses
- **Database**: Real PostgreSQL for integration tests

## Test Coverage

### Unit Tests Coverage
- ✅ Service initialization
- ✅ Database connection handling
- ✅ External service calls
- ✅ Portfolio CRUD operations
- ✅ Transaction recording
- ✅ Investment processing logic
- ✅ Error handling
- ✅ Input validation

### Integration Tests Coverage
- ✅ End-to-end investment flow
- ✅ Database operations
- ✅ API endpoint testing
- ✅ Service interaction
- ✅ Data persistence
- ✅ Error scenarios

### Performance Tests Coverage
- ✅ Response time measurement
- ✅ Throughput testing
- ✅ Memory usage monitoring
- ✅ Concurrent operation handling

## Test Data

### Sample Data
- Test user IDs: `test-user-*`
- Test amounts: Various positive values
- Test portfolios: Pre-configured with known values

### Data Cleanup
- Tests automatically clean up after themselves
- Use `test-*` prefixes for easy identification
- Database transactions are rolled back when possible

## Continuous Integration

### GitHub Actions Example
```yaml
name: Test invest-svc
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16.6-alpine
        env:
          POSTGRES_DB: test_invest_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd src/invest-svc/tests
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          cd src/invest-svc/tests
          python run_tests.py --all
        env:
          TEST_DB_URI: postgresql://test:test@localhost:5432/test_invest_db
```

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
echo $TEST_DB_URI
```

#### Import Errors
```bash
# Check Python path
export PYTHONPATH=/path/to/invest-svc/src
```

#### Test Dependencies Missing
```bash
# Install test dependencies
pip install -r requirements-test.txt
```

#### Docker Issues
```bash
# Check Docker status
docker ps

# Check logs
docker-compose -f docker-compose.test.yml logs
```

### Debug Mode
```bash
# Run tests with debug output
python run_tests.py --pytest --coverage -v

# Run specific test with debug
pytest test_invest_svc_pytest.py::test_health_check -v -s
```

## Test Reports

### Coverage Report
- HTML report: `htmlcov/index.html`
- Terminal report: Displayed during test run
- JSON report: `coverage.json`

### Test Results
- JUnit XML: `test-results.xml`
- HTML report: `test_report.html`
- JSON report: `test_report.json`

## Best Practices

### Writing Tests
1. **Test Naming**: Use descriptive test names
2. **Test Isolation**: Each test should be independent
3. **Mocking**: Mock external dependencies
4. **Assertions**: Use specific assertions
5. **Data Cleanup**: Clean up test data

### Test Organization
1. **Group Related Tests**: Use test classes
2. **Use Fixtures**: For common setup/teardown
3. **Parameterized Tests**: For testing multiple inputs
4. **Test Categories**: Unit, integration, performance

### Maintenance
1. **Keep Tests Updated**: Update tests when code changes
2. **Review Test Coverage**: Ensure adequate coverage
3. **Monitor Test Performance**: Keep tests fast
4. **Document Test Cases**: Explain complex test scenarios

## Contributing

### Adding New Tests
1. Follow existing naming conventions
2. Add appropriate docstrings
3. Include both positive and negative test cases
4. Update this README if needed

### Test Review Checklist
- [ ] Tests cover new functionality
- [ ] Tests are properly isolated
- [ ] Mocking is appropriate
- [ ] Error cases are tested
- [ ] Performance impact is considered
- [ ] Documentation is updated

## Support

For questions or issues with testing:
1. Check this README
2. Review test logs
3. Check GitHub issues
4. Contact the development team
