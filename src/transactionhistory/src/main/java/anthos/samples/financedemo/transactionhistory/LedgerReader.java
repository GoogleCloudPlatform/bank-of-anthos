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

import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.RedisCommandTimeoutException;
import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

import org.springframework.context.ApplicationListener;
import org.springframework.context.event.ContextRefreshedEvent;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;
import org.springframework.stereotype.Component;

/**
 * Defines an interface for reacting to new transactions
 */
interface LedgerReaderListener {
    void processTransaction(TransactionHistoryEntry entry);
}

/**
 * LedgerReader listens for incoming transactions, and executes a callback
 * on a subscribed listener object
 */
@Component
public final class LedgerReader {

    private final Logger logger =
            Logger.getLogger(LedgerReader.class.getName());

    private ApplicationContext ctx =
        new AnnotationConfigApplicationContext(TransactionHistoryConfig.class);
    private StatefulRedisConnection redisConnection =
        ctx.getBean(StatefulRedisConnection.class);
    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");
    public LedgerReaderListener listener;
    private boolean initialized = false;

    public void startWithListener(LedgerReaderListener listener){
        this.listener = listener;
        if (!backgroundThread.isAlive()) {
            backgroundThread.start();
        }
    }

    private final Thread backgroundThread = new Thread(
            new Runnable() {
                @Override
                public void run() {
                    String latest = pollTransactions(1, "0");
                    logger.info("caught up");
                    initialized = true;
                    while (true) {
                        latest = pollTransactions(0, latest);
                    }
                }
            }
        );


    /**
     * Poll for new transactions
     * Execute callback for each one
     *
     * @param timeout the blocking time for new transactions.
     *                0 = block forever
     * @param startingTransaction the transaction to start reading after.
     *                            "0" = start reading at beginning of the ledger
     * @return String id of latest transaction processed
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
            List<StreamMessage<String, String>> messages =
                redisConnection.sync().xread(args, offset);

            for (StreamMessage<String, String> message : messages) {
                // found a list of transactions. Execute callback for each one
                latestTransactionId = message.getId();
                Map<String, String> map = message.getBody();
                if (this.listener != null) {
                    String senderRouting = map.get("fromRoutingNum");
                    String receiverRouting = map.get("toRoutingNum");
                    // create credit and debit entries for transaction
                    TransactionHistoryEntry cred = new TransactionHistoryEntry(
                            message.getBody(), TransactionType.CREDIT);
                    TransactionHistoryEntry debit = new TransactionHistoryEntry(
                            message.getBody(), TransactionType.DEBIT);
                    // process entries only if they belong to this bank
                    if (senderRouting.equals(localRoutingNum)) {
                        this.listener.processTransaction(cred);
                    }
                    if (receiverRouting.equals(localRoutingNum)) {
                        this.listener.processTransaction(debit);
                    }
                } else {
                    logger.warning("Listener not set up.");
                }
            }
        } catch (RedisCommandTimeoutException e) {
            logger.info("Redis stream read timeout.");
        }
        return latestTransactionId;
    }

    /**
     * Indicates health of LedgerReader
     * @return false if background thread dies
     */
    public boolean isAlive() {
        return this.backgroundThread.isAlive();
    }

    public boolean isInitialized() {
        return this.initialized;
    }
}
