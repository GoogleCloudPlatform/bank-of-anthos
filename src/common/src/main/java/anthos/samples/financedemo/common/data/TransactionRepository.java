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

package anthos.samples.financedemo.common.data;

import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.logging.Logger;

/**
 * Transaction repository for the bank ledger.
 */
public final class TransactionRepository {

    private static final double MILLISECONDS_PER_SECOND = 1000.0;
    private static final String READ_STREAM_START_ID = "0";

    private final String ledgerStreamKey;
    private final StatefulRedisConnection redisConnection;

    private String streamOffset;

    /**
     * Constructor.
     *
     * @param redisConnection a connection to the repository Redis database.
     * @param ledgerStreamKey the Redis stream key for the bank ledger.
     */
    public TransactionRepository(StatefulRedisConnection redisConnection,
            String ledgerStreamKey) {
        this.redisConnection = redisConnection;
        this.ledgerStreamKey = ledgerStreamKey;
        this.streamOffset = READ_STREAM_START_ID;
    }

    /**
     * Submit the given transaction to the repository.
     */
    public void submitTransaction(Transaction transaction) {
        timestampTransaction(transaction);
        redisConnection.async().xadd(ledgerStreamKey, serialize(transaction));
    }

    /**
     * Poll the repository for new transactions since last called.
     *
     * Blocking operation.
     * Will return each new transaction only once.
     * 
     * @param timeout number of seconds to block before request timeout.
     */
    public List<Transaction> pollTransactions(int timeout) {
        if (timeout < 0) {
            throw new IllegalArgumentException(
                    "pollTransactions request timeout must be non-negative");
        }
        StreamOffset offset =
                StreamOffset.from(ledgerStreamKey, streamOffset);
        XReadArgs args = XReadArgs.Builder.block(Duration.ofSeconds(timeout));
        List<StreamMessage<String, String>> messages =
                redisConnection.sync().xread(args, offset);

        List<Transaction> transactions = new ArrayList<Transaction>();
        for (StreamMessage<String, String> message : messages) {
            streamOffset = message.getId();
            transactions.add(deserialize(message.getBody()));
        }
        return transactions;
    }

    /**
     * Timestamps the given Transaction with the current system time.
     *
     * Uses the UNIX Timestamp in seconds with decimal precision.
     */
    private static void timestampTransaction(Transaction transaction) {
        double timestamp = System.currentTimeMillis() / MILLISECONDS_PER_SECOND;
        transaction.setTimestamp(timestamp);
    }

    /**
     * Serialize a Transaction for Redis data formatting.
     *
     * @param transaction to be serialized.
     * @return a Map containing the fields/values of the Transaction object.
     */
    private static Map<String, String> serialize(Transaction transaction) {
        Map<String, String> map = new HashMap<String, String>();
        map.put("fromAccountNum", transaction.getFromAccountNum());
        map.put("fromRoutingNum", transaction.getFromRoutingNum());
        map.put("toAccountNum", transaction.getToAccountNum());
        map.put("toRoutingNum", transaction.getToRoutingNum());
        map.put("amount", transaction.getAmount().toString());
        map.put("timestamp", Double.toString(transaction.getTimestamp()));
        return map;
    }

    /**
     * Deserialize a Transaction from Redis data formatting.
     *
     * The given Map must contain the following keys with values to be parsed as
     * indicated:
     *     "fromAccountNum" : string
     *     "fromRoutingNum" : string
     *     "toAccountNum" : string
     *     "toRoutingNum" : string
     *     "amount" : int
     *     "timestamp" : float
     *
     * @param the Redis data body as a key/value Map.
     * @return a Transaction object matching the values of the Map.
     */
    private static Transaction deserialize(Map<String, String> map) {
        Transaction transaction = new Transaction();
        transaction.setFromAccountNum(map.get("fromAccountNum"));
        transaction.setFromRoutingNum(map.get("fromRoutingNum"));
        transaction.setToAccountNum(map.get("toAccountNum"));
        transaction.setToRoutingNum(map.get("toRoutingNum"));
        transaction.setAmount(Integer.valueOf(map.get("amount")));
        transaction.setTimestamp(Double.valueOf(map.get("timestamp")));
        return transaction;
    }
}
