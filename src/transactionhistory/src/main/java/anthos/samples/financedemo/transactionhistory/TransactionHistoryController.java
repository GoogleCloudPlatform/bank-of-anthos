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

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.List;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import java.util.logging.Logger;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.PathVariable;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;

/**
 * Controller for the TransactionHistory service.
 *
 * Functions to show the transaction history for each user account.
 */
@RestController
public final class TransactionHistoryController
        implements LedgerReaderListener {

    private static final Logger logger =
            Logger.getLogger(TransactionHistoryController.class.getName());

    private final Map<String, List<TransactionHistoryEntry>> historyMap;
    private final LedgerReader reader;
    private final JWTVerifier verifier;
    private final boolean initialized;

    /**
     * Constructor.
     *
     * Initializes a connection to the bank ledger.
     */
    public TransactionHistoryController() throws IOException,
                                           NoSuchAlgorithmException,
                                           InvalidKeySpecException {
        this.historyMap = new HashMap<String, List<TransactionHistoryEntry>>();

        // Initialize transaction processor.
        this.reader = new LedgerReader(this);

        // Initialize JWT verifier.
        String fPath = System.getenv("PUB_KEY_PATH");
        String pubKeyStr  = new String(Files.readAllBytes(Paths.get(fPath)));
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
        logger.info("Initialization complete.");
    }

   /**
     * Version endpoint.
     *
     * @return service version string
     */
    @GetMapping("/version")
    public ResponseEntity version() {
        final String versionStr =  System.getenv("VERSION");
        return new ResponseEntity<String>(versionStr, HttpStatus.OK);
    }

    /**
     * Readiness probe endpoint.
     *
     * @return HTTP Status 200 if server is ready to recieve requests.
     */
    @GetMapping("/ready")
    public ResponseEntity readiness() {
        if (this.initialized) {
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
        if (this.initialized && !this.reader.isAlive()) {
            // background thread died. Abort
            return new ResponseEntity<String>("LedgerReader not healthy",
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return new ResponseEntity<String>("ok", HttpStatus.OK);
    }

    /**
     * Return a list of transactions for the specified account.
     *
     * The currently authenticated user must be allowed to access the account.
     *
     * @param bearerToken  HTTP request 'Authorization' header
     * @param accountId    the account to get transactions for.
     * @return             a list of transactions for this account.
     */
    @GetMapping("/transactions/{accountId}")
    public ResponseEntity<?> getTransactions(
            @RequestHeader("Authorization") String bearerToken,
            @PathVariable String accountId) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken = bearerToken.split("Bearer ")[1];
        }
        try {
            DecodedJWT jwt = this.verifier.verify(bearerToken);
            // Check that the authenticated user can access this account.
            if (!accountId.equals(jwt.getClaim("acct").asString())) {
                return new ResponseEntity<String>("not authorized",
                                                  HttpStatus.UNAUTHORIZED);
            }

            List<TransactionHistoryEntry> historyList;
            if (this.historyMap.containsKey(accountId)) {
                historyList = this.historyMap.get(accountId);
            } else {
                historyList = new LinkedList<TransactionHistoryEntry>();
            }

            // Set artificial extra latency.
            String latency = System.getenv("EXTRA_LATENCY_MILLIS");
            if (latency != null) {
                try {
                    Thread.sleep(Integer.parseInt(latency));
                } catch (InterruptedException e) {
                    // Fake latency interrupted. Continue.
                }
            }

            return new ResponseEntity<List<TransactionHistoryEntry>>(
                    historyList, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * Appends a transaction to the account history.
     *
     * @param account  the account id of the transaction
     * @param entry    the transaction metadata to append to the history
     */
    public void processTransaction(String account,
                                   TransactionHistoryEntry entry) {
        LinkedList<TransactionHistoryEntry> historyList;
        if (!this.historyMap.containsKey(account)) {
            historyList = new LinkedList<TransactionHistoryEntry>();
            this.historyMap.put(account, historyList);
        } else {
            historyList = (LinkedList) this.historyMap.get(account);
        }
        historyList.addFirst(entry);
    }
}
