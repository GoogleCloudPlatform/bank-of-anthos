package anthos.samples.financedemo.transactionhistory;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;
import java.util.Set;
import java.util.List;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.domain.Pageable;
@Repository
public interface TransactionRepository extends CrudRepository<Transaction, Long>{

    @Query("SELECT t FROM Transaction t WHERE t.fromAccountNum=:accountNum OR t.toAccountNum=:accountNum")
    public List<Transaction> findForAccount(@Param("accountNum")String accountNum, Pageable pageable);
}
