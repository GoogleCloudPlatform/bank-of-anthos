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
import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;


import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * Defines an interface for reacting to new transactions
 */
interface LedgerReaderListener {
    void processTransaction(String account, Integer amount);
}

/**
 * LedgerReader listens for incomming transactions, and executes a callback
 * on a subscribed listener object
 */
public final class LedgerReader {
    private ApplicationContext ctx =
        new AnnotationConfigApplicationContext(BalanceReaderConfig.class);
    private StatefulRedisConnection redisConnection =
        ctx.getBean(StatefulRedisConnection.class);
    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");
    private final Thread backgroundThread;
    private LedgerReaderListener listener;

    /**
     * LedgerReader constructor
     * Synchronously loads all existing transactions, and then starts
     * a background thread to listen for future transactions
     * @param listener to process transactions
     */
    public LedgerReader(LedgerReaderListener listener) {
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
        System.out.println("Starting background thread.");
        this.backgroundThread.start();
    }


    /**
     * Poll for new transactions
     * Execute callback for each one
     *
     * @param timeout the blocking time for new transactions. 0 = block forever
     * @return String id of latest transaction processed
     */
    private String pollTransactions(int timeout, String startingTransaction) {
        if (timeout < 0) {
            throw new IllegalArgumentException(
                    "pollTransactions request timeout must be non-negative");
        }
        StreamOffset offset = StreamOffset.from(ledgerStreamKey,
                                                startingTransaction);
        XReadArgs args = XReadArgs.Builder.block(Duration.ofSeconds(timeout));
        List<StreamMessage<String, String>> messages =
            redisConnection.sync().xread(args, offset);

        String latestTransactionId = startingTransaction;
        for (StreamMessage<String, String> message : messages) {
            // found a list of transactions. Execute callback for each one
            latestTransactionId = message.getId();
            Map<String, String> map = message.getBody();
            if (this.listener != null) {
                // each transaction is made up of two parts: debit and credit
                String sender = map.get("fromAccountNum");
                String senderRouting = map.get("fromRoutingNum");
                String receiver = map.get("toAccountNum");
                String receiverRouting = map.get("toRoutingNum");
                Integer amount = Integer.valueOf(map.get("amount"));
                if (senderRouting.equals(localRoutingNum)) {
                    this.listener.processTransaction(receiver, amount);
                }
                if (receiverRouting.equals(localRoutingNum)) {
                    this.listener.processTransaction(sender, -amount);
                }
            } else {
                System.out.println("Listener not set up");
            }
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
}
