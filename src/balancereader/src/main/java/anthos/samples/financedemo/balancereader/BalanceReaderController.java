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

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;

/**
 * Controller for the BalanceReader service.
 *
 * Functions to track the bank balance for each user account.
 */
@RestController
public final class BalanceReaderController {

    private static final Logger LOGGER =
            Logger.getLogger(BalanceReaderController.class.getName());

    private final String version = System.getenv("VERSION");
    private final String pubKeyPath = System.getenv("PUB_KEY_PATH");
    private final String localRoutingNum = System.getenv("LOCAL_ROUTING_NUM");

    private final Map<String, AtomicInteger> balanceMap;
    private final LedgerReader reader;
    private final JWTVerifier verifier;
    private final boolean initialized;

    /**
     * Constructor.
     *
     * Initializes a connection to the bank ledger.
     */
    public BalanceReaderController() throws IOException,
                                           NoSuchAlgorithmException,
                                           InvalidKeySpecException {
        this.balanceMap = new ConcurrentHashMap<String, AtomicInteger>();

        // Initialize transaction reader.
        this.reader = new LedgerReader() {
            @Override
            void processTransaction(Map<String, String> transaction) {
                // Each transaction is made up of a debit and a credit.
                String sender = transaction.get("fromAccountNum");
                String senderRouting = transaction.get("fromRoutingNum");
                String receiver = transaction.get("toAccountNum");
                String receiverRouting = transaction.get("toRoutingNum");
                Integer amount = Integer.valueOf(transaction.get("amount"));
                // Update an account balance only if it is a local account.
                if (senderRouting.equals(localRoutingNum)) {
                    // Debit the sender.
                    updateBalance(sender, amount * -1);
                }
                if (receiverRouting.equals(localRoutingNum)) {
                    // Credit the receiver.
                    updateBalance(receiver, amount);
                }
            }
        };

        // Initialize JWT verifier.
        String pubKeyStr =
                new String(Files.readAllBytes(Paths.get(pubKeyPath)));
        pubKeyStr = pubKeyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "");
        pubKeyStr = pubKeyStr.replaceFirst("-----END PUBLIC KEY-----", "");
        pubKeyStr = pubKeyStr.replaceAll("\\s", "");
        byte[] pubKeyBytes = Base64.getDecoder().decode(pubKeyStr);
        KeyFactory kf = KeyFactory.getInstance("RSA");
        X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(pubKeyBytes);
        RSAPublicKey publicKey = (RSAPublicKey) kf.generatePublic(keySpecX509);
        Algorithm algorithm = Algorithm.RSA256(publicKey, null);
        this.verifier = JWT.require(algorithm).build();

        this.initialized = true;
        LOGGER.info("Initialization complete.");
    }

    /**
     * Version endpoint.
     *
     * @return  service version string
     */
    @GetMapping("/version")
    public ResponseEntity version() {
        return new ResponseEntity<String>(version, HttpStatus.OK);
    }

    /**
     * Readiness probe endpoint.
     *
     * @return HTTP Status 200 if server is ready to receive requests.
     */
    @GetMapping("/ready")
    public ResponseEntity readiness() {
        if (initialized) {
            return new ResponseEntity<String>("ok", HttpStatus.OK);
        } else {
            return new ResponseEntity<String>("not initialized",
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Liveness probe endpoint.
     *
     * @return HTTP Status 200 if server is healthy and serving requests.
     */
    @GetMapping("/healthy")
    public ResponseEntity liveness() {
        if (initialized && !reader.isAlive()) {
            // Background thread died.
            return new ResponseEntity<String>("Ledger reader not healthy",
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return new ResponseEntity<String>("ok", HttpStatus.OK);
    }

    /**
     * Return the balance for the specified account.
     *
     * The currently authenticated user must be allowed to access the account.
     *
     * @param bearerToken  HTTP request 'Authorization' header
     * @param accountId    the account to get the balance for
     * @return             the balance of the account
     */
    @GetMapping("/balances/{accountId}")
    public ResponseEntity<?> getBalance(
            @RequestHeader("Authorization") String bearerToken,
            @PathVariable String accountId) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken = bearerToken.split("Bearer ")[1];
        }
        try {
            DecodedJWT jwt = verifier.verify(bearerToken);
            // Check that the authenticated user can access this account.
            if (!accountId.equals(jwt.getClaim("acct").asString())) {
                return new ResponseEntity<String>("not authorized",
                                                  HttpStatus.UNAUTHORIZED);
            }

            Integer balance = balanceMap
                    .getOrDefault(accountId, new AtomicInteger(0))
                    .get();
            return new ResponseEntity<Integer>(balance, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * Update the balance for an account.
     *
     * @param account  the account id of the transaction
     * @param amount   the amount of the transaction
     */
    private void updateBalance(String account, Integer amount) {
        balanceMap.putIfAbsent(account, new AtomicInteger());
        balanceMap.get(account).getAndAdd(amount);
    }
}
