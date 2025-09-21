-- Master Test Runner for User Portfolio Database
-- This script runs all unit tests in sequence

\echo 'Starting User Portfolio Database Unit Tests...'
\echo '================================================'

-- Test 1: Schema Validation
\echo 'Running Schema Validation Tests...'
\i 01_schema_validation.sql

\echo ''
\echo 'Running Constraint Tests...'
\i 02_constraint_tests.sql

\echo ''
\echo 'Running Functionality Tests...'
\i 03_functionality_tests.sql

\echo ''
\echo 'Running Performance Tests...'
\i 04_performance_tests.sql

\echo ''
\echo '================================================'
\echo 'All unit tests completed!'
\echo 'Check the output above for any FAIL messages.'
