/*
 * Copyright 2020, Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

CREATE TABLE IF NOT EXISTS users (
  accountid VARCHAR(16) NOT NULL,
  username VARCHAR(64) NOT NULL,
  passhash BYTEA NOT NULL,
  firstname VARCHAR(64) NOT NULL,
  lastname VARCHAR(64) NOT NULL,
  birthday DATE NOT NULL,
  timezone VARCHAR(8) NOT NULL,
  address VARCHAR(64) NOT NULL,
  state VARCHAR(2) NOT NULL,
  zip VARCHAR(16) NOT NULL,
  ssn VARCHAR(16) NOT NULL,
  CONSTRAINT pk_accountid PRIMARY KEY (accountid),
  CONSTRAINT unique_username UNIQUE (username)
);

CREATE INDEX IF NOT EXISTS idx_users_accountid ON users (accountid);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);



CREATE TABLE IF NOT EXISTS contacts (
  username VARCHAR(64) NOT NULL,
  label VARCHAR(64),
  account_num VARCHAR(16) NOT NULL,
  routing_num VARCHAR(16) NOT NULL,
  is_external BOOLEAN NOT NULL,
  FOREIGN KEY (username) REFERENCES users(username)
);

CREATE INDEX IF NOT EXISTS idx_contacts_username ON contacts (username);
