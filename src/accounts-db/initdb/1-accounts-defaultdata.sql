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

INSERT INTO users VALUES ('123456789', 'testuser123', 'passhash', '', '', '2000-02-02', '', '', '', '', '') ON CONFLICT DO NOTHING;

INSERT INTO contacts VALUES ('testuser123', 'External Checking', '0123456789', '111111111') ON CONFLICT DO NOTHING;
INSERT INTO contacts VALUES ('testuser123', 'External Savings', '9876543210', '222222222') ON CONFLICT DO NOTHING;
INSERT INTO contacts VALUES ('testuser123', 'Friend', '1122334455', '123456789') ON CONFLICT DO NOTHING;
INSERT INTO contacts VALUES ('testuser123', 'Mom', '6677889900', '123456789') ON CONFLICT DO NOTHING;
