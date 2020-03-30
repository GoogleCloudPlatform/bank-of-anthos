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

package anthos.samples.financedemo.ledgerwriter;

import com.fasterxml.jackson.annotation.JsonProperty;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;

import javax.persistence.Index;

import java.util.Date;
import org.hibernate.annotations.CreationTimestamp;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
@Entity
@Table(name="TRANSACTIONS")
public final class Transaction {

    private static final double MILLISECONDS_PER_SECOND = 1000.0;

    @Id
    @Column(name="TRANSACTION_ID")
    @GeneratedValue(strategy=GenerationType.IDENTITY)
    private long transactionId;

    @Column(name="FROM_ACCT")
    @JsonProperty("fromAccountNum")
    private String fromAccountNum;
    @Column(name="FROM_ROUTE")
    @JsonProperty("fromRoutingNum")
    private String fromRoutingNum;
    @Column(name="TO_ACCT")
    @JsonProperty("toAccountNum")
    private String toAccountNum;
    @Column(name="TO_ROUTE")
    @JsonProperty("toRoutingNum")
    private String toRoutingNum;
    @Column(name="AMOUNT")
    @JsonProperty("amount")
    private Integer amount;
    @Column(name="TIMESTAMP", nullable = false, updatable = false)
    @CreationTimestamp
    @JsonProperty("timestamp")
    private Date timestamp;

    public long getTransactionId() {
        return this.transactionId;
    }

    public String getFromAccountNum() {
        return this.fromAccountNum;
    }

    public void setFromAccountNum(String fromAccountNum) {
        this.fromAccountNum = fromAccountNum;
    }

    public String getFromRoutingNum() {
        return this.fromRoutingNum;
    }

    public void setFromRoutingNum(String fromRoutingNum) {
        this.fromRoutingNum = fromRoutingNum;
    }

    public String getToAccountNum() {
        return this.toAccountNum;
    }

    public void setToAccountNum(String toAccountNum) {
        this.toAccountNum = toAccountNum;
    }

    public String getToRoutingNum() {
        return this.toRoutingNum;
    }

    public void setToRoutingNum(String toRoutingNum) {
        this.toRoutingNum = toRoutingNum;
    }

    public Integer getAmount() {
        return this.amount;
    }

    public void setAmount(Integer amount) {
        this.amount = amount;
    }

    public String toString() {
        return String.format("%d: %s->%s",
                amount, fromAccountNum, toAccountNum);
    }
}
