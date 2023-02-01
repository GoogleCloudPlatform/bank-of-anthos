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

import static anthos.samples.bankofanthos.ledgermonolith.ExceptionMessages.EXCEPTION_MESSAGE_DUPLICATE_TRANSACTION;
import static anthos.samples.bankofanthos.ledgermonolith.ExceptionMessages.EXCEPTION_MESSAGE_INSUFFICIENT_BALANCE;
import static anthos.samples.bankofanthos.ledgermonolith.ExceptionMessages.EXCEPTION_MESSAGE_WHEN_AUTHORIZATION_HEADER_NULL;

import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.LoadingCache;
import com.google.common.util.concurrent.UncheckedExecutionException;
import java.util.concurrent.TimeUnit;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.CannotCreateTransactionException;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import java.util.Collection;
import java.util.Deque;
import java.util.concurrent.ExecutionException;
import org.springframework.web.bind.annotation.PathVariable;

/**
 * Controller for the combined LedgerMonolith service
 *
 * Combines endpoints for Transactionhistory, BalanceReader, and LedgerWriter
 */
@RestController
public final class LedgerMonolithController {

    private static final Logger LOGGER =
        LogManager.getLogger(LedgerMonolithController.class);

    @Autowired
    private TransactionRepository dbRepo;

    @Value("${EXTRA_LATENCY_MILLIS:#{null}}")
    private Integer extraLatencyMillis;
    @Value("${HISTORY_LIMIT:100}")
    private Integer historyLimit;

    private JWTVerifier verifier;
    private LedgerReader ledgerReader;

    // Combined balancereader / txnhistory cache
    private LoadingCache<String, AccountInfo> ledgerReaderCache;
    private Cache<String, Long> ledgerWriterCache;

    private TransactionRepository transactionRepository;
    private TransactionValidator transactionValidator;


    private String localRoutingNum;
    private String version;

    public static final String READINESS_CODE = "ok";
    public static final String UNAUTHORIZED_CODE = "not authorized";
    public static final String JWT_ACCOUNT_KEY = "acct";

    @Autowired
    RestTemplate restTemplate;

    /**
    * Constructor.
    *
    * Initializes JWT verifier.
    * (merges together constructors for :
    * LedgerWriter, Transactionhistory, Balancereader.
    **ONE** shared DB cache, not multiple)
    */
    @Autowired
    public LedgerMonolithController(
            @Value("${PUB_KEY_PATH}") final String publicKeyPath,
            LoadingCache<String, AccountInfo> ledgerReaderCache,
            JWTVerifier verifier,
            TransactionRepository transactionRepository,
            TransactionValidator transactionValidator,
            LedgerReader reader,
            @Value("${LOCAL_ROUTING_NUM}") String localRoutingNum,
            @Value("${VERSION}") String version) {
        this.verifier = verifier;
        this.transactionRepository = transactionRepository;
        this.transactionValidator = transactionValidator;
        this.localRoutingNum = localRoutingNum;
        this.version = version;

        // balance reader
        this.ledgerReaderCache = ledgerReaderCache;

        // ledger writer
        this.ledgerWriterCache = CacheBuilder.newBuilder()
        .recordStats()
        .expireAfterWrite(1, TimeUnit.HOURS)
        .build();

        // Ledger Cache processing
        this.ledgerReader = reader;
        this.ledgerReader.startWithCallback(transaction -> {
            final String fromId = transaction.getFromAccountNum();
            final String fromRouting = transaction.getFromRoutingNum();
            final String toId = transaction.getToAccountNum();
            final String toRouting = transaction.getToRoutingNum();
            final Integer amount = transaction.getAmount();

            if (fromRouting.equals(localRoutingNum)
                && this.ledgerReaderCache.asMap().containsKey(fromId)) {
                AccountInfo info = ledgerReaderCache.asMap().get(fromId);
                Long prevBalance = info.getBalance();
                Long newBalance = prevBalance - amount;
                processTransaction(fromId, newBalance, transaction);
            }

            if (toRouting.equals(localRoutingNum)
                && this.ledgerReaderCache.asMap().containsKey(toId)) {
                AccountInfo info = ledgerReaderCache.asMap().get(toId);
                Long prevBalance = info.getBalance();
                Long newBalance = prevBalance + amount;
                processTransaction(toId, newBalance, transaction);
            }

        });
        LOGGER.info("✅ Started LedgerMonolith.");
    }

     /**
     * Helper function to add a single transaction to the internal cache
     *
     * @param accountId   the accountId associated with the transaction
     * @param transaction the full transaction object
     */
    private void processTransaction(String accountId, Long newBalance,
        Transaction transaction) {
        LOGGER.debug("Processing transaction for account: " + accountId);
        AccountInfo accountInfo = this.ledgerReaderCache.asMap()
                                .get(accountId);

        Deque<Transaction> tList = accountInfo.getTransactions();

        tList.addFirst(transaction);
        // Drop old transactions
        if (tList.size() > historyLimit) {
            tList.removeLast();
        }

        // Update cache with updated balance, transactions
        AccountInfo info = new AccountInfo(newBalance, tList);
        LOGGER.debug("Updating ledgerReaderCache with new balance: "
        + newBalance.toString());
        this.ledgerReaderCache.put(accountId, info);
    }


    /**
     * Version endpoint.
     *
     * @return  service version string
     */
    @GetMapping("/version")
    public ResponseEntity version() {
        return new ResponseEntity<>(version, HttpStatus.OK);
    }

