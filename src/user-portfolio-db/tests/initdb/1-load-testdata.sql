-- Test data for user-portfolio-db
-- This file contains sample data for development and testing

-- Insert sample user portfolios
INSERT INTO user_portfolios (id, user_id, total_value, currency, tier1_allocation, tier2_allocation, tier3_allocation, tier1_value, tier2_value, tier3_value) VALUES
('550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440001', 10000.00, 'USD', 60.0, 30.0, 10.0, 6000.00, 3000.00, 1000.00),
('550e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440002', 50000.00, 'USD', 40.0, 40.0, 20.0, 20000.00, 20000.00, 10000.00),
('550e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440003', 100000.00, 'USD', 20.0, 30.0, 50.0, 20000.00, 30000.00, 50000.00);

-- Insert sample portfolio transactions
INSERT INTO portfolio_transactions (portfolio_id, transaction_type, tier1_change, tier2_change, tier3_change, total_amount, fees, status) VALUES
('550e8400-e29b-41d4-a716-446655440010', 'ALLOCATION_CHANGE', 10.0, -5.0, -5.0, 0.00, 0.00, 'COMPLETED'),
('550e8400-e29b-41d4-a716-446655440011', 'DEPOSIT', 0.0, 0.0, 0.0, 10000.00, 50.00, 'COMPLETED'),
('550e8400-e29b-41d4-a716-446655440012', 'ALLOCATION_CHANGE', -10.0, 0.0, 10.0, 0.00, 0.00, 'COMPLETED');
