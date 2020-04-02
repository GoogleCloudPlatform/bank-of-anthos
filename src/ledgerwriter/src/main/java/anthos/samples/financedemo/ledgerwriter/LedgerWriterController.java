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

package anthos.samples.financedemo.ledgerwriter;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.logging.Logger;
import java.util.regex.Pattern;

import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.client.RestTemplate;

import io.lettuce.core.api.StatefulRedisConnection;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;

/**
 * Controller for the LedgerWriter service.
 *
 * Functions to accept new transactions for the bank ledger.
 */
@RestController
public final class LedgerWriterController {

    private static final Logger LOGGER =
            Logger.getLogger(LedgerWriterController.class.getName());

    private final String version = System.getenv("VERSION");
    private final String pubKeyPath = System.getenv("PUB_KEY_PATH");
    private final String localRoutingNum = System.getenv("LOCAL_ROUTING_NUM");
    private final String ledgerStream = System.getenv("LEDGER_STREAM");
    private final String balancesApiUri = String.format("http://${}/balances",
            System.getenv("BALANCES_API_ADDR"));

    private final ApplicationContext ctx;
    private final JWTVerifier verifier;
    // account ids should be 10 digits between 0 and 9
    private static final Pattern ACCT_REGEX = Pattern.compile("^[0-9]{10}$");
    // route numbers should be 9 digits between 0 and 9
    private static final Pattern ROUTE_REGEX = Pattern.compile("^[0-9]{9}$");

    /**
     * Constructor.
     *
     * Opens a connection to the transaction repository for the bank ledger.
     */
    public LedgerWriterController() throws IOException,
                                           NoSuchAlgorithmException,
                                           InvalidKeySpecException {
        this.ctx = new AnnotationConfigApplicationContext(
                LedgerWriterConfig.class);

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
     * @return  HTTP Status 200 if server is ready to receive requests.
     */
    @GetMapping("/ready")
    @ResponseStatus(HttpStatus.OK)
    public String readiness() {
        return "ok";
    }

    /**
     * Submit a new transaction to the ledger.
     *
     * @param bearerToken  HTTP request 'Authorization' header
     * @param transaction  transaction to submit
     *
     * @return  HTTP Status 200 if transaction was successfully submitted
     */
    @PostMapping(value = "/transactions", consumes = "application/json")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<?> addTransaction(
            @RequestHeader("Authorization") String bearerToken,
            @RequestBody Transaction transaction) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken = bearerToken.split("Bearer ")[1];
        }
        try {
            final DecodedJWT jwt = this.verifier.verify(bearerToken);
            // validate transaction
            validateTransaction(jwt.getClaim("acct").asString(), transaction);
                                
            if (transaction.getFromRoutingNum().equals(localRoutingNum)) {
                checkAvailableBalance(bearerToken, transaction);
            }

            // No exceptions thrown. Add to ledger.
            submitTransaction(transaction);
            return new ResponseEntity<String>("ok", HttpStatus.CREATED);

        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        } catch (IllegalArgumentException | IllegalStateException e) {
            return new ResponseEntity<String>(e.toString(),
                                              HttpStatus.BAD_REQUEST);
        }
    }


    /**
     * Authenticate transaction details before adding to the ledger.
     *
     *   - Ensure sender is the same user authenticated by auth token
     *   - Ensure account and routing numbers are in the correct format
     *   - Ensure sender and receiver are different accounts
     *   - Ensure amount is positive, and sender has proper balance
     *
     * @param authedAccount  the currently authenticated user account
     * @param transaction    the transaction object
     * @param bearerToken    the token used to authenticate request
     *
     * @throws IllegalArgumentException  on validation error
     */
    private void validateTransaction(String authedAcct, Transaction transaction)
            throws IllegalArgumentException {
        final String fromAcct = transaction.getFromAccountNum();
        final String fromRoute = transaction.getFromRoutingNum();
        final String toAcct = transaction.getToAccountNum();
        final String toRoute = transaction.getToRoutingNum();
        final Integer amount = transaction.getAmount();

        // If this is an internal transaction,
        // ensure it originated from the authenticated user.
        if (fromRoute.equals(localRoutingNum) && !fromAcct.equals(authedAcct)) {
            throw new IllegalArgumentException("sender not authenticated");
        }
        // Validate account and routing numbers.
        if (!ACCT_REGEX.matcher(fromAcct).matches()
              || !ACCT_REGEX.matcher(toAcct).matches()
              || !ROUTE_REGEX.matcher(fromRoute).matches()
              || !ROUTE_REGEX.matcher(toRoute).matches()) {
            throw new IllegalArgumentException("invalid account details");

        }
        // Ensure sender isn't receiver.
        if (fromAcct.equals(toAcct) && fromRoute.equals(toRoute)) {
            throw new IllegalArgumentException("can't send to self");
        }
        // Ensure amount is valid value.
        if (amount <= 0) {
            throw new IllegalArgumentException("invalid amount");
        }
    }


    /**
     * Check there is available funds for this transaction.
     *
     * @param bearerToken  the token used to authenticate request
     * @param transaction  the transaction object
     *
     * @throws IllegalStateException  if insufficient funds
     */
    private void checkAvailableBalance(String bearerToken,
            Transaction transaction) throws IllegalStateException {
        final String fromAcct = transaction.getFromAccountNum();
        final Integer amount = transaction.getAmount();

        // Ensure sender balance can cover transaction.
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + bearerToken);
        HttpEntity entity = new HttpEntity(headers);
        RestTemplate restTemplate = new RestTemplate();
        String uri = balancesApiUri + "/" + fromAcct;
        ResponseEntity<Integer> response = restTemplate.exchange(
            uri, HttpMethod.GET, entity, Integer.class);
        Integer senderBalance = response.getBody();
        if (senderBalance < amount) {
            throw new IllegalStateException("insufficient balance");
        }
    }


    private void submitTransaction(Transaction transaction) {
        LOGGER.fine("Submitting transaction to ledger: " + transaction);
        StatefulRedisConnection redisConnection =
                ctx.getBean(StatefulRedisConnection.class);
        // Use String key/values so Redis data can be read by non-Java clients.
        redisConnection.async().xadd(ledgerStream,
                "fromAccountNum", transaction.getFromAccountNum(),
                "fromRoutingNum", transaction.getFromRoutingNum(),
                "toAccountNum", transaction.getToAccountNum(),
                "toRoutingNum", transaction.getToRoutingNum(),
                "amount", transaction.getAmount().toString(),
                "timestamp", Double.toString(transaction.getTimestamp()));
    }
}
