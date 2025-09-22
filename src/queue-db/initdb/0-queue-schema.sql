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

-- Create the withdrawal queue table
CREATE TABLE IF NOT EXISTS withdrawal_queue (
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
CREATE INDEX IF NOT EXISTS idx_investment_queue_account ON investment_queue (account_number);
CREATE INDEX IF NOT EXISTS idx_investment_queue_uuid ON investment_queue (uuid);
CREATE INDEX IF NOT EXISTS idx_investment_queue_status ON investment_queue (status);
CREATE INDEX IF NOT EXISTS idx_investment_queue_created ON investment_queue (created_at);

-- Create indexes for withdrawal queue
CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_account ON withdrawal_queue (account_number);
CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_uuid ON withdrawal_queue (uuid);
CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_status ON withdrawal_queue (status);
CREATE INDEX IF NOT EXISTS idx_withdrawal_queue_created ON withdrawal_queue (created_at);

-- Add constraints for investment queue
ALTER TABLE investment_queue 
ADD CONSTRAINT chk_investment_status_valid CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')),
ADD CONSTRAINT chk_investment_uuid_format CHECK (uuid ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

-- Add constraints for withdrawal queue
ALTER TABLE withdrawal_queue 
ADD CONSTRAINT chk_withdrawal_status_valid CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')),
ADD CONSTRAINT chk_withdrawal_uuid_format CHECK (uuid ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

-- Add comments for better documentation
COMMENT ON TABLE investment_queue IS 'Stores investment requests for tier-based portfolio management';
COMMENT ON COLUMN investment_queue.account_number IS 'Bank account number making the investment request';
COMMENT ON COLUMN investment_queue.tier_1 IS 'Amount to add to Tier 1 (Conservative investments)';
COMMENT ON COLUMN investment_queue.tier_2 IS 'Amount to add to Tier 2 (Moderate investments)';
COMMENT ON COLUMN investment_queue.tier_3 IS 'Amount to add to Tier 3 (Aggressive investments)';
COMMENT ON COLUMN investment_queue.uuid IS 'Unique identifier for the investment queue entry';
COMMENT ON COLUMN investment_queue.status IS 'Processing status of the investment queue entry';
COMMENT ON COLUMN investment_queue.created_at IS 'Timestamp when the investment request was created';
COMMENT ON COLUMN investment_queue.updated_at IS 'Timestamp when the investment request was last updated';
COMMENT ON COLUMN investment_queue.processed_at IS 'Timestamp when the investment request was processed';

COMMENT ON TABLE withdrawal_queue IS 'Stores withdrawal requests for tier-based portfolio management';
COMMENT ON COLUMN withdrawal_queue.account_number IS 'Bank account number making the withdrawal request';
COMMENT ON COLUMN withdrawal_queue.tier_1 IS 'Amount to remove from Tier 1 (Conservative investments)';
COMMENT ON COLUMN withdrawal_queue.tier_2 IS 'Amount to remove from Tier 2 (Moderate investments)';
COMMENT ON COLUMN withdrawal_queue.tier_3 IS 'Amount to remove from Tier 3 (Aggressive investments)';
COMMENT ON COLUMN withdrawal_queue.uuid IS 'Unique identifier for the withdrawal queue entry';
COMMENT ON COLUMN withdrawal_queue.status IS 'Processing status of the withdrawal queue entry';
COMMENT ON COLUMN withdrawal_queue.created_at IS 'Timestamp when the withdrawal request was created';
COMMENT ON COLUMN withdrawal_queue.updated_at IS 'Timestamp when the withdrawal request was last updated';
COMMENT ON COLUMN withdrawal_queue.processed_at IS 'Timestamp when the withdrawal request was processed';

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at for investment queue
CREATE TRIGGER update_investment_queue_updated_at 
    BEFORE UPDATE ON investment_queue 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to automatically update updated_at for withdrawal queue
CREATE TRIGGER update_withdrawal_queue_updated_at 
    BEFORE UPDATE ON withdrawal_queue 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create a function to generate consistent UUIDs for queue entries
CREATE OR REPLACE FUNCTION generate_queue_uuid()
RETURNS VARCHAR(36) AS $$
BEGIN
    RETURN gen_random_uuid()::VARCHAR(36);
END;
$$ LANGUAGE plpgsql;

-- Create a function to validate UUID consistency across queues
CREATE OR REPLACE FUNCTION validate_uuid_consistency(
    p_uuid VARCHAR(36),
    p_queue_type VARCHAR(20)
)
RETURNS BOOLEAN AS $$
DECLARE
    uuid_exists BOOLEAN := FALSE;
BEGIN
    -- Check if UUID exists in either queue
    SELECT EXISTS(
        SELECT 1 FROM investment_queue WHERE uuid = p_uuid
        UNION
        SELECT 1 FROM withdrawal_queue WHERE uuid = p_uuid
    ) INTO uuid_exists;
    
    -- If UUID exists, it should be in the same queue type
    IF uuid_exists THEN
        IF p_queue_type = 'INVESTMENT' THEN
            RETURN EXISTS(SELECT 1 FROM investment_queue WHERE uuid = p_uuid);
        ELSIF p_queue_type = 'WITHDRAWAL' THEN
            RETURN EXISTS(SELECT 1 FROM withdrawal_queue WHERE uuid = p_uuid);
        END IF;
    END IF;
    
    -- If UUID doesn't exist, it's valid for new entries
    RETURN NOT uuid_exists;
END;
$$ LANGUAGE plpgsql;

-- Add constraint to ensure UUID consistency
ALTER TABLE investment_queue 
ADD CONSTRAINT chk_investment_uuid_consistency 
CHECK (validate_uuid_consistency(uuid, 'INVESTMENT'));

ALTER TABLE withdrawal_queue 
ADD CONSTRAINT chk_withdrawal_uuid_consistency 
CHECK (validate_uuid_consistency(uuid, 'WITHDRAWAL'));
