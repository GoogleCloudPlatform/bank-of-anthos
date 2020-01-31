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

import io.lettuce.core.api.StatefulRedisConnection;
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

@RestController
public final class LedgerWriterController {

    ApplicationContext ctx =
            new AnnotationConfigApplicationContext(LedgerWriterConfig.class);

    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final String routingNum =  System.getenv("LOCAL_ROUTING_NUM");
    private final String balancesUri = String.format("http://%s/get_balance",
        System.getenv("BALANCES_API_ADDR"));
    private final JWTVerifier verifier;

    public LedgerWriterController() throws IOException,
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
    }

    /**
     * Readiness probe endpoint.
     *
     * @return HTTP Status 200 if server is serving requests.
     */
    @GetMapping("/ready")
    @ResponseStatus(HttpStatus.OK)
    public String readiness() {
        return "ok";
    }

    /**
     * Submit a new transaction to the ledger.
     *
     * @param Transaction to be submitted.
     * @return HTTP Status 200 if transaction was successfully submitted.
     */
    @PostMapping(value = "/new_transaction", consumes = "application/json")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<?> addTransaction(
            @RequestHeader("Authorization") String bearerToken,
            @RequestBody Transaction transaction) {
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            bearerToken = bearerToken.split("Bearer ")[1];
        }
        try {
            DecodedJWT jwt = this.verifier.verify(bearerToken);
            String initiatorAcct = jwt.getClaim("acct").asString();
            // Ensure sender is the one who initiated this transaction,
            // or is external deposit.
            // TODO: Check if external account belongs to initiator of deposit.
            if (!(transaction.getFromAccountNum() == initiatorAcct
                  || transaction.getFromRoutingNum() != this.routingNum)) {
                return new ResponseEntity<String>("not authorized",
                                                  HttpStatus.UNAUTHORIZED);
            }
            // Ensure amount is valid value.
            if (transaction.getAmount() <= 0) {
                return new ResponseEntity<String>("invalid amount",
                                                  HttpStatus.BAD_REQUEST);
            }
            // Ensure sender balance can cover transaction.
            if (transaction.getFromRoutingNum() == this.routingNum) {
                HttpHeaders headers = new HttpHeaders();
                headers.set("Authorization", "Bearer " + bearerToken);
                HttpEntity entity = new HttpEntity(headers);
                RestTemplate restTemplate = new RestTemplate();
                ResponseEntity<Balance> response = restTemplate.exchange(
                    balancesUri, HttpMethod.GET, entity, Balance.class);
                Balance senderBalance = response.getBody();
                if (senderBalance.amount < transaction.getAmount()) {
                    return new ResponseEntity<String>("insufficient balance",
                                                      HttpStatus.BAD_REQUEST);
                }
            }
            // Transaction looks valid. Add to ledger.
            System.out.println("adding transaction: " + transaction);
            submitTransaction(transaction);

            return new ResponseEntity<String>("ok", HttpStatus.CREATED);
        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        }
    }

    private void submitTransaction(Transaction transaction) {
        StatefulRedisConnection redisConnection =
                ctx.getBean(StatefulRedisConnection.class);
        // Use String key/values so Redis data can be read by non-Java clients.
        redisConnection.async().xadd(ledgerStreamKey,
                "fromAccountNum", transaction.getFromAccountNum(),
                "fromRoutingNum", transaction.getFromRoutingNum(),
                "toAccountNum", transaction.getToAccountNum(),
                "toRoutingNum", transaction.getToRoutingNum(),
                "amount", transaction.getAmount().toString(),
                "timestamp", Double.toString(transaction.getTimestamp()));
    }
}
