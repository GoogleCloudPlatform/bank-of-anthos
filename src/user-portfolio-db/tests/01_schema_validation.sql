-- Unit Tests for User Portfolio Database Schema
-- Test 1: Schema Validation Tests

-- Test 1.1: Verify all required tables exist
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('user_portfolios', 'portfolio_transactions', 'portfolio_analytics');
    
    IF table_count = 3 THEN
        RAISE NOTICE 'PASS: All required tables exist';
    ELSE
        RAISE EXCEPTION 'FAIL: Expected 3 tables, found %', table_count;
    END IF;
END $$;

-- Test 1.2: Verify user_portfolios table structure
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns 
    WHERE table_name = 'user_portfolios' 
    AND column_name IN ('id', 'user_id', 'total_value', 'currency', 'tier1_allocation', 'tier2_allocation', 'tier3_allocation', 'tier1_value', 'tier2_value', 'tier3_value', 'created_at', 'updated_at');
    
    IF column_count = 12 THEN
        RAISE NOTICE 'PASS: user_portfolios table has all required columns';
    ELSE
        RAISE EXCEPTION 'FAIL: user_portfolios table missing columns, found %', column_count;
    END IF;
END $$;

-- Test 1.3: Verify constraints exist
DO $$
DECLARE
    constraint_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints 
    WHERE table_name = 'user_portfolios' 
    AND constraint_type = 'CHECK';
    
    IF constraint_count >= 1 THEN
        RAISE NOTICE 'PASS: user_portfolios has CHECK constraints';
    ELSE
        RAISE EXCEPTION 'FAIL: user_portfolios missing CHECK constraints';
    END IF;
END $$;

-- Test 1.4: Verify indexes exist
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE tablename = 'user_portfolios' 
    AND indexname LIKE 'idx_%';
    
    IF index_count >= 2 THEN
        RAISE NOTICE 'PASS: user_portfolios has required indexes';
    ELSE
        RAISE EXCEPTION 'FAIL: user_portfolios missing indexes, found %', index_count;
    END IF;
END $$;

-- Test 1.5: Verify triggers exist
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers 
    WHERE event_object_table = 'user_portfolios';
    
    IF trigger_count >= 1 THEN
        RAISE NOTICE 'PASS: user_portfolios has triggers';
    ELSE
        RAISE EXCEPTION 'FAIL: user_portfolios missing triggers';
    END IF;
END $$;

-- Test 1.6: Verify view exists
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO view_count
    FROM information_schema.views 
    WHERE table_name = 'portfolio_summary';
    
    IF view_count = 1 THEN
        RAISE NOTICE 'PASS: portfolio_summary view exists';
    ELSE
        RAISE EXCEPTION 'FAIL: portfolio_summary view missing';
    END IF;
END $$;

RAISE NOTICE 'Schema validation tests completed successfully!';
