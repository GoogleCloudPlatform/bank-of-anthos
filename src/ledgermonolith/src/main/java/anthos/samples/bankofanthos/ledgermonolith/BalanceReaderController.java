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

package anthos.samples.bankofanthos.ledgermonolith;

import java.io.IOException;

import java.nio.file.Files;
import java.nio.file.Paths;

import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;

import java.util.Base64;
import java.util.concurrent.ExecutionException;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.ResourceAccessException;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;

import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import com.google.common.util.concurrent.UncheckedExecutionException;

/**
 * REST service to retrieve the current balance for the authenticated user.
 */
@RestController
public final class BalanceReaderController {

    private static final Logger LOGGER =
        LogManager.getLogger(BalanceReaderController.class);

    @Autowired
    private TransactionRepository dbRepo;

    @Value("${LOCAL_ROUTING_NUM}")
    private String localRoutingNum;
    @Value("${VERSION}")
    private String version;

    private JWTVerifier verifier;
    private LoadingCache<String, Long> cache;
    private LedgerReader ledgerReader;

    /**
     * Constructor.
     *
     * Initializes JWT verifier and a connection to the bank ledger.
     */
    @Autowired
    public BalanceReaderController(LedgerReader reader,
        @Value("${PUB_KEY_PATH}") final String publicKeyPath,
        @Value("${CACHE_SIZE:1000000}") final Integer expireSize,
        @Value("${LOCAL_ROUTING_NUM}") final String localRoutingNum) {
        // Initialize JWT verifier.
        try {
            String keyStr =
                new String(Files.readAllBytes(Paths.get(publicKeyPath)));
            keyStr = keyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "")
                .replaceFirst("-----END PUBLIC KEY-----", "")
                .replaceAll("\\s", "");
            byte[] keyBytes = Base64.getDecoder().decode(keyStr);
            KeyFactory kf = KeyFactory.getInstance("RSA");
            X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(keyBytes);
            RSAPublicKey publicKey =
                (RSAPublicKey) kf.generatePublic(keySpecX509);
            Algorithm algorithm = Algorithm.RSA256(publicKey, null);
            this.verifier = JWT.require(algorithm).build();
        } catch (IOException
            | NoSuchAlgorithmException
            | InvalidKeySpecException e) {
            LOGGER.fatal(String.format("Failed initializing JWT verifier: %s",
                e.toString()));
            System.exit(1);
        }
        // Initialize cache
        CacheLoader loader =  new CacheLoader<String, Long>() {
            @Override
            public Long load(String accountId)
                throws ResourceAccessException,
                DataAccessResourceFailureException {
                LOGGER.debug("Cache loaded from db");
                Long balance = dbRepo.findBalance(accountId, localRoutingNum);
                if (balance == null) {
                    balance = 0L;
                }
                return balance;
            }
        };
        this.cache = CacheBuilder.newBuilder()
            .maximumSize(expireSize)
            .build(loader);
        // Initialize transaction processor.
        this.ledgerReader = reader;
        LOGGER.debug("Initialized transaction processor");
        this.ledgerReader.startWithCallback(transaction -> {
            final String fromId = transaction.getFromAccountNum();
            final String fromRouting = transaction.getFromRoutingNum();
            final String toId = transaction.getToAccountNum();
            final String toRouting = transaction.getToRoutingNum();
            final Integer amount = transaction.getAmount();

            if (fromRouting.equals(localRoutingNum)
                && this.cache.asMap().containsKey(fromId)) {
                Long prevBalance = cache.asMap().get(fromId);
                this.cache.put(fromId, prevBalance - amount);
            }
            if (toRouting.equals(localRoutingNum)
                && this.cache.asMap().containsKey(toId)) {
                Long prevBalance = cache.asMap().get(toId);
                this.cache.put(toId, prevBalance + amount);
            }
        });
    }

    /**
     * Liveness probe endpoint.
     *
     * @return HTTP Status 200 if server is healthy and serving requests.
     */
    @GetMapping("/healthy/balancereader")
    public ResponseEntity liveness() {
        if (!ledgerReader.isAlive()) {
            // Background thread died.
            LOGGER.error("Ledger reader not healthy");
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
                LOGGER.error("Failed to retrieve account balance: "
                    + "not authorized");
                return new ResponseEntity<String>("not authorized",
                    HttpStatus.UNAUTHORIZED);
            }
            // Load from cache
            Long balance = cache.get(accountId);
            return new ResponseEntity<Long>(balance, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            LOGGER.error("Failed to retrieve account balance: not authorized");
            return new ResponseEntity<String>("not authorized",
                HttpStatus.UNAUTHORIZED);
        } catch (ExecutionException | UncheckedExecutionException e) {
            LOGGER.error("Cache error");
            return new ResponseEntity<String>("cache error",
                HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
