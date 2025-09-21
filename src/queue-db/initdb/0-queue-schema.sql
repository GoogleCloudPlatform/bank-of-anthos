-- Copyright 2024 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     https://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- Create the investment queue table
CREATE TABLE IF NOT EXISTS investment_queue (
    queue_id SERIAL PRIMARY KEY,
    account_number VARCHAR(20) NOT NULL,
    tier_1 DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    tier_2 DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    tier_3 DECIMAL(20, 8) NOT NULL DEFAULT 0.0,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create indexes for commonly queried columns
CREATE INDEX IF NOT EXISTS idx_queue_account ON investment_queue (account_number);
CREATE INDEX IF NOT EXISTS idx_queue_uuid ON investment_queue (uuid);
CREATE INDEX IF NOT EXISTS idx_queue_status ON investment_queue (status);
CREATE INDEX IF NOT EXISTS idx_queue_created ON investment_queue (created_at);

-- Add constraints
ALTER TABLE investment_queue 
ADD CONSTRAINT chk_status_valid CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')),
ADD CONSTRAINT chk_uuid_format CHECK (uuid ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

-- Add comments for better documentation
COMMENT ON TABLE investment_queue IS 'Stores investment and withdrawal requests for tier-based portfolio management';
COMMENT ON COLUMN investment_queue.account_number IS 'Bank account number making the request';
COMMENT ON COLUMN investment_queue.tier_1 IS 'Amount to add/remove from Tier 1 (Cryptocurrencies)';
COMMENT ON COLUMN investment_queue.tier_2 IS 'Amount to add/remove from Tier 2 (ETFs/Stocks)';
COMMENT ON COLUMN investment_queue.tier_3 IS 'Amount to add/remove from Tier 3 (Alternative Investments)';
COMMENT ON COLUMN investment_queue.uuid IS 'Unique identifier for the queue entry';
COMMENT ON COLUMN investment_queue.status IS 'Processing status of the queue entry';
COMMENT ON COLUMN investment_queue.created_at IS 'Timestamp when the request was created';
COMMENT ON COLUMN investment_queue.updated_at IS 'Timestamp when the request was last updated';
COMMENT ON COLUMN investment_queue.processed_at IS 'Timestamp when the request was processed';

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_investment_queue_updated_at 
    BEFORE UPDATE ON investment_queue 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
