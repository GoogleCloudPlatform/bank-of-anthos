-- Unit Tests for Database Functionality
-- Test 3: Functionality Tests

-- Test 3.1: Test automatic timestamp updates
DO $$
DECLARE
    portfolio_id UUID;
    created_time TIMESTAMPTZ;
    updated_time TIMESTAMPTZ;
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Insert a test portfolio
    INSERT INTO user_portfolios (user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
    VALUES ('test-user-timestamp', 1000.00, 50.0, 30.0, 20.0, 500.00, 300.00, 200.00)
    RETURNING id, created_at, updated_at INTO portfolio_id, created_time, updated_time;
    
    -- Verify created_at and updated_at are set
    IF created_time IS NULL OR updated_time IS NULL THEN
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Timestamps not set on insert';
    ELSE
        RAISE NOTICE 'PASS: Timestamps set on insert';
    END IF;
    
    -- Wait a moment and update
    PERFORM pg_sleep(1);
    UPDATE user_portfolios 
    SET tier1_allocation = 60.0, tier2_allocation = 25.0, tier3_allocation = 15.0
    WHERE id = portfolio_id
    RETURNING updated_at INTO updated_time;
    
    -- Verify updated_at changed
    IF updated_time > created_time THEN
        RAISE NOTICE 'PASS: updated_at timestamp updated correctly';
    ELSE
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: updated_at timestamp not updated';
    END IF;
    
    -- Cleanup
    DELETE FROM user_portfolios WHERE id = portfolio_id;
    
    IF test_passed THEN
        RAISE NOTICE 'Timestamp functionality tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Some timestamp functionality tests failed';
    END IF;
END $$;

-- Test 3.2: Test portfolio_summary view
DO $$
DECLARE
    portfolio_id UUID;
    view_count INTEGER;
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Insert test data
    INSERT INTO user_portfolios (id, user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
    VALUES ('test-portfolio-view', 'test-user-view', 5000.00, 40.0, 35.0, 25.0, 2000.00, 1750.00, 1250.00)
    RETURNING id INTO portfolio_id;
    
    -- Test view returns data
    SELECT COUNT(*) INTO view_count FROM portfolio_summary WHERE portfolio_id = 'test-portfolio-view';
    
    IF view_count = 1 THEN
        RAISE NOTICE 'PASS: portfolio_summary view returns data';
    ELSE
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: portfolio_summary view does not return data';
    END IF;
    
    -- Test view data accuracy
    DO $$
    DECLARE
        view_record RECORD;
    BEGIN
        SELECT * INTO view_record FROM portfolio_summary WHERE portfolio_id = 'test-portfolio-view';
        
        IF view_record.tier1_allocation = 40.0 AND view_record.tier2_allocation = 35.0 AND view_record.tier3_allocation = 25.0 THEN
            RAISE NOTICE 'PASS: portfolio_summary view data is accurate';
        ELSE
            test_passed := FALSE;
            RAISE NOTICE 'FAIL: portfolio_summary view data is inaccurate';
        END IF;
    END $$;
    
    -- Cleanup
    DELETE FROM user_portfolios WHERE id = portfolio_id;
    
    IF test_passed THEN
        RAISE NOTICE 'View functionality tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Some view functionality tests failed';
    END IF;
END $$;

-- Test 3.3: Test foreign key relationships
DO $$
DECLARE
    portfolio_id UUID;
    transaction_id UUID;
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Insert test portfolio
    INSERT INTO user_portfolios (id, user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
    VALUES ('test-portfolio-fk', 'test-user-fk', 1000.00, 50.0, 30.0, 20.0, 500.00, 300.00, 200.00)
    RETURNING id INTO portfolio_id;
    
    -- Insert transaction with valid foreign key
    INSERT INTO portfolio_transactions (portfolio_id, transaction_type, total_amount)
    VALUES (portfolio_id, 'ALLOCATION_CHANGE', 0.00)
    RETURNING id INTO transaction_id;
    
    IF transaction_id IS NOT NULL THEN
        RAISE NOTICE 'PASS: Valid foreign key relationship works';
    ELSE
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Valid foreign key relationship failed';
    END IF;
    
    -- Test cascade delete
    DELETE FROM user_portfolios WHERE id = portfolio_id;
    
    -- Verify transaction was deleted (cascade)
    SELECT COUNT(*) INTO transaction_id FROM portfolio_transactions WHERE id = transaction_id;
    
    IF transaction_id = 0 THEN
        RAISE NOTICE 'PASS: Cascade delete works correctly';
    ELSE
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Cascade delete did not work';
    END IF;
    
    IF test_passed THEN
        RAISE NOTICE 'Foreign key functionality tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Some foreign key functionality tests failed';
    END IF;
END $$;
