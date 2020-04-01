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

package anthos.samples.financedemo.transactionhistory;

import java.util.logging.Logger;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Defines an interface for reacting to new transactions
 */
interface LedgerReaderListener {
    void processTransaction(String accountId, Transaction transaction);
}

/**
 * LedgerReader listens for incoming transactions, and executes a callback
 * on a subscribed listener object
 */
@Component
public final class LedgerReader {
    private final Logger logger =
            Logger.getLogger(LedgerReader.class.getName());
    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");
    private Thread backgroundThread;
    private LedgerReaderListener listener;
    private long latestId = -1;

    @Autowired
    private TransactionRepository dbRepo;

    @Value("${POLL_MS:100}")
    private Integer pollMs;

    /**
     * LedgerReader setup
     * Synchronously loads all existing transactions, and then starts
     * a background thread to listen for future transactions
     * @param listener to process transactions
     */
    public void startWithListener(LedgerReaderListener listener) {
        this.listener = listener;
        // get the latest transaction id in ledger
        this.latestId = dbRepo.latestId();
        logger.info(String.format("starting id: %d", this.latestId));
        this.backgroundThread = new Thread(
            new Runnable() {
                @Override
                public void run() {
                    while (true) {
                        try {
                            Thread.sleep(pollMs);
                        } catch (InterruptedException e) { }
                            latestId = pollTransactions(latestId);
                    }
                }
            });
        logger.info("Starting background thread.");
        this.backgroundThread.start();
    }

    /**
     * Poll for new transactions
     * Execute callback for each one
     *
     * @param startingTransaction the transaction to start reading after.
     *                            -1 = start reading at beginning of the ledger
     * @return long id of latest transaction processed
     */
    private long pollTransactions(long startingId) {
        long latestId = startingId;
        Iterable<Transaction> transactionList = dbRepo.findLatest(startingId);

        for (Transaction transaction : transactionList) {
            if (listener != null) {
                if (transaction.getFromRoutingNum().equals(localRoutingNum)) {
                    listener.processTransaction(transaction.getFromAccountNum(),
                                                transaction);
                }
                if (transaction.getToRoutingNum().equals(localRoutingNum)) {
                    listener.processTransaction(transaction.getToAccountNum(),
                                                transaction);
                }
            } else {
                logger.warning("Listener not set up.");
            }
            latestId = transaction.getTransactionId();
        }
        return latestId;
    }

    /**
     * Indicates health of LedgerReader
     * @return false if background thread dies
     */
    public boolean isAlive() {
        return backgroundThread == null || backgroundThread.isAlive();
    }
}
