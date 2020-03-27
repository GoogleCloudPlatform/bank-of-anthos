package anthos.samples.financedemo.transactionhistory;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.Set;
import java.util.List;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.domain.Pageable;
@Repository
public interface TransactionRepository extends CrudRepository<TransactionHistoryEntry, Long>{

    @Query("SELECT t FROM TransactionHistoryEntry t WHERE t.keyAccountNum=:accountNum ORDER BY t.timestamp DESC")
    public List<TransactionHistoryEntry> findForAccount(@Param("accountNum")String accountNum, Pageable pageable);
}
