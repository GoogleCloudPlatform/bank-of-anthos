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

package anthos.samples.bankofanthos.ledgerwriter;

import java.util.logging.Logger;

import  org.springframework.web.client.HttpServerErrorException;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.CannotCreateTransactionException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;

import static anthos.samples.bankofanthos.ledgerwriter.ExceptionMessages.
        EXCEPTION_MESSAGE_INSUFFICIENT_BALANCE;
import static anthos.samples.bankofanthos.ledgerwriter.ExceptionMessages.
        EXCEPTION_MESSAGE_WHEN_AUTHORIZATION_HEADER_NULL;

@RestController
public final class LedgerWriterController {

    private static final Logger LOGGER =
            Logger.getLogger(LedgerWriterController.class.getName());

    private TransactionRepository transactionRepository;
    private TransactionValidator transactionValidator;
    private JWTVerifier verifier;

    private String localRoutingNum;
    private String balancesApiUri;
    private String version;

    public static final String READINESS_CODE = "ok";
    public static final String UNAUTHORIZED_CODE = "not authorized";
    public static final String JWT_ACCOUNT_KEY = "acct";

    /**
    * Constructor.
    *
    * Initializes JWT verifier.
    */

    public LedgerWriterController(
            JWTVerifier verifier,
            TransactionRepository transactionRepository,
            TransactionValidator transactionValidator,
            @Value("${LOCAL_ROUTING_NUM}") String localRoutingNum,
            @Value("http://${BALANCES_API_ADDR}/balances")
                    String balancesApiUri,
            @Value("${VERSION}") String version) {
        this.verifier = verifier;
        this.transactionRepository = transactionRepository;
        this.transactionValidator = transactionValidator;
        this.localRoutingNum = localRoutingNum;
        this.balancesApiUri = balancesApiUri;
        this.version = version;
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
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<String> readiness() {
        return new ResponseEntity<String>(READINESS_CODE, HttpStatus.OK);
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
            if (bearerToken == null) {
                throw new IllegalArgumentException(
                        EXCEPTION_MESSAGE_WHEN_AUTHORIZATION_HEADER_NULL);
            }
            final DecodedJWT jwt = this.verifier.verify(bearerToken);
            // validate transaction
            transactionValidator.validateTransaction(localRoutingNum,
                    jwt.getClaim(JWT_ACCOUNT_KEY).asString(), transaction);
            // Ensure sender balance can cover transaction.
            if (transaction.getFromRoutingNum().equals(localRoutingNum)) {
                int balance = getAvailableBalance(
                        bearerToken, transaction.getFromAccountNum());
                if (balance < transaction.getAmount()) {
                    throw new IllegalStateException(
                            EXCEPTION_MESSAGE_INSUFFICIENT_BALANCE);
                }
            }

            // No exceptions thrown. Add to ledger
            LOGGER.fine("Submitting transaction "
                    + transaction.toString());
            transactionRepository.save(transaction);
            return new ResponseEntity<String>(READINESS_CODE,
                    HttpStatus.CREATED);

        } catch (JWTVerificationException e) {
            return new ResponseEntity<String>(UNAUTHORIZED_CODE,
                                              HttpStatus.UNAUTHORIZED);
        } catch (IllegalArgumentException | IllegalStateException e) {
            return new ResponseEntity<String>(e.getMessage(),
                                              HttpStatus.BAD_REQUEST);
        } catch (ResourceAccessException
                | CannotCreateTransactionException
                | HttpServerErrorException e) {
            return new ResponseEntity<String>(e.getMessage(),
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Retrieve the balance for the transaction's sender.
     *
     * @param token  the token used to authenticate request
     * @param fromAcct  sender account number
     *
     * @return available balance of the sender account
     *
     * @throws HttpServerErrorException  if balance service returns 500
     */
    protected int getAvailableBalance(String token, String fromAcct)
            throws HttpServerErrorException {
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + token);
        HttpEntity entity = new HttpEntity(headers);
        RestTemplate restTemplate = new RestTemplate();
        String uri = balancesApiUri + "/" + fromAcct;
        ResponseEntity<Integer> response = restTemplate.exchange(
            uri, HttpMethod.GET, entity, Integer.class);
        Integer senderBalance = response.getBody();
        return senderBalance.intValue();
    }

}
