package anthos.samples.financedemo.transactionhistory;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.Set;

@Repository
public interface TransactionRepository extends CrudRepository<TransactionHistoryEntry, Long>{
    Set<TransactionHistoryEntry> findAllByKeyAccountNum(String keyAccountNum);
}
