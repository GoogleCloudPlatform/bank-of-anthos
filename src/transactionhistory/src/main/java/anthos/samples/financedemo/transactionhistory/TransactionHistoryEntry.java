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

import org.springframework.beans.factory.annotation.Value;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines an entry in a list of historical banking transactions.
 */
public final class TransactionHistoryEntry {

    /**
     * The possible types of transactions.
     */
    public static enum Type {
        DEBIT, CREDIT;
    }

    @Value("${LOCAL_ROUTING_NUM}")
    private String localRoutingNum;

    @JsonProperty("type")
    private Type type;
    @JsonProperty("routingNum")
    private String routingNum;
    @JsonProperty("accountNum")
    private String accountNum;
    @JsonProperty("amount")
    private Integer amount;
    @JsonProperty("timestamp")
    private final double timestamp;

    /**
     * Constructor.
     *
     * @param map   the transaction attributes as a map of key/value pairs
     * @param type  the transaction type (credit or debit)
     */
    public TransactionHistoryEntry(Map<String, String> map,
                                   Type type) {
        this.type = type;
        this.amount = Integer.valueOf(map.get("amount"));
        this.timestamp = Double.valueOf(map.get("timestamp"));
        if (type == Type.CREDIT) {
            this.accountNum = map.get("toAccountNum");
            this.routingNum = map.get("toRoutingNum");
        } else if (type == Type.DEBIT) {
            this.accountNum = map.get("fromAccountNum");
            this.routingNum = map.get("fromRoutingNum");
        }
    }

    /**
     * String representation.
     *
     * Formatting = "{accountNum}:{type}:{amount}"
     */
    public String toString() {
        return String.format("%s:%s:%d", accountNum, type, amount);
    }
}
