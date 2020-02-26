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

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.http.ResponseEntity;

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
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.LinkedList;

@RestController
public final class BalanceReaderController implements LedgerReaderListener {

    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final String routingNum =  System.getenv("LOCAL_ROUTING_NUM");
    private final JWTVerifier verifier;
    private final Map<String, List<TransactionHistoryEntry>> historyMap =
        new HashMap<String, List<TransactionHistoryEntry>>();
    private final LedgerReader reader;
    private boolean initialized = false;

    /**
     * BalanceReaderController constructor
     * Set up JWT verifier, initialize LedgerReader
     */
    public BalanceReaderController() throws IOException,
                                           NoSuchAlgorithmException,
                                           InvalidKeySpecException {
        // load public key from file
        String fPath = System.getenv("PUB_KEY_PATH");
        String pubKeyStr  = new String(Files.readAllBytes(Paths.get(fPath)));
        pubKeyStr = pubKeyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "");
        pubKeyStr = pubKeyStr.replaceFirst("-----END PUBLIC KEY-----", "");
        pubKeyStr = pubKeyStr.replaceAll("\\s", "");
        byte[] pubKeyBytes = Base64.getDecoder().decode(pubKeyStr);
        KeyFactory kf = KeyFactory.getInstance("RSA");
        X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(pubKeyBytes);
        RSAPublicKey publicKey = (RSAPublicKey) kf.generatePublic(keySpecX509);
        // set up verifier
        Algorithm algorithm = Algorithm.RSA256(publicKey, null);
        this.verifier = JWT.require(algorithm).build();

        // set up transaction processor
        this.reader = new LedgerReader(this);
        this.initialized = true;
        System.out.println("initialization complete");
    }

    /**
     * Readiness probe endpoint.
     *
     * @return HTTP Status 200 if server is initialized and serving requestsi.
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
     * @return HTTP Status 200 if server is healthy.
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
     * Return the balance for the requesting user
     */
    @GetMapping("/get_balance")
    public ResponseEntity<?> getHistory(
            @RequestHeader("Authorization") String bearerToken) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken = bearerToken.split("Bearer ")[1];
        }
        try {
            DecodedJWT jwt = this.verifier.verify(bearerToken);
            String initiatorAcct = jwt.getClaim("acct").asString();
            //List<TransactionHistoryEntry> historyList;
            //if (this.historyMap.containsKey(initiatorAcct)) {
            //    historyList = this.historyMap.get(initiatorAcct);
            //} else {
            //    historyList = new LinkedList<TransactionHistoryEntry>();
            //}
            return new ResponseEntity<Integer>(10, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        }
    }

    /**
     * Receives transactions from LedgerReader for processing
     * Add transaction records to internal Map
     *
     * @param account associated with the transaction
     * @param entry with transaction metadata
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
