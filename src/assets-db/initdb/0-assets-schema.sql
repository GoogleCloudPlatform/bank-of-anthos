# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CREATE TABLE IF NOT EXISTS assets (
    asset_id SERIAL PRIMARY KEY,
    tier_number INTEGER NOT NULL CHECK (tier_number IN (1, 2, 3)),
    asset_name VARCHAR(64) UNIQUE NOT NULL,
    amount DECIMAL(20, 8) NOT NULL CHECK (amount >= 0),
    price_per_unit DECIMAL(20, 2) NOT NULL CHECK (price_per_unit > 0),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for commonly queried columns
CREATE INDEX IF NOT EXISTS idx_assets_tier ON assets (tier_number);
CREATE INDEX IF NOT EXISTS idx_assets_name ON assets (asset_name);

-- Add comments for better documentation
COMMENT ON TABLE assets IS 'Stores information about available investment assets';
COMMENT ON COLUMN assets.tier_number IS 'Investment tier (1, 2, or 3)';
COMMENT ON COLUMN assets.asset_name IS 'Unique identifier for the asset';
COMMENT ON COLUMN assets.amount IS 'Available units for investment';
COMMENT ON COLUMN assets.price_per_unit IS 'Current price per unit in USD';
COMMENT ON COLUMN assets.last_updated IS 'Timestamp of last price/amount update';
