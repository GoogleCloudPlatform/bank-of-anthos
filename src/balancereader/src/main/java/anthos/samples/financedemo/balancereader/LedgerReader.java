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

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

import io.lettuce.core.RedisCommandTimeoutException;
import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;
import io.lettuce.core.api.StatefulRedisConnection;

/**
 * Interface for processing ledger transactions.
 */
interface LedgerReaderListener {

    /**
     * Process a transaction.
     *
     * @param account  the account id of the transaction
     * @param amount   the amount of the transaction
     */
    void processTransaction(String account, Integer amount);

}

/**
 * Reader for new and existing ledger transactions.
 *
 * Executes a callback on a subscribed listener object.
 */
public final class LedgerReader {

    private static final Logger LOGGER =
            Logger.getLogger(LedgerReader.class.getName());

    private final ApplicationContext ctx;
    private final Thread backgroundThread;
    private final LedgerReaderListener listener;

    @Value("${ledger.stream}")
    private String ledgerStreamKey;
    @Value("${LOCAL_ROUTING_NUM}")
    private String localRoutingNum;

    /**
     * Constructor.
     *
     * Synchronously loads all existing transactions, and then starts
     * a background thread to listen for future transactions.
     *
     * @param listener  callback client to process transactions
     */
    public LedgerReader(LedgerReaderListener listener) {
        this.ctx = new AnnotationConfigApplicationContext(
                BalanceReaderConfig.class);
        this.listener = listener;
        // read from starting transaction to latest
        final String startingTransaction = pollTransactions(1, "0");

        // set up background thread to listen for incomming transactions
        this.backgroundThread = new Thread(
            new Runnable() {
                @Override
                public void run() {
                    String latest = startingTransaction;
                    while (true) {
                        latest = pollTransactions(0, latest);
                    }
                }
            }
        );
        LOGGER.info("Starting background thread.");
        this.backgroundThread.start();
    }

    /**
     * Poll for transactions.
     *
     * Execute callback for each new transaction.
     *
     * @param timeout              the blocking time for new transactions
     *                             0 = block forever
     * @param startingTransaction  the transaction to start reading after
     *                             "0" = start at the beginning of the ledger
     * @return                     the id of the latest transaction processed
     */
    private String pollTransactions(int timeout, String startingTransaction) {
        if (timeout < 0) {
            throw new IllegalArgumentException(
                    "pollTransactions request timeout must be non-negative");
        }
        String latestTransactionId = startingTransaction;
        StreamOffset offset = StreamOffset.from(ledgerStreamKey,
                                                startingTransaction);
        XReadArgs args = XReadArgs.Builder.block(Duration.ofSeconds(timeout));
        try {
            StatefulRedisConnection redisConnection =
                    ctx.getBean(StatefulRedisConnection.class);
            List<StreamMessage<String, String>> messages =
                redisConnection.sync().xread(args, offset);

            for (StreamMessage<String, String> message : messages) {
                // found a list of transactions. Execute callback for each one
                latestTransactionId = message.getId();
                Map<String, String> map = message.getBody();
                if (listener != null) {
                    // each transaction is made up of a debit and a credit
                    String sender = map.get("fromAccountNum");
                    String senderRouting = map.get("fromRoutingNum");
                    String receiver = map.get("toAccountNum");
                    String receiverRouting = map.get("toRoutingNum");
                    Integer amount = Integer.valueOf(map.get("amount"));
                    if (senderRouting.equals(localRoutingNum)) {
                        listener.processTransaction(sender, -amount);
                    }
                    if (receiverRouting.equals(localRoutingNum)) {
                        listener.processTransaction(receiver, amount);
                    }
                } else {
                    LOGGER.warning("Listener not set up.");
                }
            }
        } catch (RedisCommandTimeoutException e) {
            LOGGER.info("Redis stream read timeout.");
        }
        return latestTransactionId;
    }

    /**
     * Returns whether the transaction listener is active.
     *
     * @return  true if currently listening for transactions
     */
    public boolean isAlive() {
        return this.backgroundThread.isAlive();
    }
}
