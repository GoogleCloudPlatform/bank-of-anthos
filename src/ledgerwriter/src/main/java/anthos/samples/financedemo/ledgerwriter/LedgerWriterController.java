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

import com.auth0.jwt.interfaces.DecodedJWT;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.JWTVerifier;

import anthos.samples.financedemo.common.AuthTools;
import anthos.samples.financedemo.common.Balance;
import anthos.samples.financedemo.common.Transaction;
import anthos.samples.financedemo.common.TransactionUtils;

@RestController
public final class LedgerWriterController {

    ApplicationContext ctx =
            new AnnotationConfigApplicationContext(LedgerWriterConfig.class);

    private final String ledgerStreamKey = System.getenv("LEDGER_STREAM");
    private final String localRoutingNum =  System.getenv("LOCAL_ROUTING_NUM");
    private final String balancesUri = String.format("http://%s/get_balance",
        System.getenv("BALANCES_API_ADDR"));
    private final JWTVerifier verifier;

    public LedgerWriterController() {
      this.verifier = AuthTools.newJWTVerifierFromFile(System.getenv("PUB_KEY_PATH"));
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
                || transaction.getFromRoutingNum() != this.localRoutingNum)) {
            return new ResponseEntity<String>("not authorized",
                HttpStatus.UNAUTHORIZED);
                }
          // Ensure amount is valid value.
          if (transaction.getAmount() <= 0) {
            return new ResponseEntity<String>("invalid amount",
                HttpStatus.BAD_REQUEST);
          }
          // Ensure sender balance can cover transaction.
          if (transaction.getFromRoutingNum() == this.localRoutingNum) {
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + bearerToken);
            HttpEntity entity = new HttpEntity(headers);
            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<Balance> response = restTemplate.exchange(
                    balancesUri, HttpMethod.GET, entity, Balance.class);
                Balance senderBalance = response.getBody();
                if (senderBalance.getAmount() < transaction.getAmount()) {
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
        TransactionUtils.timestampTransaction(transaction);
        redisConnection.async().xadd(ledgerStreamKey,
                TransactionUtils.serializeForRedis(transaction));
    }
}
