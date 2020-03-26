package anthos.samples.financedemo.transactionhistory;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TransactionRepository extends CrudRepository<TransactionHistoryEntry, Long>{

}
