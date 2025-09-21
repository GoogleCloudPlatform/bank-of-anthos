#!/bin/bash

# Copyright 2024 Google LLC
# Assets-DB Schema SQL Testing Script (No Docker Required)

echo "🧪 Assets-DB Schema SQL Testing Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}This script provides SQL commands to test the assets-db schema.${NC}"
echo -e "${BLUE}You can run these commands when you have access to a PostgreSQL database.${NC}"

echo -e "\n${YELLOW}=== SCHEMA TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}1. Database Connection Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"SELECT version();\""

echo -e "\n${GREEN}2. Table Existence Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"\\dt assets\""

echo -e "\n${GREEN}3. Table Structure Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"\\d assets\""

echo -e "\n${GREEN}4. Indexes Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"\\di idx_assets_*\""

echo -e "\n${GREEN}5. Data Count Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"SELECT COUNT(*) FROM assets;\""

echo -e "\n${GREEN}6. Tier Distribution Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
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
\""

echo -e "\n${GREEN}7. Sample Data Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
SELECT asset_name, tier_number, price_per_unit, amount 
FROM assets 
ORDER BY tier_number, asset_name 
LIMIT 10;
\""

echo -e "\n${YELLOW}=== CONSTRAINT TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}8. Tier Constraint Test (should fail):${NC}"
echo "psql -U assets-admin -d assets-db -c \"
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (4, 'INVALID_TIER', 100.0, 50.0);
\""

echo -e "\n${GREEN}9. Amount Constraint Test (should fail):${NC}"
echo "psql -U assets-admin -d assets-db -c \"
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'NEGATIVE_AMOUNT', -100.0, 50.0);
\""

echo -e "\n${GREEN}10. Price Constraint Test (should fail):${NC}"
echo "psql -U assets-admin -d assets-db -c \"
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'ZERO_PRICE', 100.0, 0.0);
\""

echo -e "\n${GREEN}11. Unique Constraint Test (should fail):${NC}"
echo "psql -U assets-admin -d assets-db -c \"
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'BTC', 100.0, 50000.0);
\""

echo -e "\n${YELLOW}=== DATA TYPE TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}12. Decimal Precision Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'PRECISION_TEST', 123.45678901, 987.65);
SELECT asset_name, amount, price_per_unit FROM assets WHERE asset_name = 'PRECISION_TEST';
\""

echo -e "\n${GREEN}13. Timestamp Functionality Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
UPDATE assets SET price_per_unit = 46000.00 WHERE asset_name = 'BTC';
SELECT asset_name, price_per_unit, last_updated FROM assets WHERE asset_name = 'BTC';
\""

echo -e "\n${YELLOW}=== PERFORMANCE TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}14. Tier Index Performance Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM assets WHERE tier_number = 1;
\""

echo -e "\n${GREEN}15. Asset Name Index Performance Test:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM assets WHERE asset_name = 'BTC';
\""

echo -e "\n${YELLOW}=== DATA INTEGRITY TESTING COMMANDS ===${NC}"

echo -e "\n${GREEN}16. Data Consistency Check:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
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
\""

echo -e "\n${GREEN}17. Null Value Check:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
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
\""

echo -e "\n${YELLOW}=== CLEANUP COMMANDS ===${NC}"

echo -e "\n${GREEN}18. Cleanup Test Data:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
DELETE FROM assets WHERE asset_name LIKE 'TEST_%' OR asset_name = 'PRECISION_TEST';
\""

echo -e "\n${GREEN}19. Verify Cleanup:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
SELECT COUNT(*) as remaining_test_data 
FROM assets 
WHERE asset_name LIKE 'TEST_%' OR asset_name = 'PRECISION_TEST';
\""

echo -e "\n${BLUE}=== QUICK TEST SUMMARY ===${NC}"
echo -e "\n${GREEN}To run a quick test, execute:${NC}"
echo "psql -U assets-admin -d assets-db -c \"
SELECT 
    'Schema Test' as test_type,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END as result
FROM assets;
\""

echo -e "\n${GREEN}🎉 Assets-DB Schema Testing Commands Ready!${NC}"
echo -e "${BLUE}Copy and paste these commands when you have access to PostgreSQL.${NC}"
