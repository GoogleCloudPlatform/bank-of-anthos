#!/bin/bash

# Copyright 2024 Google LLC
# Assets-DB Schema Unit Testing Script

echo "🧪 Starting Assets-DB Schema Unit Tests with Docker"
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
        if docker exec assets-db-test pg_isready -U assets-admin -d assets-db >/dev/null 2>&1; then
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
    
    result=$(docker exec assets-db-test psql -U assets-admin -d assets-db -t -c "$sql_query" 2>/dev/null)
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
    if ! docker ps | grep -q assets-db-test; then
        echo -e "${RED}Container is not running. Checking logs...${NC}"
        docker logs assets-db-test 2>/dev/null | tail -20
        return 1
    fi
    return 0
}

# Step 1: Cleanup any existing containers
echo -e "\n${YELLOW}Step 1: Cleaning up existing containers${NC}"
docker stop assets-db-test 2>/dev/null
docker rm assets-db-test 2>/dev/null
print_test 0 "Cleanup completed"

# Step 2: Build Docker Image
echo -e "\n${YELLOW}Step 2: Building Docker Image${NC}"
cd src/assets-db
docker build -t assets-db-test . 2>/dev/null
print_test $? "Docker image built successfully"

# Step 3: Start Container with proper environment
echo -e "\n${YELLOW}Step 3: Starting Container${NC}"
docker run -d \
    --name assets-db-test \
    -e POSTGRES_DB=assets-db \
    -e POSTGRES_USER=assets-admin \
    -e POSTGRES_PASSWORD=assets-pwd \
    -e USE_DEMO_DATA=True \
    -p 5433:5432 \
    assets-db-test 2>/dev/null

if [ $? -eq 0 ]; then
    print_test 0 "Container started successfully"
else
    print_test 1 "Failed to start container"
    exit 1
fi

# Step 4: Wait for database to be ready
if ! wait_for_db; then
    echo -e "${RED}Database initialization failed. Checking logs...${NC}"
    docker logs assets-db-test 2>/dev/null | tail -20
    exit 1
fi

# Step 5: Test Database Connection
echo -e "\n${YELLOW}Step 5: Testing Database Connection${NC}"
if check_container; then
    docker exec assets-db-test pg_isready -U assets-admin -d assets-db 2>/dev/null
    print_test $? "Database connection successful"
else
    print_test 1 "Container not running"
    exit 1
fi

# Step 6: Test Schema
echo -e "\n${YELLOW}Step 6: Testing Database Schema${NC}"

# Test 4.1: Check if assets table exists
run_sql_test "Table Existence" "\dt assets" "assets"

# Test 4.2: Check table structure
echo -e "\n${YELLOW}Table Structure:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "\d assets"

# Test 4.3: Check indexes
echo -e "\n${YELLOW}Indexes:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "\di idx_assets_*"

# Step 5: Test Data Loading
echo -e "\n${YELLOW}Step 5: Testing Data Loading${NC}"

# Test 5.1: Count total assets
run_sql_test "Data Count" "SELECT COUNT(*) FROM assets;" ""

# Test 5.2: Check tier distribution
echo -e "\n${YELLOW}Tier Distribution:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
SELECT 
    tier_number,
    COUNT(*) as asset_count,
    CASE 
        WHEN tier_number = 1 THEN 'Cryptocurrencies'
        WHEN tier_number = 2 THEN 'ETFs/Stocks'
        WHEN tier_number = 3 THEN 'Alternative Investments'
    END as description
FROM assets 
GROUP BY tier_number 
ORDER BY tier_number;
"

# Test 5.3: Sample data
echo -e "\n${YELLOW}Sample Data:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
SELECT asset_name, tier_number, price_per_unit, amount 
FROM assets 
ORDER BY tier_number, asset_name 
LIMIT 10;
"

# Step 6: Test Constraints
echo -e "\n${YELLOW}Step 6: Testing Constraints${NC}"

# Test 6.1: Tier constraint (should fail)
echo -e "\n${YELLOW}Testing Tier Constraint (should fail):${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (4, 'INVALID_TIER', 100.0, 50.0);
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Tier constraint working (rejected invalid tier 4)"
else
    print_test 1 "Tier constraint failed (accepted invalid tier 4)"
