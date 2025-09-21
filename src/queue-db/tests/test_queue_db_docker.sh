#!/bin/bash

# Copyright 2024 Google LLC
# Queue-DB Schema Unit Testing Script

echo "🧪 Starting Queue-DB Schema Unit Tests with Docker"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test results
print_test() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Function to wait for database to be ready
wait_for_db() {
    local max_attempts=30
    local attempt=1
    
    echo -e "\n${YELLOW}Waiting for database to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec queue-db-test pg_isready -U queue-admin -d queue-db >/dev/null 2>&1; then
            echo -e "${GREEN}Database is ready after $attempt attempts${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}Attempt $attempt/$max_attempts - Database not ready yet, waiting...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}Database failed to become ready after $max_attempts attempts${NC}"
    return 1
}

# Function to run SQL test
run_sql_test() {
    local test_name="$1"
    local sql_query="$2"
    local expected_result="$3"
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}"
    echo "SQL: $sql_query"
    
    result=$(docker exec queue-db-test psql -U queue-admin -d queue-db -t -c "$sql_query" 2>/dev/null)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "Result: $result"
        print_test 0 "$test_name"
    else
        echo "Error: $result"
        print_test 1 "$test_name"
    fi
}

# Function to check if container is running
check_container() {
    if ! docker ps | grep -q queue-db-test; then
        echo -e "${RED}Container is not running. Checking logs...${NC}"
        docker logs queue-db-test 2>/dev/null | tail -20
        return 1
    fi
    return 0
}

# Step 1: Cleanup any existing containers
echo -e "\n${YELLOW}Step 1: Cleaning up existing containers${NC}"
docker stop queue-db-test 2>/dev/null
docker rm queue-db-test 2>/dev/null
print_test 0 "Cleanup completed"

# Step 2: Build Docker Image
echo -e "\n${YELLOW}Step 2: Building Docker Image${NC}"
cd "$(dirname "$0")/.."
docker build -t queue-db-test . 2>/dev/null
print_test $? "Docker image built successfully"

# Step 3: Start Container with proper environment
echo -e "\n${YELLOW}Step 3: Starting Container${NC}"
docker run -d \
    --name queue-db-test \
    -e POSTGRES_DB=queue-db \
    -e POSTGRES_USER=queue-admin \
    -e POSTGRES_PASSWORD=queue-pwd \
    -e USE_DEMO_DATA=True \
    -p 5434:5432 \
    queue-db-test 2>/dev/null

if [ $? -eq 0 ]; then
    print_test 0 "Container started successfully"
else
    print_test 1 "Failed to start container"
    exit 1
fi

# Step 4: Wait for database to be ready
if ! wait_for_db; then
    echo -e "${RED}Database initialization failed. Checking logs...${NC}"
    docker logs queue-db-test 2>/dev/null | tail -20
    exit 1
fi

# Step 5: Test Database Connection
echo -e "\n${YELLOW}Step 5: Testing Database Connection${NC}"
if check_container; then
    docker exec queue-db-test pg_isready -U queue-admin -d queue-db 2>/dev/null
    print_test $? "Database connection successful"
else
    print_test 1 "Container not running"
    exit 1
fi

# Step 6: Test Schema
echo -e "\n${YELLOW}Step 6: Testing Database Schema${NC}"

# Test 6.1: Check if investment_queue table exists
run_sql_test "Table Existence" "\dt investment_queue" "investment_queue"

# Test 6.2: Check table structure
echo -e "\n${YELLOW}Table Structure:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "\d investment_queue"

# Test 6.3: Check indexes
echo -e "\n${YELLOW}Indexes:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "\di idx_queue_*"

# Step 7: Test Data Loading
echo -e "\n${YELLOW}Step 7: Testing Data Loading${NC}"

# Test 7.1: Count total queue entries
run_sql_test "Data Count" "SELECT COUNT(*) FROM investment_queue;" ""

# Test 7.2: Check status distribution
echo -e "\n${YELLOW}Status Distribution:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    status,
    COUNT(*) as count,
    CASE 
        WHEN status = 'PENDING' THEN 'Waiting to be processed'
        WHEN status = 'PROCESSING' THEN 'Currently being processed'
        WHEN status = 'COMPLETED' THEN 'Successfully processed'
        WHEN status = 'FAILED' THEN 'Processing failed'
        WHEN status = 'CANCELLED' THEN 'Request cancelled'
    END as description
FROM investment_queue 
GROUP BY status 
ORDER BY status;
"

