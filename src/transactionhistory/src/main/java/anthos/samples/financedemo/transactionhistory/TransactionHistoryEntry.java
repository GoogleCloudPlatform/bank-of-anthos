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

import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;


enum TransactionType {
    DEBIT, CREDIT;
}
/**
 * Defines a banking transaction histoy entry for display to a user
 */
public final class TransactionHistoryEntry {

    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");

    @JsonProperty("type")
    private TransactionType type;
    @JsonProperty("routingNum")
    private String routingNum;
    @JsonProperty("accountNum")
    private String accountNum;
    @JsonProperty("amount")
    private Integer amount;
    @JsonProperty("timestamp")
    private final double timestamp;

    /**
     * Construct a TransactionHistoryEntry
     *
     * @param map returned from redis
     * @param transaction type (credit or debit) to parse from the map
     */
    public TransactionHistoryEntry(Map<String, String> map,
                                   TransactionType type) {
        this.type = type;
        this.amount = Integer.valueOf(map.get("amount"));
        this.timestamp = Double.valueOf(map.get("timestamp"));
        if (type == TransactionType.CREDIT) {
            this.accountNum = map.get("toAccountNum");
            this.routingNum = map.get("toRoutingNum");
        } else if (type == TransactionType.DEBIT) {
            this.accountNum = map.get("fromAccountNum");
            this.routingNum = map.get("fromRoutingNum");
        }
    }

    /**
     * String representation.
     *
     * "{accountNum}:{type}:{amount}"
     */
    public String toString() {
        return String.format("%s:%s:%d", accountNum, type, amount);
    }
}
