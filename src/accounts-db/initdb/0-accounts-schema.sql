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
  accountid INTEGER NOT NULL,
  username VARCHAR(64) NOT NULL,
  passhash VARCHAR(256),
  firstname VARCHAR(32),
  lastname VARCHAR(32),
  birthday DATE,
  timezone VARCHAR(64),
  address VARCHAR(256),
  state VARCHAR(32),
  zip VARCHAR(16),
  ssn VARCHAR(16),
  CONSTRAINT pk_accountid PRIMARY KEY (accountid),
  CONSTRAINT unique_username UNIQUE (username)
);

CREATE INDEX IF NOT EXISTS idx_users_accountid ON users (accountid);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);



CREATE TABLE IF NOT EXISTS contacts (
  username VARCHAR(64) NOT NULL,
  label VARCHAR(64) NOT NULL,
  account_num VARCHAR(16),
  routing_num VARCHAR(16),
  FOREIGN KEY (username) REFERENCES users(username)
);

CREATE INDEX IF NOT EXISTS idx_contacts_username ON contacts (username);
