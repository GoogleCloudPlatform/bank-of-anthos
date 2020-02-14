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
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.http.ResponseEntity;

import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.JWTVerifier;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import anthos.samples.financedemo.common.AuthTools;
import anthos.samples.financedemo.common.data.Balance;
import anthos.samples.financedemo.common.data.Transaction;
import anthos.samples.financedemo.common.data.TransactionRepository;

@RestController
public final class BalanceReaderController {

    private final ApplicationContext ctx =
            new AnnotationConfigApplicationContext(BalanceReaderConfig.class);

    private final String localRoutingNum;
    private final JWTVerifier verifier;
    private final Map<String, Balance> balances;
    private final TransactionRepository transactionRepository;
    private final Thread backgroundThread;

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
                                transactionRepository.pollTransactions();
                        for (Transaction transaction : transactions) {
                            processTransaction(transaction);
                        }
                    }
                }
            }
        );
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
     * Submit a new transaction to the ledger.
     *
     * @param Transaction to be submitted.
     * @return HTTP Status 200 if transaction was successfully submitted.
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

            if (balances.containsKey(initiatorAcct)) {
                return new ResponseEntity<Balance>(
                        balances.get(initiatorAcct), HttpStatus.OK);
            } else {
                // If account not found, return an empty balance.
                return new ResponseEntity<Balance>(
                        new Balance(0), HttpStatus.OK);
            }
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
