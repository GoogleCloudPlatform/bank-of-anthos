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
    @GeneratedValue(strategy=GenerationType.AUTO)
    private long transactionId;

    @JsonProperty("accountNum")
    @Column (name="SEND_ACCT")
    private String accountNum;

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
}