fi

# Test 6.2: Amount constraint (should fail)
echo -e "\n${YELLOW}Testing Amount Constraint (should fail):${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'NEGATIVE_AMOUNT', -100.0, 50.0);
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Amount constraint working (rejected negative amount)"
else
    print_test 1 "Amount constraint failed (accepted negative amount)"
fi

# Test 6.3: Price constraint (should fail)
echo -e "\n${YELLOW}Testing Price Constraint (should fail):${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'ZERO_PRICE', 100.0, 0.0);
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Price constraint working (rejected zero price)"
else
    print_test 1 "Price constraint failed (accepted zero price)"
fi

# Test 6.4: Unique constraint (should fail)
echo -e "\n${YELLOW}Testing Unique Constraint (should fail):${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'BTC', 100.0, 50000.0);
" 2>/dev/null
if [ $? -ne 0 ]; then
    print_test 0 "Unique constraint working (rejected duplicate BTC)"
else
    print_test 1 "Unique constraint failed (accepted duplicate BTC)"
fi

# Step 7: Test Data Types and Precision
echo -e "\n${YELLOW}Step 7: Testing Data Types and Precision${NC}"

# Test 7.1: Decimal precision
echo -e "\n${YELLOW}Testing Decimal Precision:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'PRECISION_TEST', 123.45678901, 987.65);
SELECT asset_name, amount, price_per_unit FROM assets WHERE asset_name = 'PRECISION_TEST';
"

# Test 7.2: Timestamp functionality
echo -e "\n${YELLOW}Testing Timestamp Functionality:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
UPDATE assets SET price_per_unit = 46000.00 WHERE asset_name = 'BTC';
SELECT asset_name, price_per_unit, last_updated FROM assets WHERE asset_name = 'BTC';
"

# Step 8: Test Indexes Performance
echo -e "\n${YELLOW}Step 8: Testing Index Performance${NC}"

# Test 8.1: Tier index
echo -e "\n${YELLOW}Tier Index Performance:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM assets WHERE tier_number = 1;
"

# Test 8.2: Asset name index
echo -e "\n${YELLOW}Asset Name Index Performance:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM assets WHERE asset_name = 'BTC';
"

# Step 9: Test Data Integrity
echo -e "\n${YELLOW}Step 9: Testing Data Integrity${NC}"

# Test 9.1: Data consistency
echo -e "\n${YELLOW}Data Consistency Check:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
SELECT 
    'Total Assets' as metric,
    COUNT(*) as value
FROM assets
UNION ALL
SELECT 
    'Tier 1 Assets' as metric,
    COUNT(*) as value
FROM assets WHERE tier_number = 1
UNION ALL
SELECT 
    'Tier 2 Assets' as metric,
    COUNT(*) as value
FROM assets WHERE tier_number = 2
UNION ALL
SELECT 
    'Tier 3 Assets' as metric,
    COUNT(*) as value
FROM assets WHERE tier_number = 3;
"

# Test 9.2: Null value check
echo -e "\n${YELLOW}Null Value Check:${NC}"
docker exec assets-db-test psql -U assets-admin -d assets-db -c "
SELECT 
    'Null Asset Names' as check_type,
    COUNT(*) as count
FROM assets WHERE asset_name IS NULL
UNION ALL
SELECT 
    'Null Tier Numbers' as check_type,
    COUNT(*) as count
FROM assets WHERE tier_number IS NULL
UNION ALL
SELECT 
    'Null Amounts' as check_type,
    COUNT(*) as count
FROM assets WHERE amount IS NULL
UNION ALL
SELECT 
    'Null Prices' as check_type,
    COUNT(*) as count
FROM assets WHERE price_per_unit IS NULL;
"

# Step 10: Cleanup
echo -e "\n${YELLOW}Step 10: Cleanup${NC}"
docker stop assets-db-test 2>/dev/null
docker rm assets-db-test 2>/dev/null
print_test 0 "Container cleaned up"

echo -e "\n${GREEN}🎉 Assets-DB Schema Unit Tests Complete!${NC}"
echo "=================================================="
