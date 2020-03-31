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


INSERT INTO users VALUES ('1111111111', 'testuser', '\x243262243132245273764737474f39777562452f4a786a79444a7263756f386568466b762e634e5262356e6867746b474752584c6634437969346643', 'test', 'user', '2000-01-01', '-5', 'Bowling Green, New York City', 'NY', '10004', '111-22-3333') ON CONFLICT DO NOTHING;

INSERT INTO contacts VALUES ('testuser', 'External Checking', '9999999999', '987654321', 'true') ON CONFLICT DO NOTHING;
INSERT INTO contacts VALUES ('testuser', 'External Savings', '8888888888', '987654321', 'true') ON CONFLICT DO NOTHING;
INSERT INTO contacts VALUES ('testuser', 'Friend', '2222222222', '123456789', 'false') ON CONFLICT DO NOTHING;
INSERT INTO contacts VALUES ('testuser', 'Mom', '3333333333', '123456789', 'false') ON CONFLICT DO NOTHING;

