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

import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.Table;

import org.hibernate.annotations.CreationTimestamp;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines a banking transaction.
 *
 * Timestamped at object creation time.
 */
@Entity
@Table(name = "TRANSACTIONS")
public final class Transaction {
    @Id
    @Column(name = "TRANSACTION_ID", nullable = false, updatable = false)
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private long transactionId;
    @Column(name = "FROM_ACCT", nullable = false, updatable = false)
    @JsonProperty("fromAccountNum")
    private String fromAccountNum;
    @Column(name = "FROM_ROUTE", nullable = false, updatable = false)
    @JsonProperty("fromRoutingNum")
    private String fromRoutingNum;
    @Column(name = "TO_ACCT", nullable = false, updatable = false)
    @JsonProperty("toAccountNum")
    private String toAccountNum;
    @Column(name = "TO_ROUTE", nullable = false, updatable = false)
    @JsonProperty("toRoutingNum")
    private String toRoutingNum;
    @Column(name = "AMOUNT", nullable = false, updatable = false)
    @JsonProperty("amount")
    private Integer amount;
    @Column(name = "TIMESTAMP", nullable = false, updatable = false)
    @CreationTimestamp
    @JsonProperty("timestamp")
    private Date timestamp;

    public long getTransactionId() {
        return this.transactionId;
    }

    public String getFromAccountNum() {
        return this.fromAccountNum;
    }

    public String getFromRoutingNum() {
        return this.fromRoutingNum;
    }

    public String getToAccountNum() {
        return this.toAccountNum;
    }

    public String getToRoutingNum() {
        return this.toRoutingNum;
    }

    public Integer getAmount() {
        return this.amount;
    }

    public String toString() {
        return String.format("%d: %s->%s",
                amount, fromAccountNum, toAccountNum);
    }
}
