#!/bin/bash

# Copyright 2024 Google LLC
# Queue-DB Schema SQL Testing Script (No Docker Required)

echo "🧪 Queue-DB Schema SQL Testing Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}This script provides SQL commands to test the queue-db schema.${NC}"
echo -e "${BLUE}You can run these commands when you have access to a PostgreSQL database.${NC}"

echo -e "\n${YELLOW}=== SCHEMA TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}1. Database Connection Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"SELECT version();\""

echo -e "\n${GREEN}2. Table Existence Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"\\dt investment_queue\""

echo -e "\n${GREEN}3. Table Structure Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"\\d investment_queue\""

echo -e "\n${GREEN}4. Indexes Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"\\di idx_queue_*\""

echo -e "\n${GREEN}5. Data Count Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"SELECT COUNT(*) FROM investment_queue;\""

echo -e "\n${GREEN}6. Status Distribution Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
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
\""

echo -e "\n${GREEN}7. Sample Data Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT account_number, tier_1, tier_2, tier_3, status, created_at 
FROM investment_queue 
ORDER BY created_at 
LIMIT 10;
\""

echo -e "\n${YELLOW}=== CONSTRAINT TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}8. Status Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440999', 'INVALID_STATUS');
\""

echo -e "\n${GREEN}9. UUID Format Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, 'invalid-uuid', 'PENDING');
\""

echo -e "\n${GREEN}10. Negative Amount Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', -100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440998', 'PENDING');
\""

echo -e "\n${GREEN}11. Unique Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440001', 'PENDING');
\""

echo -e "\n${YELLOW}=== DATA TYPE TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}12. Decimal Precision Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 123.45678901, 987.65432109, 555.12345678, '550e8400-e29b-41d4-a716-446655440997', 'PENDING');
SELECT account_number, tier_1, tier_2, tier_3 FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440997';
\""

echo -e "\n${GREEN}13. Timestamp Functionality Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
UPDATE investment_queue SET status = 'COMPLETED', processed_at = CURRENT_TIMESTAMP WHERE uuid = '550e8400-e29b-41d4-a716-446655440997';
SELECT account_number, status, created_at, updated_at, processed_at FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440997';
\""

echo -e "\n${YELLOW}=== PERFORMANCE TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}14. Account Index Performance Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE account_number = '1011226111';
\""

echo -e "\n${GREEN}15. Status Index Performance Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE status = 'PENDING';
\""

echo -e "\n${YELLOW}=== DATA INTEGRITY TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}16. Data Consistency Check:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
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
\""

echo -e "\n${GREEN}17. Null Value Check:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
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
\""

echo -e "\n${YELLOW}=== CLEANUP COMMANDS ===${NC}"

echo -e "\n${GREEN}18. Cleanup Test Data:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
DELETE FROM investment_queue WHERE uuid LIKE '550e8400-e29b-41d4-a716-44665544099%';
\""

echo -e "\n${GREEN}19. Verify Cleanup:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT COUNT(*) as remaining_test_data 
FROM investment_queue 
WHERE uuid LIKE '550e8400-e29b-41d4-a716-44665544099%';
\""

echo -e "\n${BLUE}=== QUICK TEST SUMMARY ===${NC}"
echo -e "\n${GREEN}To run a quick test, execute:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    'Schema Test' as test_type,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END as result
FROM investment_queue;
\""

echo -e "\n${GREEN}🎉 Queue-DB Schema Testing Commands Ready!${NC}"
echo -e "${BLUE}Copy and paste these commands when you have access to PostgreSQL.${NC}"
