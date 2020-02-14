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

import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.JWTVerifier;
import io.lettuce.core.api.StatefulRedisConnection;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.http.ResponseEntity;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;

import anthos.samples.financedemo.common.AuthTools;
import anthos.samples.financedemo.common.data.Balance;
import anthos.samples.financedemo.common.data.Transaction;
import anthos.samples.financedemo.common.data.TransactionRepository;

/**
 * Controller for the BalanceReader service.
 *
 * Functions to track the bank balance for each user account.
 */
@RestController
public final class BalanceReaderController {

    private static final int POLL_TRANSACTIONS_TIMEOUT = 10;

    private final ApplicationContext ctx =
            new AnnotationConfigApplicationContext(BalanceReaderConfig.class);
    private final Logger logger =
            Logger.getLogger(BalanceReaderController.class.getName());

    private final String localRoutingNum;
    private final JWTVerifier verifier;
    private final Map<String, Balance> balances;
    private final TransactionRepository transactionRepository;
    private final Thread backgroundThread;

    /**
     * Constructor.
     *
     * Opens a connection to the transaction repository for the bank ledger.
     * Starts background thread to poll for new transactions.
     */
    public BalanceReaderController() {
        this.localRoutingNum = System.getenv("LOCAL_ROUTING_NUM");
        this.verifier =
                AuthTools.newJWTVerifierFromFile(System.getenv("PUB_KEY_PATH"));
        this.balances = new HashMap<String, Balance>();
        this.transactionRepository = new TransactionRepository(
                ctx.getBean(StatefulRedisConnection.class),
                System.getenv("LEDGER_STREAM"));

        backgroundThread = new Thread(
            new Runnable() {
                @Override
                public void run() {
                    while (true) {
                        List<Transaction> transactions =
                                transactionRepository.pollTransactions(
                                    POLL_TRANSACTIONS_TIMEOUT);

                        if (!transactions.isEmpty()) {
                            logger.info(String.format(
                                    "%d transaction(s) polled from repository.",
                                    transactions.size()));
                        }
                        for (Transaction transaction : transactions) {
                            processTransaction(transaction);
                        }
                    }
                }
            }
        );
        logger.info("Starting background thread to listen for transactions.");
        backgroundThread.start();
    }

    /**
     * Readiness probe endpoint.
     *
     * @return HTTP Status 200 if server can be reached.
     */
    @GetMapping("/ready")
    @ResponseStatus(HttpStatus.OK)
    public String readiness() {
        return "ok";
    }

    /**
     * Liveness probe endpoint.
     *
     * @return HTTP Status 200 if server is serving requests.
     */
    @GetMapping("/healthy")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<String> liveness() {
        if (backgroundThread.isAlive()) {
            return new ResponseEntity<String>("ok", HttpStatus.OK);
        } else {
            return new ResponseEntity<String>("unable to serve requests",
                    HttpStatus.SERVICE_UNAVAILABLE);
        }
    }

    /**
     * Get the account balance for the currently authorized account.
     *
     * @return Balance JSON object if balance was successfully retrieved.
     */
    @GetMapping("/get_balance")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<?> getBalance(
            @RequestHeader("Authorization") String bearerToken) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken = bearerToken.split("Bearer ")[1];
        }
        try {
            DecodedJWT jwt = this.verifier.verify(bearerToken);
            String initiatorAcct = jwt.getClaim("acct").asString();

            // If account not found, return an empty balance.
            Balance balance = (balances.containsKey(initiatorAcct)
                    ? balances.get(initiatorAcct) : new Balance(0));
            return new ResponseEntity<Balance>(balance, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                    HttpStatus.UNAUTHORIZED);
        }
    }

    private void processTransaction(Transaction transaction) {
        if (transaction.getFromRoutingNum().equals(localRoutingNum)) {
            // Subtract amount from FromAccount only if it is a local account.
            int amount = transaction.getAmount() * -1;
            adjustBalance(transaction.getFromAccountNum(), amount);
        }
        if (transaction.getToRoutingNum().equals(localRoutingNum)) {
            // Add amount to ToAccount only if it is a local account.
            int amount = transaction.getAmount();
            adjustBalance(transaction.getToAccountNum(), amount);
        }
    }

    private void adjustBalance(String account, int amount) {
        if (balances.containsKey(account)) {
            Balance balance = balances.get(account);
            balance.setAmount(balance.getAmount() + amount);
        } else {
            balances.put(account, new Balance(amount));
        }
    }
}
