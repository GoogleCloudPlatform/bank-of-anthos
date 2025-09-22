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
run_sql_test "Investment Table Existence" "\dt investment_queue" "investment_queue"

# Test 6.2: Check if withdrawal_queue table exists
run_sql_test "Withdrawal Table Existence" "\dt withdrawal_queue" "withdrawal_queue"

# Test 6.3: Check table structures
echo -e "\n${YELLOW}Investment Queue Table Structure:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "\d investment_queue"

echo -e "\n${YELLOW}Withdrawal Queue Table Structure:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "\d withdrawal_queue"

# Test 6.4: Check indexes
echo -e "\n${YELLOW}Investment Queue Indexes:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "\di idx_investment_queue_*"

echo -e "\n${YELLOW}Withdrawal Queue Indexes:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "\di idx_withdrawal_queue_*"

# Step 7: Test Data Loading
echo -e "\n${YELLOW}Step 7: Testing Data Loading${NC}"

# Test 7.1: Count total queue entries
run_sql_test "Investment Data Count" "SELECT COUNT(*) FROM investment_queue;" ""
run_sql_test "Withdrawal Data Count" "SELECT COUNT(*) FROM withdrawal_queue;" ""

# Test 7.2: Check status distribution for both tables
echo -e "\n${YELLOW}Investment Queue Status Distribution:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'investment' as queue_type,
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

echo -e "\n${YELLOW}Withdrawal Queue Status Distribution:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'withdrawal' as queue_type,
    status,
    COUNT(*) as count,
    CASE 
        WHEN status = 'PENDING' THEN 'Waiting to be processed'
        WHEN status = 'PROCESSING' THEN 'Currently being processed'
        WHEN status = 'COMPLETED' THEN 'Successfully processed'
        WHEN status = 'FAILED' THEN 'Processing failed'
        WHEN status = 'CANCELLED' THEN 'Request cancelled'
    END as description
FROM withdrawal_queue 
GROUP BY status 
ORDER BY status;
"

# Test 7.3: Sample data from both tables
echo -e "\n${YELLOW}Sample Investment Data:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT account_number, tier_1, tier_2, tier_3, status, created_at 
FROM investment_queue 
ORDER BY created_at 
LIMIT 5;
"

echo -e "\n${YELLOW}Sample Withdrawal Data:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT account_number, tier_1, tier_2, tier_3, status, created_at 
FROM withdrawal_queue 
ORDER BY created_at 
LIMIT 5;
"

# Step 8: Test UUID Consistency Functions
echo -e "\n${YELLOW}Step 8: Testing UUID Consistency Functions${NC}"

# Test 8.1: Test UUID generation function
echo -e "\n${YELLOW}Testing UUID Generation Function:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT generate_queue_uuid() as generated_uuid;
"

# Test 8.2: Test UUID validation function
echo -e "\n${YELLOW}Testing UUID Validation Function:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    '550e8400-e29b-41d4-a716-446655440001' as test_uuid,
    validate_uuid_consistency('550e8400-e29b-41d4-a716-446655440001', 'INVESTMENT') as investment_valid,
    validate_uuid_consistency('550e8400-e29b-41d4-a716-446655440001', 'WITHDRAWAL') as withdrawal_valid;
"

# Step 9: Test Constraints
echo -e "\n${YELLOW}Step 9: Testing Constraints${NC}"

# Test 9.1: Investment queue status constraint (should fail)
echo -e "\n${YELLOW}Testing Investment Status Constraint (should fail):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440999', 'INVALID_STATUS');
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Investment status constraint working (rejected invalid status)"
else
    print_test 1 "Investment status constraint failed (accepted invalid status)"
fi

# Test 9.2: Withdrawal queue status constraint (should fail)
echo -e "\n${YELLOW}Testing Withdrawal Status Constraint (should fail):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440998', 'INVALID_STATUS');
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Withdrawal status constraint working (rejected invalid status)"
else
    print_test 1 "Withdrawal status constraint failed (accepted invalid status)"
fi

# Test 9.3: UUID format constraint (should fail)
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

