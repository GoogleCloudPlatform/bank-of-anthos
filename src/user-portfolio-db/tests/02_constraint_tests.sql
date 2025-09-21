-- Unit Tests for Database Constraints
-- Test 2: Constraint Validation Tests

-- Test 2.1: Test tier allocation constraint (must sum to 100%)
DO $$
DECLARE
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Test valid allocation (should pass)
    BEGIN
        INSERT INTO user_portfolios (user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
        VALUES ('test-user-1', 1000.00, 50.0, 30.0, 20.0, 500.00, 300.00, 200.00);
        DELETE FROM user_portfolios WHERE user_id = 'test-user-1';
        RAISE NOTICE 'PASS: Valid allocation (50+30+20=100) accepted';
    EXCEPTION WHEN OTHERS THEN
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Valid allocation rejected: %', SQLERRM;
    END;
    
    -- Test invalid allocation (should fail)
    BEGIN
        INSERT INTO user_portfolios (user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
        VALUES ('test-user-2', 1000.00, 50.0, 30.0, 25.0, 500.00, 300.00, 250.00);
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Invalid allocation (50+30+25=105) was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Invalid allocation (50+30+25=105) correctly rejected';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'FAIL: Unexpected error for invalid allocation: %', SQLERRM;
    END;
    
    IF test_passed THEN
        RAISE NOTICE 'Constraint tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Some constraint tests failed';
    END IF;
END $$;

-- Test 2.2: Test tier allocation range constraints (0-100%)
DO $$
DECLARE
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Test negative allocation (should fail)
    BEGIN
        INSERT INTO user_portfolios (user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
        VALUES ('test-user-3', 1000.00, -10.0, 60.0, 50.0, -100.00, 600.00, 500.00);
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Negative allocation was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Negative allocation correctly rejected';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'FAIL: Unexpected error for negative allocation: %', SQLERRM;
    END;
    
    -- Test allocation over 100% (should fail)
    BEGIN
        INSERT INTO user_portfolios (user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
        VALUES ('test-user-4', 1000.00, 50.0, 30.0, 25.0, 500.00, 300.00, 250.00);
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Allocation over 100% was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Allocation over 100% correctly rejected';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'FAIL: Unexpected error for allocation over 100%: %', SQLERRM;
    END;
    
    IF test_passed THEN
        RAISE NOTICE 'Range constraint tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Some range constraint tests failed';
    END IF;
END $$;

-- Test 2.3: Test transaction type constraints
DO $$
DECLARE
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Test valid transaction type (should pass)
    BEGIN
        INSERT INTO user_portfolios (id, user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
        VALUES ('test-portfolio-1', 'test-user-5', 1000.00, 50.0, 30.0, 20.0, 500.00, 300.00, 200.00);
        
        INSERT INTO portfolio_transactions (portfolio_id, transaction_type, total_amount)
        VALUES ('test-portfolio-1', 'ALLOCATION_CHANGE', 0.00);
        
        DELETE FROM portfolio_transactions WHERE portfolio_id = 'test-portfolio-1';
        DELETE FROM user_portfolios WHERE id = 'test-portfolio-1';
        RAISE NOTICE 'PASS: Valid transaction type accepted';
    EXCEPTION WHEN OTHERS THEN
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Valid transaction type rejected: %', SQLERRM;
    END;
    
    -- Test invalid transaction type (should fail)
    BEGIN
        INSERT INTO user_portfolios (id, user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
        VALUES ('test-portfolio-2', 'test-user-6', 1000.00, 50.0, 30.0, 20.0, 500.00, 300.00, 200.00);
        
        INSERT INTO portfolio_transactions (portfolio_id, transaction_type, total_amount)
        VALUES ('test-portfolio-2', 'INVALID_TYPE', 0.00);
        
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Invalid transaction type was accepted';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Invalid transaction type correctly rejected';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'FAIL: Unexpected error for invalid transaction type: %', SQLERRM;
    END;
    
    -- Cleanup
    DELETE FROM portfolio_transactions WHERE portfolio_id = 'test-portfolio-2';
    DELETE FROM user_portfolios WHERE id = 'test-portfolio-2';
    
    IF test_passed THEN
        RAISE NOTICE 'Transaction constraint tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Some transaction constraint tests failed';
    END IF;
END $$;
