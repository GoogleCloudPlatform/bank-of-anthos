-- Copyright 2020 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--      http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- Spanner DDL for TRANSACTIONS table
CREATE TABLE TRANSACTIONS (
    TRANSACTION_ID INT64 NOT NULL,
    FROM_ACCT STRING(10) NOT NULL,
    TO_ACCT STRING(10) NOT NULL,
    FROM_ROUTE STRING(9) NOT NULL,
    TO_ROUTE STRING(9) NOT NULL,
    AMOUNT INT64 NOT NULL,
    TIMESTAMP TIMESTAMP NOT NULL
) PRIMARY KEY (TRANSACTION_ID);

-- Create sequence for auto-incrementing transaction IDs
CREATE SEQUENCE TRANSACTION_SEQ OPTIONS (
  sequence_kind = "bit_reversed_positive"
);

-- Index account number/routing number pairs for efficient queries
CREATE INDEX IDX_TRANSACTIONS_FROM ON TRANSACTIONS (FROM_ACCT, FROM_ROUTE, TIMESTAMP);
CREATE INDEX IDX_TRANSACTIONS_TO ON TRANSACTIONS (TO_ACCT, TO_ROUTE, TIMESTAMP);

-- Note: Spanner does not support PostgreSQL RULES for preventing updates/deletes.
-- Append-only behavior should be enforced through IAM permissions and application logic.