# Test 7.3: Sample data
echo -e "\n${YELLOW}Sample Data:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT account_number, tier_1, tier_2, tier_3, status, created_at 
FROM investment_queue 
ORDER BY created_at 
LIMIT 10;
"

# Step 8: Test Constraints
echo -e "\n${YELLOW}Step 8: Testing Constraints${NC}"

# Test 8.1: Status constraint (should fail)
echo -e "\n${YELLOW}Testing Status Constraint (should fail):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440999', 'INVALID_STATUS');
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Status constraint working (rejected invalid status)"
else
    print_test 1 "Status constraint failed (accepted invalid status)"
fi

# Test 8.2: UUID format constraint (should fail)
echo -e "\n${YELLOW}Testing UUID Format Constraint (should fail):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, 'invalid-uuid', 'PENDING');
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "UUID format constraint working (rejected invalid UUID)"
else
    print_test 1 "UUID format constraint failed (accepted invalid UUID)"
fi

# Test 8.3: Negative amounts allowed (should succeed)
echo -e "\n${YELLOW}Testing Negative Amounts Allowed (should succeed):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', -100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440998', 'PENDING');
" 2>/dev/null
if [ $? -eq 0 ]; then
    print_test 0 "Negative amounts allowed (accepted negative tier_1 for withdrawals)"
else
    print_test 1 "Negative amounts rejected (should be allowed for withdrawals)"
fi

# Test 8.4: Unique constraint (should fail)
echo -e "\n${YELLOW}Testing Unique Constraint (should fail):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440001', 'PENDING');
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Unique constraint working (rejected duplicate UUID)"
else
    print_test 1 "Unique constraint failed (accepted duplicate UUID)"
fi

# Step 9: Test Data Types and Precision
echo -e "\n${YELLOW}Step 9: Testing Data Types and Precision${NC}"

# Test 9.1: Decimal precision
echo -e "\n${YELLOW}Testing Decimal Precision:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 123.45678901, 987.65432109, 555.12345678, '550e8400-e29b-41d4-a716-446655440997', 'PENDING');
SELECT account_number, tier_1, tier_2, tier_3 FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440997';
"

# Test 9.2: Timestamp functionality
echo -e "\n${YELLOW}Testing Timestamp Functionality:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
UPDATE investment_queue SET status = 'COMPLETED', processed_at = CURRENT_TIMESTAMP WHERE uuid = '550e8400-e29b-41d4-a716-446655440997';
SELECT account_number, status, created_at, updated_at, processed_at FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440997';
"

# Step 10: Test Indexes Performance
echo -e "\n${YELLOW}Step 10: Testing Index Performance${NC}"

# Test 10.1: Account index
echo -e "\n${YELLOW}Account Index Performance:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE account_number = '1011226111';
"

# Test 10.2: Status index
echo -e "\n${YELLOW}Status Index Performance:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE status = 'PENDING';
"

# Step 11: Test Data Integrity
echo -e "\n${YELLOW}Step 11: Testing Data Integrity${NC}"

# Test 11.1: Data consistency
echo -e "\n${YELLOW}Data Consistency Check:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'Total Queue Entries' as metric,
    COUNT(*) as value
FROM investment_queue
UNION ALL
SELECT 
    'Pending Requests' as metric,
    COUNT(*) as value
FROM investment_queue WHERE status = 'PENDING'
UNION ALL
SELECT 
    'Completed Requests' as metric,
    COUNT(*) as value
FROM investment_queue WHERE status = 'COMPLETED'
UNION ALL
SELECT 
    'Failed Requests' as metric,
    COUNT(*) as value
FROM investment_queue WHERE status = 'FAILED';
"

# Test 11.2: Null value check
echo -e "\n${YELLOW}Null Value Check:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'Null Account Numbers' as check_type,
    COUNT(*) as count
FROM investment_queue WHERE account_number IS NULL
UNION ALL
SELECT 
    'Null UUIDs' as check_type,
    COUNT(*) as count
FROM investment_queue WHERE uuid IS NULL
UNION ALL
SELECT 
    'Null Status' as check_type,
    COUNT(*) as count
FROM investment_queue WHERE status IS NULL;
"

# Step 12: Cleanup
echo -e "\n${YELLOW}Step 12: Cleanup${NC}"
docker stop queue-db-test 2>/dev/null
docker rm queue-db-test 2>/dev/null
print_test 0 "Container cleaned up"

echo -e "\n${GREEN}🎉 Queue-DB Schema Unit Tests Complete!${NC}"
echo "=================================================="
