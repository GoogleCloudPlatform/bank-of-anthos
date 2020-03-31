package anthos.samples.financedemo.transactionhistory;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

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
    List<Transaction> findForAccount(String accountNum, Pageable pager);

    @Query("SELECT t FROM Transaction t "
        + "WHERE t.transactionId > ?1 ORDER BY t.transactionId ASC")
    List<Transaction> findLatest(long latestTransaction);
}
