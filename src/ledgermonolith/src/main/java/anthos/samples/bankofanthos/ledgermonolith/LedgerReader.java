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


import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;

/**
 * Defines an interface for reacting to new transactions
 *
 * @param accountId    the account associated with the transaction
 * @param amount       the amount of change in balance for the account
 * @param transaction  the full transaction object
 */
interface LedgerReaderCallback {
    void processTransaction(Transaction transaction);
}

/**
 * LedgerReader listens for and reacts to incoming transactions
 */
@Component
public final class LedgerReader {

    private static final Logger LOGGER =
        LogManager.getLogger(LedgerReader.class);
    private static final long STARTING_TRANSACTION_ID = -1;

    @Autowired
    private TransactionRepository dbRepo;

    @Value("${POLL_MS:100}")
    private Integer pollMs;
    @Value("${LOCAL_ROUTING_NUM}")
    private String localRoutingNum;

    private Thread backgroundThread;
    private LedgerReaderCallback callback;
    private long latestTransactionId;

    /**
     * LedgerReader setup
     * Synchronously loads all existing transactions, and then starts
     * a background thread to listen for future transactions
     *
     * @param callback to process transactions
     * @throws IllegalStateException if callback is null
     */
    public void startWithCallback(LedgerReaderCallback callback)
        throws IllegalStateException {
        if (callback == null) {
            throw new IllegalStateException("callback is null");
        }
        this.callback = callback;
        this.latestTransactionId = STARTING_TRANSACTION_ID;
        // get the latest transaction id in ledger
        try {
            latestTransactionId = getLatestTransactionId();
            LOGGER.debug(String.format("Transaction starting id: %d",
                latestTransactionId));
        } catch (ResourceAccessException
            | DataAccessResourceFailureException e) {
            LOGGER.warn("Could not contact ledger database at init");
        }
        this.backgroundThread = new Thread(new Runnable() {
            @Override
            public void run() {
                boolean alive = true;
                while (alive) {
                    // sleep between polls
                    try {
                        Thread.sleep(pollMs);
                    } catch (InterruptedException e) {
                        LOGGER.warn("LedgerReader sleep interrupted");
                    }
                    // check for new updates in ledger
                    Long remoteLatest = STARTING_TRANSACTION_ID;
                    try {
                        remoteLatest = getLatestTransactionId();
                    } catch (ResourceAccessException
                        | DataAccessResourceFailureException e) {
                        remoteLatest = latestTransactionId;
                        LOGGER.warn("Could not reach ledger database");
                    }
                    // if there are new transactions, poll the database
                    if (remoteLatest > latestTransactionId) {
                        latestTransactionId =
                                pollTransactions(latestTransactionId);
                    } else if (remoteLatest < latestTransactionId) {
                        // remote database out of sync
                        // suspend processing transactions to reset service
                        alive = false;
                        LOGGER.error("Remote transaction id out of sync");
                    }
                }
            }
        });
        LOGGER.info("Starting background thread.");
        this.backgroundThread.start();
    }

    /**
     * Poll for new transactions
     * Execute callback for each one
     *
     * @param startingId the transaction to start reading after.
     *                            -1 = start reading at beginning of the ledger
     * @return long id of latest transaction processed
     */
    private long pollTransactions(long startingId) {
        long latestId = startingId;
        Iterable<Transaction> transactionList = dbRepo.findLatest(startingId);
        LOGGER.debug("Polling Transactions");
        for (Transaction transaction : transactionList) {
            callback.processTransaction(transaction);
            latestId = transaction.getTransactionId();
        }
        LOGGER.debug("New transaction(s) found - polled DB: "
        + "latest txnID is now: " + latestId);
        return latestId;
    }

    /**
     * Indicates health of LedgerReader
     * @return false if background thread dies
     */
    public boolean isAlive() {
        return backgroundThread == null || backgroundThread.isAlive();
    }

    /**
     * Returns the id of the most recent transaction.
     *
     * @return the transaction id as a long or -1 if no transactions exist
     */
    private long getLatestTransactionId() {
        Long latestId = dbRepo.latestTransactionId();
        if (latestId == null) {
            return STARTING_TRANSACTION_ID;
        }
        return latestId;
    }
}