    /**
     * Readiness probe endpoint.
     *
     * @return HTTP Status 200 if server is ready to receive requests.
     */
    @GetMapping("/ready")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<String> readiness() {
        return new ResponseEntity<>(READINESS_CODE, HttpStatus.OK);
    }

      /**
     * Liveness probe endpoint.
     *
     * @return HTTP Status 200 if server is healthy and serving requests.
     */
    @GetMapping("/healthy")
    public ResponseEntity liveness() {
        if (!ledgerReader.isAlive()) {
            // Background thread died.
            LOGGER.error("Ledger reader not healthy");
            return new ResponseEntity<>("Ledger reader not healthy",
                HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return new ResponseEntity<>("ok", HttpStatus.OK);
    }


    // BEGIN LEDGER WRITER

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
                LOGGER.error("Transaction submission failed: "
                    + "Authorization header null");
                throw new IllegalArgumentException(
                        EXCEPTION_MESSAGE_WHEN_AUTHORIZATION_HEADER_NULL);
            }
            final DecodedJWT jwt = this.verifier.verify(bearerToken);

            // Check against cache for duplicate transactions
            if (this.ledgerWriterCache.asMap().containsKey(transaction.getRequestUuid())) {
                throw new IllegalStateException(
                        EXCEPTION_MESSAGE_DUPLICATE_TRANSACTION);
            }

            // validate transaction
            transactionValidator.validateTransaction(localRoutingNum,
                    jwt.getClaim(JWT_ACCOUNT_KEY).asString(), transaction);
            // Ensure sender balance can cover transaction.
            if (transaction.getFromRoutingNum().equals(localRoutingNum)) {
                Long balance = getAvailableBalance(transaction.getFromAccountNum());
                if (balance < transaction.getAmount()) {
                    LOGGER.error("Transaction submission failed: "
                        + "Insufficient balance");
                    throw new IllegalStateException(
                            EXCEPTION_MESSAGE_INSUFFICIENT_BALANCE);
                }
            }
            // No exceptions thrown. Add to ledger
            transactionRepository.save(transaction);
            this.ledgerWriterCache.put(transaction.getRequestUuid(),
                    transaction.getTransactionId());
            LOGGER.info("Submitted transaction successfully");
            return new ResponseEntity<>(READINESS_CODE,
                    HttpStatus.CREATED);

        } catch (JWTVerificationException e) {
            LOGGER.error("Failed to submit transaction: "
                + "not authorized");
            return new ResponseEntity<>(UNAUTHORIZED_CODE,
                                              HttpStatus.UNAUTHORIZED);
        } catch (IllegalArgumentException | IllegalStateException e) {
            LOGGER.error("Failed to retrieve account balance: "
                + "bad request");
            return new ResponseEntity<>(e.getMessage(),
                                              HttpStatus.BAD_REQUEST);
        } catch (ResourceAccessException
                | CannotCreateTransactionException
                | HttpServerErrorException e) {
            LOGGER.error("Failed to retrieve account balance");
            return new ResponseEntity<>(e.getMessage(),
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Modified getAvailableBalance - instead of making an external
     * API call like in the microservice version,
     * get balance from local cache.
     */
    protected Long getAvailableBalance(String accountId) {
        LOGGER.debug("Retrieving balance for transaction sender");
        Long balance = Long.valueOf(-1);
        try {
            AccountInfo info = ledgerReaderCache.get(accountId);
            balance = info.getBalance();
        } catch (ExecutionException | UncheckedExecutionException e) {
            LOGGER.error("Cache error");
        }
        return balance;
    }

    // BEGIN BALANCE READER

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
                return new ResponseEntity<>("not authorized",
                    HttpStatus.UNAUTHORIZED);
            }
            // Load from cache
            AccountInfo info = ledgerReaderCache.get(accountId);
            Long balance = info.getBalance();

            return new ResponseEntity<Long>(balance, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            LOGGER.error("Failed to retrieve account balance: not authorized");
            return new ResponseEntity<>("not authorized",
                HttpStatus.UNAUTHORIZED);
        } catch (ExecutionException | UncheckedExecutionException e) {
            LOGGER.error("Cache error");
            return new ResponseEntity<>("Account cache error",
                HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }


    // BEGIN TRANSACTION HISTORY

    /**
     * Return a list of transactions for the specified account.
     *
     * The currently authenticated user must be allowed to access the account.
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
            DecodedJWT jwt = verifier.verify(bearerToken);
            // Check that the authenticated user can access this account.
            if (!accountId.equals(jwt.getClaim("acct").asString())) {
                LOGGER.error("Failed to retrieve account transactions: "
                    + "not authorized");
                return new ResponseEntity<>("not authorized",
                                                  HttpStatus.UNAUTHORIZED);
            }

            // Load from cache
            AccountInfo info = ledgerReaderCache.get(accountId);
            Deque<Transaction> historyList = info.getTransactions();

            // Set artificial extra latency.
            LOGGER.debug("Setting artificial latency");
            if (extraLatencyMillis != null) {
                try {
                    Thread.sleep(extraLatencyMillis);
                } catch (InterruptedException e) {
                    // Fake latency interrupted. Continue.
                }
            }

            return new ResponseEntity<Collection<Transaction>>(
                    historyList, HttpStatus.OK);
        } catch (JWTVerificationException e) {
            LOGGER.error("Failed to retrieve account transactions: "
                + "not authorized");
            return new ResponseEntity<>("not authorized",
                                              HttpStatus.UNAUTHORIZED);
        } catch (ExecutionException | UncheckedExecutionException e) {
            LOGGER.error("Cache error");
            return new ResponseEntity<>("cache error",
                                              HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}

