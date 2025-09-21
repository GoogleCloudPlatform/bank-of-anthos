-- Copyright 2024 Google LLC
-- Assets-DB Schema Validation Script
-- Run this script to validate the assets-db schema

-- ==============================================
-- SCHEMA VALIDATION TESTS
-- ==============================================

-- Test 1: Check if assets table exists
SELECT 
    'Table Existence' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'assets' AND table_schema = 'public'
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 2: Check table structure
SELECT 
    'Table Structure' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assets' 
        AND column_name IN ('asset_id', 'tier_number', 'asset_name', 'amount', 'price_per_unit', 'last_updated')
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 3: Check primary key constraint
SELECT 
    'Primary Key' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'assets' 
        AND constraint_type = 'PRIMARY KEY'
        AND constraint_name LIKE '%asset_id%'
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 4: Check unique constraint on asset_name
SELECT 
    'Unique Constraint' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'assets' 
        AND constraint_type = 'UNIQUE'
        AND constraint_name LIKE '%asset_name%'
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 5: Check check constraints
SELECT 
    'Check Constraints' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name LIKE '%tier_number%'
        OR constraint_name LIKE '%amount%'
        OR constraint_name LIKE '%price_per_unit%'
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 6: Check indexes
SELECT 
    'Indexes' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'assets' 
        AND indexname LIKE 'idx_assets_%'
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 7: Check data types
SELECT 
    'Data Types' as test_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'assets' 
        AND column_name = 'asset_id' 
        AND data_type = 'integer'
        AND column_name = 'tier_number' 
        AND data_type = 'integer'
        AND column_name = 'asset_name' 
        AND data_type = 'character varying'
        AND column_name = 'amount' 
        AND data_type = 'numeric'
        AND column_name = 'price_per_unit' 
        AND data_type = 'numeric'
    ) THEN 'PASS' ELSE 'FAIL' END as result;

-- ==============================================
-- DATA VALIDATION TESTS
-- ==============================================

-- Test 8: Check if data exists
SELECT 
    'Data Exists' as test_name,
    CASE WHEN (SELECT COUNT(*) FROM assets) > 0 THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 9: Check tier distribution
SELECT 
    'Tier Distribution' as test_name,
    CASE WHEN (
        SELECT COUNT(DISTINCT tier_number) FROM assets
    ) = 3 THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 10: Check for null values
SELECT 
    'No Null Values' as test_name,
    CASE WHEN (
        SELECT COUNT(*) FROM assets 
        WHERE asset_name IS NULL 
        OR tier_number IS NULL 
        OR amount IS NULL 
        OR price_per_unit IS NULL
    ) = 0 THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 11: Check tier values are valid (1, 2, 3)
SELECT 
    'Valid Tier Values' as test_name,
    CASE WHEN (
        SELECT COUNT(*) FROM assets 
        WHERE tier_number NOT IN (1, 2, 3)
    ) = 0 THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 12: Check amount values are positive
SELECT 
    'Positive Amounts' as test_name,
    CASE WHEN (
        SELECT COUNT(*) FROM assets 
        WHERE amount < 0
    ) = 0 THEN 'PASS' ELSE 'FAIL' END as result;

-- Test 13: Check price values are positive
SELECT 
    'Positive Prices' as test_name,
    CASE WHEN (
        SELECT COUNT(*) FROM assets 
        WHERE price_per_unit <= 0
    ) = 0 THEN 'PASS' ELSE 'FAIL' END as result;

-- ==============================================
-- CONSTRAINT TESTING
-- ==============================================

-- Test 14: Test tier constraint (should fail)
-- This will show an error if constraint is working
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (4, 'CONSTRAINT_TEST_TIER', 100.0, 50.0);

-- Test 15: Test amount constraint (should fail)
-- This will show an error if constraint is working
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'CONSTRAINT_TEST_AMOUNT', -100.0, 50.0);

-- Test 16: Test price constraint (should fail)
-- This will show an error if constraint is working
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'CONSTRAINT_TEST_PRICE', 100.0, 0.0);

-- Test 17: Test unique constraint (should fail)
-- This will show an error if constraint is working
INSERT INTO assets (tier_number, asset_name, amount, price_per_unit) 
VALUES (1, 'BTC', 100.0, 50000.0);

-- ==============================================
-- PERFORMANCE TESTS
-- ==============================================

-- Test 18: Test tier index performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM assets WHERE tier_number = 1;

-- Test 19: Test asset_name index performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM assets WHERE asset_name = 'BTC';

-- ==============================================
-- SUMMARY REPORT
-- ==============================================

-- Final summary
SELECT 
    '=== ASSETS-DB SCHEMA VALIDATION SUMMARY ===' as summary;

SELECT 
    'Total Assets' as metric,
    COUNT(*) as value
FROM assets;

SELECT 
    tier_number,
    COUNT(*) as count,
    CASE 
        WHEN tier_number = 1 THEN 'Cryptocurrencies'
        WHEN tier_number = 2 THEN 'ETFs/Stocks'
        WHEN tier_number = 3 THEN 'Alternative Investments'
    END as description
FROM assets 
GROUP BY tier_number 
ORDER BY tier_number;

-- Cleanup test data
DELETE FROM assets WHERE asset_name LIKE 'CONSTRAINT_TEST_%';

SELECT 
    '=== VALIDATION COMPLETE ===' as summary;
