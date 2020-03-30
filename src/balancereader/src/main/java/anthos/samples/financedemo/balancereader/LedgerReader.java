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

package anthos.samples.financedemo.balancereader;

import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.RedisCommandTimeoutException;
import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;


import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;
import java.lang.Iterable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * Defines an interface for reacting to new transactions
 */
interface LedgerReaderListener {
    void processTransaction(String account, Integer amount);
}

/**
 * LedgerReader listens for incoming transactions, and executes a callback
 * on a subscribed listener object
 */
@Component
public final class LedgerReader {



    private final Logger logger =
            Logger.getLogger(LedgerReader.class.getName());
    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");
    private Thread backgroundThread;
    private LedgerReaderListener listener;
    private boolean initialized = false;

    @Autowired
    private TransactionRepository transactionRepository;

    /**
     * LedgerReader constructor
     * Synchronously loads all existing transactions, and then starts
     * a background thread to listen for future transactions
     * @param listener to process transactions
     */
    public void startWithListener(LedgerReaderListener listener) {
        this.listener = listener;
        logger.info("Starting poll.");
        final long first = pollTransactions(-1);
        this.initialized = true;
        logger.info("Poll complete.");
        this.backgroundThread = new Thread(
            new Runnable() {
                @Override
                public void run() {
                    long latest = first;
                    while (true) {
                        try{
                            Thread.sleep(100);
                        } catch (InterruptedException e){}
                        latest = pollTransactions(latest);
                    }
                }
            }
        );
        logger.info("Starting background thread.");
        this.backgroundThread.start();
    }

    /**
     * Poll for new transactions
     * Execute callback for each one
     *
     * @param timeout the blocking time for new transactions.
     *                0 = block forever
     * @param startingTransaction the transaction to start reading after.
     *                            "0" = start reading at beginning of the ledger
     * @return long id of latest transaction processed
     */
    private long pollTransactions(long startingTransaction) {
        long latestTransactionId = startingTransaction;
        Iterable<Transaction> transactionList = transactionRepository.findLatest(startingTransaction);

        for (Transaction transaction : transactionList) {
            if (this.listener != null) {
                if (transaction.getFromRoutingNum().equals(localRoutingNum)) {
                    this.listener.processTransaction(transaction.getFromAccountNum(), -transaction.getAmount());
                }
                if (transaction.getToRoutingNum().equals(localRoutingNum)) {
                    this.listener.processTransaction(transaction.getToAccountNum(), transaction.getAmount());
                }
            } else {
                logger.warning("Listener not set up.");
            }
            latestTransactionId = transaction.getTransactionId();
        }
        return latestTransactionId;
    }

    /**
     * Indicates health of LedgerReader
     * @return false if background thread dies
     */
    public boolean isAlive() {
        return !this.initialized || this.backgroundThread.isAlive();
    }

    /**
     * Indicates health of LedgerReader
     * @return false if background thread dies
     */
    public boolean isInitialized() {
        return this.initialized;
    }


}