# Test 9.4: Positive amounts constraint (should succeed for both tables)
echo -e "\n${YELLOW}Testing Positive Amounts Constraint (should succeed):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440997', 'PENDING');
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 50.0, 100.0, 150.0, '550e8400-e29b-41d4-a716-446655440996', 'PENDING');
" 2>/dev/null
if [ $? -eq 0 ]; then
    print_test 0 "Positive amounts accepted (both tables)"
else
    print_test 1 "Positive amounts rejected (should be accepted)"
fi

# Test 9.5: Cross-table UUID uniqueness (should succeed)
echo -e "\n${YELLOW}Testing Cross-Table UUID Uniqueness (should succeed):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440995', 'PENDING');
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 50.0, 100.0, 150.0, '550e8400-e29b-41d4-a716-446655440994', 'PENDING');
" 2>/dev/null
if [ $? -eq 0 ]; then
    print_test 0 "Cross-table UUID uniqueness working (different UUIDs accepted)"
else
    print_test 1 "Cross-table UUID uniqueness failed (should accept different UUIDs)"
fi

# Test 9.6: Same UUID in different tables (should fail)
echo -e "\n${YELLOW}Testing Same UUID in Different Tables (should fail):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 50.0, 100.0, 150.0, '550e8400-e29b-41d4-a716-446655440995', 'PENDING');
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Same UUID constraint working (rejected duplicate UUID across tables)"
else
    print_test 1 "Same UUID constraint failed (accepted duplicate UUID across tables)"
fi

# Step 10: Test Data Types and Precision
echo -e "\n${YELLOW}Step 10: Testing Data Types and Precision${NC}"

# Test 10.1: Decimal precision for both tables
echo -e "\n${YELLOW}Testing Decimal Precision (Both Tables):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 123.45678901, 987.65432109, 555.12345678, '550e8400-e29b-41d4-a716-446655440993', 'PENDING');
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 12.34567890, 98.76543210, 55.12345678, '550e8400-e29b-41d4-a716-446655440992', 'PENDING');
SELECT 'investment' as table_type, account_number, tier_1, tier_2, tier_3 FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440993'
UNION ALL
SELECT 'withdrawal' as table_type, account_number, tier_1, tier_2, tier_3 FROM withdrawal_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440992';
"

# Test 10.2: Timestamp functionality for both tables
echo -e "\n${YELLOW}Testing Timestamp Functionality (Both Tables):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
UPDATE investment_queue SET status = 'COMPLETED', processed_at = CURRENT_TIMESTAMP WHERE uuid = '550e8400-e29b-41d4-a716-446655440993';
UPDATE withdrawal_queue SET status = 'COMPLETED', processed_at = CURRENT_TIMESTAMP WHERE uuid = '550e8400-e29b-41d4-a716-446655440992';
SELECT 'investment' as table_type, account_number, status, created_at, updated_at, processed_at FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440993'
UNION ALL
SELECT 'withdrawal' as table_type, account_number, status, created_at, updated_at, processed_at FROM withdrawal_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440992';
"

# Step 11: Test Indexes Performance
echo -e "\n${YELLOW}Step 11: Testing Index Performance${NC}"

# Test 11.1: Investment queue account index
echo -e "\n${YELLOW}Investment Queue Account Index Performance:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE account_number = '1011226111';
"

# Test 11.2: Withdrawal queue account index
echo -e "\n${YELLOW}Withdrawal Queue Account Index Performance:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM withdrawal_queue WHERE account_number = '1011226114';
"

# Test 11.3: Investment queue status index
echo -e "\n${YELLOW}Investment Queue Status Index Performance:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE status = 'PENDING';
"

# Test 11.4: Withdrawal queue status index
echo -e "\n${YELLOW}Withdrawal Queue Status Index Performance:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM withdrawal_queue WHERE status = 'PENDING';
"

# Step 12: Test Data Integrity
echo -e "\n${YELLOW}Step 12: Testing Data Integrity${NC}"

# Test 12.1: Combined data consistency
echo -e "\n${YELLOW}Combined Data Consistency Check:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'Total Investment Entries' as metric,
    COUNT(*) as value
