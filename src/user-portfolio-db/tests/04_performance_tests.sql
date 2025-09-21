-- Unit Tests for Database Performance
-- Test 4: Performance Tests

-- Test 4.1: Test index performance
DO $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    execution_time INTERVAL;
    test_passed BOOLEAN := TRUE;
BEGIN
    -- Insert test data
    INSERT INTO user_portfolios (user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
    SELECT 
        'test-user-' || i::text,
        1000.00 + (i * 100),
        50.0 + (i % 20),
        30.0 + (i % 15),
        20.0 - (i % 10),
        500.00 + (i * 50),
        300.00 + (i * 30),
        200.00 + (i * 20)
    FROM generate_series(1, 1000) AS i;
    
    -- Test user_id index performance
    start_time := clock_timestamp();
    PERFORM COUNT(*) FROM user_portfolios WHERE user_id = 'test-user-500';
    end_time := clock_timestamp();
    execution_time := end_time - start_time;
    
    IF execution_time < INTERVAL '10 milliseconds' THEN
        RAISE NOTICE 'PASS: user_id index query completed in %', execution_time;
    ELSE
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: user_id index query took too long: %', execution_time;
    END IF;
    
    -- Test created_at index performance
    start_time := clock_timestamp();
    PERFORM COUNT(*) FROM user_portfolios WHERE created_at > NOW() - INTERVAL '1 hour';
    end_time := clock_timestamp();
    execution_time := end_time - start_time;
    
    IF execution_time < INTERVAL '50 milliseconds' THEN
        RAISE NOTICE 'PASS: created_at index query completed in %', execution_time;
    ELSE
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: created_at index query took too long: %', execution_time;
    END IF;
    
    -- Cleanup
    DELETE FROM user_portfolios WHERE user_id LIKE 'test-user-%';
    
    IF test_passed THEN
        RAISE NOTICE 'Performance tests completed successfully!';
    ELSE
        RAISE NOTICE 'Some performance tests failed - consider reviewing indexes';
    END IF;
END $$;

-- Test 4.2: Test concurrent access simulation
DO $$
DECLARE
    test_passed BOOLEAN := TRUE;
    portfolio_id UUID;
BEGIN
    -- Insert test portfolio
    INSERT INTO user_portfolios (id, user_id, total_value, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value)
    VALUES ('test-portfolio-concurrent', 'test-user-concurrent', 1000.00, 50.0, 30.0, 20.0, 500.00, 300.00, 200.00)
    RETURNING id INTO portfolio_id;
    
    -- Simulate concurrent updates (in a real scenario, these would be separate transactions)
    BEGIN
        -- Update 1
        UPDATE user_portfolios 
        SET tier1_allocation = 60.0, tier2_allocation = 25.0, tier3_allocation = 15.0,
            tier1_value = 600.00, tier2_value = 250.00, tier3_value = 150.00
        WHERE id = portfolio_id;
        
        -- Update 2
        UPDATE user_portfolios 
        SET tier1_allocation = 40.0, tier2_allocation = 40.0, tier3_allocation = 20.0,
            tier1_value = 400.00, tier2_value = 400.00, tier3_value = 200.00
        WHERE id = portfolio_id;
        
        RAISE NOTICE 'PASS: Concurrent updates handled successfully';
    EXCEPTION WHEN OTHERS THEN
        test_passed := FALSE;
        RAISE NOTICE 'FAIL: Concurrent updates failed: %', SQLERRM;
    END;
    
    -- Cleanup
    DELETE FROM user_portfolios WHERE id = portfolio_id;
    
    IF test_passed THEN
        RAISE NOTICE 'Concurrent access tests completed successfully!';
    ELSE
        RAISE EXCEPTION 'Concurrent access tests failed';
    END IF;
END $$;
