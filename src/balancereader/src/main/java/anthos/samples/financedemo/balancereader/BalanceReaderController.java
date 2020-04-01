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
import java.util.concurrent.ExecutionException;
import java.util.logging.Logger;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationListener;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;

import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;

@RestController
public final class BalanceReaderController implements LedgerReaderListener,
       ApplicationListener<ContextRefreshedEvent> {

    private final Logger logger =
            Logger.getLogger(BalanceReaderController.class.getName());

    private JWTVerifier verifier;

    private LoadingCache<String, Long> cache;

    @Autowired
    private LedgerReader reader;

    @Autowired
    private TransactionRepository dbRepo;

    @Value("${CACHE_SIZE:1000000}")
    private long expireSize;
    @Value("${LOCAL_ROUTING_NUM}")
    private String localRoutingNum;

    /**
     * BalanceReaderController initialization
     */
    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        try {
            // load public key from file
            String fPath = System.getenv("PUB_KEY_PATH");
            String keyStr  = new String(Files.readAllBytes(Paths.get(fPath)));
            keyStr = keyStr.replaceFirst("-----BEGIN PUBLIC KEY-----", "")
                           .replaceFirst("-----END PUBLIC KEY-----", "")
                           .replaceAll("\\s", "");
            byte[] keyBytes = Base64.getDecoder().decode(keyStr);
            KeyFactory kf = KeyFactory.getInstance("RSA");
            X509EncodedKeySpec keySpecX509 = new X509EncodedKeySpec(keyBytes);
            RSAPublicKey publicKey =
                (RSAPublicKey) kf.generatePublic(keySpecX509);
            // set up verifier
            Algorithm algorithm = Algorithm.RSA256(publicKey, null);
            this.verifier = JWT.require(algorithm).build();
        } catch (IOException
                | NoSuchAlgorithmException
                | InvalidKeySpecException e) {
            logger.warning(e.toString());
            System.exit(1);
        }
        // set up cache
        CacheLoader loader =  new CacheLoader<String, Long>() {
            @Override
            public Long load(String accountId) {
                logger.info("loaded from db");
                Long balance = dbRepo.findBalance(accountId, localRoutingNum);
                if (balance == null) {
                    balance = 0L;
                }
                return balance;
            }
        };
        cache = CacheBuilder.newBuilder()
                            .maximumSize(expireSize)
                            .build(loader);
        // start background ledger reader
        this.reader.startWithListener(this);
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
     * @return HTTP Status 200 if server is initialized and serving requests.
     */
    @GetMapping("/ready")
    @ResponseStatus(HttpStatus.OK)
    public String readiness() {
        return "ok";
    }

    /**
     * Liveness probe endpoint.
     *
     * @return HTTP Status 200 if server is healthy.
     */
    @GetMapping("/healthy")
    public ResponseEntity liveness() {
        if (!this.reader.isAlive()) {
            // background thread died. Abort
            return new ResponseEntity<String>("LedgerReader not healthy",
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return new ResponseEntity<String>("ok", HttpStatus.OK);
    }

    /**
     * Return the balance for the specified account.
     *
     * The currently authenticated user must be allowed to access the account.
     *
     * @param accountId the account to get the balance for.
     * @return the balance amount.
     */
    @GetMapping("/balances/{accountId}")
    public ResponseEntity<?> getBalance(
            @RequestHeader("Authorization") String bearerToken,
            @PathVariable String accountId) {
        logger.info("request from: " + accountId);
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

            // Load from cache
            Long balance = cache.get(accountId);

            return new ResponseEntity<Long>(balance, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        } catch (ExecutionException e) {
            return new ResponseEntity<String>("cache error",
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Receives transactions from LedgerReader for processing
     * Update balance in internal Map
     *
     * @param account associated with the transaction
     * @param entry with transaction metadata
     */
    public void processTransaction(String accountId, Integer amount) {
        if (cache.asMap().containsKey(accountId)) {
            logger.info("modifying cache: " + accountId);
            Long prevBalance = cache.asMap().get(accountId);
            cache.put(accountId, prevBalance + amount);
        }
    }
}
