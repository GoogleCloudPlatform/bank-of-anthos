// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package anthos.samples.financedemo.transactionhistory;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.LinkedList;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.domain.Pageable;
@Repository
public interface TransactionRepository
        extends CrudRepository<Transaction, Long> {

    @Query("SELECT MAX(transactionId) FROM Transaction")
    long latestId();

    @Query("SELECT t FROM Transaction t "
        + "WHERE t.fromAccountNum=?1 OR t.toAccountNum=?1"
        + "ORDER BY t.timestamp DESC")
    LinkedList<Transaction> findForAccount(String accountNum, Pageable pager);

    @Query("SELECT t FROM Transaction t "
        + "WHERE t.transactionId > ?1 ORDER BY t.transactionId ASC")
    List<Transaction> findLatest(long latestTransaction);
}
