package anthos.samples.financedemo.balancereader;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

import org.springframework.data.jpa.repository.Query;
@Repository
public interface TransactionRepository
    extends CrudRepository<Transaction, Long> {

    @Query(value = "SELECT "
        + " (SELECT SUM(AMOUNT) FROM TRANSACTIONS t WHERE TO_ACCT = ?1) - "
        + " (SELECT SUM(AMOUNT) FROM TRANSACTIONS t WHERE FROM_ACCT = ?1)",
        nativeQuery = true)
    Long findBalance(String accountId);

    @Query("SELECT t FROM Transaction t "
        + "WHERE t.transactionId > ?1 "
        + "ORDER BY t.transactionId ASC")
    List<Transaction> findLatest(long latestTransaction);

    @Query("SELECT MAX(transactionId) FROM Transaction")
    long latestId();
}
