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
echo "psql -U queue-admin -d queue-db -c \"\\dt withdrawal_queue\""

echo -e "\n${GREEN}3. Table Structure Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"\\d investment_queue\""
echo "psql -U queue-admin -d queue-db -c \"\\d withdrawal_queue\""

echo -e "\n${GREEN}4. Indexes Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"\\di idx_investment_queue_*\""
echo "psql -U queue-admin -d queue-db -c \"\\di idx_withdrawal_queue_*\""

echo -e "\n${GREEN}5. Data Count Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"SELECT COUNT(*) FROM investment_queue;\""
echo "psql -U queue-admin -d queue-db -c \"SELECT COUNT(*) FROM withdrawal_queue;\""

echo -e "\n${GREEN}6. UUID Consistency Functions Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"SELECT generate_queue_uuid() as generated_uuid;\""
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    '550e8400-e29b-41d4-a716-446655440001' as test_uuid,
    validate_uuid_consistency('550e8400-e29b-41d4-a716-446655440001', 'INVESTMENT') as investment_valid,
    validate_uuid_consistency('550e8400-e29b-41d4-a716-446655440001', 'WITHDRAWAL') as withdrawal_valid;
\""

echo -e "\n${GREEN}7. Status Distribution Test (Both Tables):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    'investment' as queue_type,
    status,
    COUNT(*) as count
FROM investment_queue 
GROUP BY status 
ORDER BY status;
\""
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    'withdrawal' as queue_type,
    status,
    COUNT(*) as count
FROM withdrawal_queue 
GROUP BY status 
ORDER BY status;
\""

echo -e "\n${GREEN}8. Sample Data Test (Both Tables):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT 'investment' as table_type, account_number, tier_1, tier_2, tier_3, status, created_at 
FROM investment_queue 
ORDER BY created_at 
LIMIT 5;
\""
echo "psql -U queue-admin -d queue-db -c \"
SELECT 'withdrawal' as table_type, account_number, tier_1, tier_2, tier_3, status, created_at 
FROM withdrawal_queue 
ORDER BY created_at 
LIMIT 5;
\""

echo -e "\n${YELLOW}=== CONSTRAINT TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}9. Investment Status Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440999', 'INVALID_STATUS');
\""

echo -e "\n${GREEN}10. Withdrawal Status Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440998', 'INVALID_STATUS');
\""

echo -e "\n${GREEN}11. UUID Format Constraint Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, 'invalid-uuid', 'PENDING');
\""

echo -e "\n${GREEN}12. Positive Amount Constraint Test (should succeed):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440997', 'PENDING');
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 50.0, 100.0, 150.0, '550e8400-e29b-41d4-a716-446655440996', 'PENDING');
\""

echo -e "\n${GREEN}13. Cross-Table UUID Uniqueness Test (should succeed):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 100.0, 200.0, 300.0, '550e8400-e29b-41d4-a716-446655440995', 'PENDING');
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 50.0, 100.0, 150.0, '550e8400-e29b-41d4-a716-446655440994', 'PENDING');
\""

echo -e "\n${GREEN}14. Same UUID Across Tables Test (should fail):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 50.0, 100.0, 150.0, '550e8400-e29b-41d4-a716-446655440995', 'PENDING');
\""

echo -e "\n${YELLOW}=== DATA TYPE TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}15. Decimal Precision Test (Both Tables):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
INSERT INTO investment_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 123.45678901, 987.65432109, 555.12345678, '550e8400-e29b-41d4-a716-446655440993', 'PENDING');
INSERT INTO withdrawal_queue (account_number, tier_1, tier_2, tier_3, uuid, status) 
VALUES ('1234567890', 12.34567890, 98.76543210, 55.12345678, '550e8400-e29b-41d4-a716-446655440992', 'PENDING');
SELECT 'investment' as table_type, account_number, tier_1, tier_2, tier_3 FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440993'
UNION ALL
SELECT 'withdrawal' as table_type, account_number, tier_1, tier_2, tier_3 FROM withdrawal_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440992';
\""

