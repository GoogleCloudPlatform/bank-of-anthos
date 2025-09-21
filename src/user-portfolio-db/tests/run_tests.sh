#!/bin/bash
# Test runner script for User Portfolio Database

set -e

echo "=========================================="
echo "User Portfolio Database Unit Tests"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Function to run individual test
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo -e "\n${YELLOW}Running $test_name...${NC}"
    
    if psql -h localhost -p 5432 -U test_admin -d test_user_portfolio_db -f "$test_file" > /dev/null 2>&1; then
        print_status 0 "$test_name"
        return 0
    else
        print_status 1 "$test_name"
        return 1
    fi
}

# Check if PostgreSQL is running
echo "Checking database connection..."
if ! pg_isready -h localhost -p 5432 -U test_admin > /dev/null 2>&1; then
    echo -e "${RED}Database is not running. Please start the test database first.${NC}"
    echo "Run: docker-compose -f docker-compose.test.yml up -d"
    exit 1
fi

# Run tests
echo -e "\n${YELLOW}Starting test execution...${NC}"

failed_tests=0
total_tests=0

# Test 1: Schema Validation
total_tests=$((total_tests + 1))
if ! run_test "01_schema_validation.sql" "Schema Validation"; then
    failed_tests=$((failed_tests + 1))
fi

# Test 2: Constraint Tests
total_tests=$((total_tests + 1))
if ! run_test "02_constraint_tests.sql" "Constraint Tests"; then
    failed_tests=$((failed_tests + 1))
fi

# Test 3: Functionality Tests
total_tests=$((total_tests + 1))
if ! run_test "03_functionality_tests.sql" "Functionality Tests"; then
    failed_tests=$((failed_tests + 1))
fi

# Test 4: Performance Tests
total_tests=$((total_tests + 1))
if ! run_test "04_performance_tests.sql" "Performance Tests"; then
    failed_tests=$((failed_tests + 1))
fi

# Summary
echo -e "\n=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: $total_tests"
echo "Passed: $((total_tests - failed_tests))"
echo "Failed: $failed_tests"

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}All tests passed! 🎉${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
fi
