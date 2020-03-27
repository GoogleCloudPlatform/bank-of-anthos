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
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;

enum TransactionType {
    DEBIT, CREDIT;
}
/**
 * Defines a banking transaction histoy entry for display to a user
 */
@Entity
@Table(name="TRANSACTIONS")
final class TransactionHistoryEntry {

    @Id
    @Column(name="TRANSACTION_ID")
    @GeneratedValue(strategy=GenerationType.IDENTITY)
    private long transactionId;

    @JsonProperty("accountNum")
    @Column (name="SEND_ACCT")
    private String accountNum;

    @Column (name="KEY_ACCT")
    private String keyAccountNum;

    @JsonProperty("routingNum")
    @Column (name="SEND_ROUTING")
    private String routingNum;

    @JsonProperty("amount")
    @Column (name="AMOUNT")
    private long amount;

    @JsonProperty("timestamp")
    @Column (name="TIMESTAMP")
    private double timestamp;

    public long getTransactionId() {
        return transactionId;
    }

    public void setTransactionId(long transactionId){
        this.transactionId = transactionId;
    }

    public String getAccountNum(){
        return accountNum;
    }

    public void setAccountNum(String accountNum) {
        this.accountNum = accountNum;
    }

    public String getKeyAccountNum() {
        return keyAccountNum;
    }

    public void setKeyAccountNum(String keyAccountNum){
        this.keyAccountNum = keyAccountNum;
    }

    public String getRoutingNum() {
        return routingNum;
    }

    public void setRoutingNum(String routingNum){
        this.routingNum = routingNum;
    }

    public long getAmount() {
        return amount;
    }

    public void setAmount(long amount){
        this.amount = amount;
    }

    public double getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(double timestamp){
        this.timestamp = timestamp;
    }

    /**
     * Construct a TransactionHistoryEntry
     *
     * @param map returned from redis
     * @param transaction type (credit or debit) to parse from the map
     */
    public TransactionHistoryEntry(Map<String, String> map,
                                   TransactionType type) {
        //this.type = type;
        this.amount = Integer.valueOf(map.get("amount"));
        this.timestamp = Double.valueOf(map.get("timestamp"));
        if (type == TransactionType.CREDIT) {
            this.accountNum = map.get("toAccountNum");
            this.routingNum = map.get("toRoutingNum");
            this.keyAccountNum = map.get("fromAccountNum");
        } else if (type == TransactionType.DEBIT) {
            this.accountNum = map.get("fromAccountNum");
            this.routingNum = map.get("fromRoutingNum");
            this.keyAccountNum = map.get("toAccountNum");
        }
    }

    public TransactionHistoryEntry() {}
}
