// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const { defineConfig } = require('cypress')

module.exports = defineConfig({
    "CI": true,
    "retries": 3,
    "video": false,
    "fixturesFolder": false,
    "chromeWebSecurity": false,
    "defaultCommandTimeout": 6000,
    "pageLoadTimeout": 10000,
    "responseTimeout": 10000,
    "env": {
        "messages": {
            "transaction": {
                "empty": "No Transactions Found",
                "error": "Error: Could Not Load Transactions"
            },
            "deposit": {
                "success": "Deposit successful",
                "error": "Deposit failed",
                "errRoutingNum": "invalid routing number"
            },
            "transfer": {
                "success": "Payment successful",
                "error": "Payment failed",
                "errSelf": "may not add yourself to contacts"
            },
            "invalidFeedback": {
                "accountNum": "Please enter a valid 10 digit account number",
                "routingNum": "Please enter a valid 9 digit routing number",
                "payment": "Please enter a valid amount",
                "username": "Please enter a valid username. Username must be 2 to 15 characters in length and contain only alphanumeric or underscore characters."
            }
        },
        "defaultUser": {
            "username": "testuser",
            "password": "bankofanthos",
            "name": "Test",
            "accountNum": "1011226111",
            "externalAccounts": [
                {
                    "accountNum": "9099791699",
                    "routingNum": "808889588"
                }
            ],
            "recipients": [
                {
                    "accountNum": "1033623433",
                    "name": "Alice"
                },
                {
                    "accountNum": "1055757655",
                    "name": "Bob"
                },
                {
                    "accountNum": "1077441377",
                    "name": "Eve"
                }
            ],
            "localRoutingNum": "883745000"
        }
    },
    "e2e": {
        supportFile: "cypress/support/index.js",
        specPattern: "cypress/integration/**/*.js"
    }
})