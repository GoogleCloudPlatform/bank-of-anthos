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
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;

import io.lettuce.core.StreamMessage;
import io.lettuce.core.XReadArgs;
import io.lettuce.core.XReadArgs.StreamOffset;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

interface LedgerReaderListener {
    void processTransaction(String account, TransactionHistoryEntry entry);
}

public final class LedgerReader {
    private ApplicationContext ctx =
        new AnnotationConfigApplicationContext(TransactionHistoryConfig.class);
    private StatefulRedisConnection redisConnection = ctx.getBean(StatefulRedisConnection.class);
    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final Thread backgroundThread;
    private LedgerReaderListener listener;

    private String pollTransactions(int timeout, String startingTransaction) {
        if (timeout < 0) {
            throw new IllegalArgumentException(
                    "pollTransactions request timeout must be non-negative");
        }
        StreamOffset offset = StreamOffset.from(ledgerStreamKey, startingTransaction);
        XReadArgs args = XReadArgs.Builder.block(Duration.ofSeconds(timeout));
        List<StreamMessage<String, String>> messages = redisConnection.sync().xread(args, offset);

        String latestTransactionId = startingTransaction;
        for (StreamMessage<String, String> message : messages) {
            latestTransactionId = message.getId();
            if (this.listener != null) {
                String sender = message.getBody().get("fromAccountNum");
                String receiver = message.getBody().get("toAccountNum");
                TransactionHistoryEntry credit = new TransactionHistoryEntry(message.getBody(), TransactionType.CREDIT);
                TransactionHistoryEntry debit = new TransactionHistoryEntry(message.getBody(), TransactionType.DEBIT);
                this.listener.processTransaction(receiver, credit);
                this.listener.processTransaction(sender, debit);
            } else {
                System.out.println("Listener not set up");
            }
        }
        return latestTransactionId;
    }

    public LedgerReader (LedgerReaderListener listener) {
        this.listener = listener;
        // catch up to latest transaction
        final String startingTransaction = pollTransactions(1, "0");

        // wait for incomming transactions in background thread
        this.backgroundThread = new Thread(
            new Runnable() {
                @Override
                public void run() {
                    String latestTransaction = startingTransaction;
                    while (true) {
                        latestTransaction = pollTransactions(0, latestTransaction);
                    }
                }
            }
        );
        System.out.println("Starting background thread to listen for transactions.");
        this.backgroundThread.start();
    }

    public boolean isAlive() {
        return this.backgroundThread.isAlive();
    }
}
