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

package anthos.samples.financedemo.transactionhistory;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
public final class Transaction {

    // Timestamp in seconds with decimal precision.
    private final double timestamp;

    @JsonProperty("fromAccountNum")
    private String fromAccountNum;
    @JsonProperty("fromRoutingNum")
    private String fromRoutingNum;
    @JsonProperty("toAccountNum")
    private String toAccountNum;
    @JsonProperty("toRoutingNum")
    private String toRoutingNum;
    @JsonProperty("amount")
    private Integer amount;

    public Transaction(Map<String, String> map) {
        this.fromAccountNum = map.get("fromAccountNum");
        this.fromRoutingNum = map.get("fromRoutingNum");
        this.toAccountNum = map.get("toAccountNum");
        this.toRoutingNum = map.get("toRoutingNum");
        this.amount = Integer.valueOf(map.get("amount"));
        this.timestamp = Double.valueOf(map.get("timestamp"));
    }

    public String toString() {
        return String.format("%d: %s->%s",
                amount, fromAccountNum, toAccountNum);
    }
}
