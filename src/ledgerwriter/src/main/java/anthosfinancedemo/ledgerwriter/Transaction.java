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

package anthosfinancedemo.ledgerwriter;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines a banking transaction.
 */
public class Transaction {

    @JsonProperty("from_account_num")
    public String fromAccountNum;
    @JsonProperty("from_routing_num")
    public String fromRoutingNum;
    @JsonProperty("to_account_num")
    public String toAccountNum;
    @JsonProperty("to_routing_num")
    public String toRoutingNum;
    @JsonProperty("amount")
    public int amount;
    public long date;

    public String toString() {
        return String.format("$%d: %s->%s", amount/100, fromAccountNum, toAccountNum);
    }
}
