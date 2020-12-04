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

package anthos.samples.bankofanthos.ledgermonolith;

import java.util.Deque;


/**
 * Defines the account Info object used for the LedgerReaderCache
 */
public class AccountInfo {
  Long balance;
  Deque<Transaction> transactions;

  // Constructor
  public AccountInfo(Long balance,
    Deque<Transaction> transactions) {
        this.balance = balance;
        this.transactions = transactions;
    }

// Getters
  public Deque<Transaction> getTransactions() {
    return transactions;
  }

  public Long getBalance() {
    return balance;
  }
}
