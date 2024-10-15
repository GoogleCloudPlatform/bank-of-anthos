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


INSERT INTO users (accountid, username, passhash, salt, firstname, lastname, birthday, timezone, address, state, zip, ssn) 
VALUES
('1011226111', 'testuser', '\x5da0a1304c22bec69bdb74f66d590cd4a0d585063ecbd7d1120662ddf55c49c8', '\x0e0ab7fc8ad0f68d8c0a88da06a7e79e', 'Test', 'User', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333'),
('1033623433', 'alice', '\x5da0a1304c22bec69bdb74f66d590cd4a0d585063ecbd7d1120662ddf55c49c8', '\x0e0ab7fc8ad0f68d8c0a88da06a7e79e', 'Alice', 'User', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333'),
('1055757655', 'bob', '\x5da0a1304c22bec69bdb74f66d590cd4a0d585063ecbd7d1120662ddf55c49c8', '\x0e0ab7fc8ad0f68d8c0a88da06a7e79e', 'Bob', 'User', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333'),
('1077441377', 'eve', '\x5da0a1304c22bec69bdb74f66d590cd4a0d585063ecbd7d1120662ddf55c49c8', '\x0e0ab7fc8ad0f68d8c0a88da06a7e79e', 'Eve', 'User', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333')
ON CONFLICT DO NOTHING;

INSERT INTO contacts VALUES
('testuser', 'Alice', '1033623433', '883745000', 'false'),
('testuser', 'Bob', '1055757655', '883745000', 'false'),
('testuser', 'Eve', '1077441377', '883745000', 'false'),
('alice', 'Testuser', '1011226111', '883745000', 'false'),
('alice', 'Bob', '1055757655', '883745000', 'false'),
('alice', 'Eve', '1077441377', '883745000', 'false'),
('bob', 'Testuser', '1011226111', '883745000', 'false'),
('bob', 'Alice', '1033623433', '883745000', 'false'),
('bob', 'Eve', '1077441377', '883745000', 'false'),
('eve', 'Testuser', '1011226111', '883745000', 'false'),
('eve', 'Alice', '1033623433', '883745000', 'false'),
('eve', 'Bob', '1055757655', '883745000', 'false')
ON CONFLICT DO NOTHING;

INSERT INTO contacts VALUES
('testuser', 'External Bank', '9099791699', '808889588', 'true'),
('alice', 'External Bank', '9099791699', '808889588', 'true'),
('bob', 'External Bank', '9099791699', '808889588', 'true'),
('eve', 'External Bank', '9099791699', '808889588', 'true')
ON CONFLICT DO NOTHING;