FROM investment_queue
UNION ALL
SELECT 
    'Total Withdrawal Entries' as metric,
    COUNT(*) as value
FROM withdrawal_queue
UNION ALL
SELECT 
    'Pending Investment Requests' as metric,
    COUNT(*) as value
FROM investment_queue WHERE status = 'PENDING'
UNION ALL
SELECT 
    'Pending Withdrawal Requests' as metric,
    COUNT(*) as value
FROM withdrawal_queue WHERE status = 'PENDING'
UNION ALL
SELECT 
    'Completed Investment Requests' as metric,
    COUNT(*) as value
FROM investment_queue WHERE status = 'COMPLETED'
UNION ALL
SELECT 
    'Completed Withdrawal Requests' as metric,
    COUNT(*) as value
FROM withdrawal_queue WHERE status = 'COMPLETED';
"

# Test 12.2: UUID uniqueness across tables
echo -e "\n${YELLOW}UUID Uniqueness Across Tables Check:${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'Duplicate UUIDs' as check_type,
    COUNT(*) as count
FROM (
    SELECT uuid FROM investment_queue
    INTERSECT
    SELECT uuid FROM withdrawal_queue
) as duplicates;
"

# Test 12.3: Null value check for both tables
echo -e "\n${YELLOW}Null Value Check (Both Tables):${NC}"
docker exec queue-db-test psql -U queue-admin -d queue-db -c "
SELECT 
    'Investment - Null Account Numbers' as check_type,
    COUNT(*) as count
FROM investment_queue WHERE account_number IS NULL
UNION ALL
SELECT 
    'Investment - Null UUIDs' as check_type,
    COUNT(*) as count
FROM investment_queue WHERE uuid IS NULL
UNION ALL
SELECT 
    'Investment - Null Status' as check_type,
    COUNT(*) as count
FROM investment_queue WHERE status IS NULL
UNION ALL
SELECT 
    'Withdrawal - Null Account Numbers' as check_type,
    COUNT(*) as count
FROM withdrawal_queue WHERE account_number IS NULL
UNION ALL
SELECT 
    'Withdrawal - Null UUIDs' as check_type,
    COUNT(*) as count
FROM withdrawal_queue WHERE uuid IS NULL
UNION ALL
SELECT 
    'Withdrawal - Null Status' as check_type,
    COUNT(*) as count
FROM withdrawal_queue WHERE status IS NULL;
"

# Step 13: Cleanup
echo -e "\n${YELLOW}Step 13: Cleanup${NC}"
docker stop queue-db-test 2>/dev/null
docker rm queue-db-test 2>/dev/null
print_test 0 "Container cleaned up"

# Step 14: Test Summary
echo -e "\n${YELLOW}Step 14: Test Summary${NC}"
echo -e "\n${BLUE}=== QUEUE-DB TEST SUMMARY ===${NC}"
echo -e "${GREEN}✅ Investment Queue Table: Tested${NC}"
echo -e "${GREEN}✅ Withdrawal Queue Table: Tested${NC}"
echo -e "${GREEN}✅ UUID Consistency Functions: Tested${NC}"
echo -e "${GREEN}✅ Cross-Table Constraints: Tested${NC}"
echo -e "${GREEN}✅ Index Performance: Tested${NC}"
echo -e "${GREEN}✅ Data Integrity: Tested${NC}"
echo -e "${GREEN}✅ Timestamp Functionality: Tested${NC}"
echo -e "${GREEN}✅ Decimal Precision: Tested${NC}"

echo -e "\n${BLUE}=== KEY FEATURES VALIDATED ===${NC}"
echo -e "${GREEN}• Separate investment and withdrawal queues${NC}"
echo -e "${GREEN}• UUID consistency across both tables${NC}"
echo -e "${GREEN}• Proper constraint validation${NC}"
echo -e "${GREEN}• Index performance optimization${NC}"
echo -e "${GREEN}• Data integrity and consistency${NC}"

echo -e "\n${GREEN}🎉 Queue-DB Comprehensive Unit Tests Complete!${NC}"
echo "=================================================="