echo -e "\n${GREEN}16. Timestamp Functionality Test (Both Tables):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
UPDATE investment_queue SET status = 'COMPLETED', processed_at = CURRENT_TIMESTAMP WHERE uuid = '550e8400-e29b-41d4-a716-446655440993';
UPDATE withdrawal_queue SET status = 'COMPLETED', processed_at = CURRENT_TIMESTAMP WHERE uuid = '550e8400-e29b-41d4-a716-446655440992';
SELECT 'investment' as table_type, account_number, status, created_at, updated_at, processed_at FROM investment_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440993'
UNION ALL
SELECT 'withdrawal' as table_type, account_number, status, created_at, updated_at, processed_at FROM withdrawal_queue WHERE uuid = '550e8400-e29b-41d4-a716-446655440992';
\""

echo -e "\n${YELLOW}=== PERFORMANCE TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}17. Investment Queue Account Index Performance Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE account_number = '1011226111';
\""

echo -e "\n${GREEN}18. Withdrawal Queue Account Index Performance Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM withdrawal_queue WHERE account_number = '1011226114';
\""

echo -e "\n${GREEN}19. Investment Queue Status Index Performance Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM investment_queue WHERE status = 'PENDING';
\""

echo -e "\n${GREEN}20. Withdrawal Queue Status Index Performance Test:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM withdrawal_queue WHERE status = 'PENDING';
\""

echo -e "\n${YELLOW}=== DATA INTEGRITY TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}21. Combined Data Consistency Check:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
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
\""

echo -e "\n${GREEN}22. UUID Uniqueness Across Tables Check:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    'Duplicate UUIDs' as check_type,
    COUNT(*) as count
FROM (
    SELECT uuid FROM investment_queue
    INTERSECT
    SELECT uuid FROM withdrawal_queue
) as duplicates;
\""

echo -e "\n${GREEN}23. Null Value Check (Both Tables):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
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
\""

echo -e "\n${YELLOW}=== CLEANUP COMMANDS ===${NC}"

echo -e "\n${GREEN}24. Cleanup Test Data (Both Tables):${NC}"
echo "psql -U queue-admin -d queue-db -c \"
DELETE FROM investment_queue WHERE uuid LIKE '550e8400-e29b-41d4-a716-44665544099%';
DELETE FROM withdrawal_queue WHERE uuid LIKE '550e8400-e29b-41d4-a716-44665544099%';
\""

echo -e "\n${GREEN}25. Verify Cleanup:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    'Investment Test Data Remaining' as check_type,
    COUNT(*) as count
FROM investment_queue 
WHERE uuid LIKE '550e8400-e29b-41d4-a716-44665544099%'
UNION ALL
SELECT 
    'Withdrawal Test Data Remaining' as check_type,
    COUNT(*) as count
FROM withdrawal_queue 
WHERE uuid LIKE '550e8400-e29b-41d4-a716-44665544099%';
\""

echo -e "\n${BLUE}=== QUICK TEST SUMMARY ===${NC}"
echo -e "\n${GREEN}To run a quick test, execute:${NC}"
echo "psql -U queue-admin -d queue-db -c \"
SELECT 
    'Investment Queue Test' as test_type,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END as result
FROM investment_queue
UNION ALL
SELECT 
    'Withdrawal Queue Test' as test_type,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END as result
FROM withdrawal_queue;
\""

echo -e "\n${BLUE}=== COMPREHENSIVE TEST SUMMARY ===${NC}"
echo -e "\n${GREEN}✅ Investment Queue Table: Ready for testing${NC}"
echo -e "${GREEN}✅ Withdrawal Queue Table: Ready for testing${NC}"
echo -e "${GREEN}✅ UUID Consistency Functions: Ready for testing${NC}"
echo -e "${GREEN}✅ Cross-Table Constraints: Ready for testing${NC}"
echo -e "${GREEN}✅ Index Performance: Ready for testing${NC}"
echo -e "${GREEN}✅ Data Integrity: Ready for testing${NC}"

echo -e "\n${BLUE}=== KEY FEATURES TO VALIDATE ===${NC}"
echo -e "${GREEN}• Separate investment and withdrawal queues${NC}"
echo -e "${GREEN}• UUID consistency across both tables${NC}"
echo -e "${GREEN}• Proper constraint validation${NC}"
echo -e "${GREEN}• Index performance optimization${NC}"
echo -e "${GREEN}• Data integrity and consistency${NC}"

echo -e "\n${GREEN}🎉 Queue-DB Comprehensive Testing Commands Ready!${NC}"
echo -e "${BLUE}Copy and paste these commands when you have access to PostgreSQL.${NC}"
