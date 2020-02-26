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

/**
 * Defines a banking transaction entry.
 *
 * Timestamped at object creation time.
 */

enum TransactionType {
    DEBIT, CREDIT;
}

public final class TransactionHistoryEntry {

    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");

    private TransactionType type;
    private String routingNum;
    private String accountNum;
    private Integer amount;
    private final double timestamp;

    public TransactionHistoryEntry(Map<String, String> map,
                                   TransactionType type) {
        this.type = type;
        this.amount = Integer.valueOf(map.get("amount"));
        this.timestamp = Double.valueOf(map.get("timestamp"));
        if (type == TransactionType.CREDIT) {
            this.accountNum = map.get("fromAccountNum");
            this.routingNum = map.get("fromRoutingNum");
        } else if (type == TransactionType.DEBIT) {
            this.accountNum = map.get("toAccountNum");
            this.routingNum = map.get("toRoutingNum");
        }
    }

    public String toString() {
        return String.format("%d: %s",
                amount, accountNum);
    }
}
