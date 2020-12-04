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

import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import java.util.Deque;
import java.util.concurrent.TimeUnit;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.client.ResourceAccessException;


/**
 * LedgerReaderCache creates the LoadingCache that handles caching
 * and retrieving account transactions from the TransactionRepository.
 */
@Configuration
public class LedgerReaderCache {

    private static final Logger LOGGER =
        LogManager.getLogger(LedgerReaderCache.class);

    @Autowired
    private TransactionRepository dbRepo;


    /**
     * Combined cache for BalanceReader and TransactionHistory.
     *
     * @param expireSize max size of the cache
     * @param localRoutingNum bank routing number for account
     * @return the LoadingCache storing accountIds and their transactions
     */
    @Bean(name = "cache")
    public LoadingCache<String, AccountInfo> initializeCache(
        @Value("${CACHE_SIZE:1000000}") final Integer expireSize,
        @Value("${CACHE_MINUTES:60}") final Integer expireMinutes,
        @Value("${LOCAL_ROUTING_NUM}") String localRoutingNum,
        @Value("${HISTORY_LIMIT:100}") Integer historyLimit) {
        CacheLoader load = new CacheLoader<String, AccountInfo>() {
          @Override
          public AccountInfo load(String accountId)
              throws ResourceAccessException,
              DataAccessResourceFailureException  {
            LOGGER.debug("Ledger cache loaded from db");
            // Load balance
            Long balance = dbRepo.findBalance(accountId, localRoutingNum);
            if (balance == null) {
                balance = 0L;
            }
            // Load transactions
            Pageable request = PageRequest.of(0, historyLimit);
            Deque<Transaction> txns = dbRepo.findForAccount(accountId,
                localRoutingNum,
                request);

            return new AccountInfo(balance, txns);
          }
        };
      return CacheBuilder.newBuilder()
          .recordStats()
          .maximumSize(expireSize)
          .expireAfterWrite(expireMinutes, TimeUnit.MINUTES)
          .build(load);
    }
}
