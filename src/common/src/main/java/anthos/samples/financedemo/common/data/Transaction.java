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

package anthos.samples.financedemo.common.data;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Defines a banking transaction.
 */
public final class Transaction {

    // Timestamp in seconds with decimal precision.
    private Double timestamp;

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

    /**
     * Get the timestamp in seconds with decimal precision.
     */
    public Double getTimestamp() {
        return this.timestamp;
    }

    /**
     * Set the timestamp.
     *
     * @param timestamp in seconds with decimal precision.
     */
    public void setTimestamp(Double timestamp) {
        this.timestamp = timestamp;
    }

    public String toString() {
        return String.format("%d: %s->%s",
                amount, fromAccountNum, toAccountNum);
    }
}
