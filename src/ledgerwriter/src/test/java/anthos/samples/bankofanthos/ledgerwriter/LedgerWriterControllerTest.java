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

import static anthos.samples.bankofanthos.ledgerwriter.ExceptionMessages.EXCEPTION_MESSAGE_DUPLICATE_TRANSACTION;
import static anthos.samples.bankofanthos.ledgerwriter.ExceptionMessages.EXCEPTION_MESSAGE_INSUFFICIENT_BALANCE;
import static anthos.samples.bankofanthos.ledgerwriter.ExceptionMessages.EXCEPTION_MESSAGE_WHEN_AUTHORIZATION_HEADER_NULL;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.Claim;
import com.auth0.jwt.interfaces.DecodedJWT;
import io.micrometer.core.instrument.Clock;
import io.micrometer.core.lang.Nullable;
import io.micrometer.stackdriver.StackdriverConfig;
import io.micrometer.stackdriver.StackdriverMeterRegistry;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.mockito.Mock;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.CannotCreateTransactionException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

class LedgerWriterControllerTest {

    private LedgerWriterController ledgerWriterController;

    @Mock
    private TransactionValidator transactionValidator;
    @Mock
    private TransactionRepository transactionRepository;
    @Mock
    private JWTVerifier verifier;
    @Mock
    private Transaction transaction;
    @Mock
    private DecodedJWT jwt;
    @Mock
    private Claim claim;
    @Mock
    private Clock clock;

    private static final String VERSION = "v0.1.0";
    private static final String LOCAL_ROUTING_NUM = "123456789";
    private static final String NON_LOCAL_ROUTING_NUM = "987654321";
    private static final String BALANCES_API_ADDR = "balancereader:8080";
    private static final String AUTHED_ACCOUNT_NUM = "1234567890";
    private static final String BEARER_TOKEN = "Bearer abc";
    private static final String TOKEN = "abc";
    private static final String EXCEPTION_MESSAGE = "Invalid variable";
    private static final int SENDER_BALANCE = 40;
    private static final int LARGER_THAN_SENDER_BALANCE = 1000;
    private static final int SMALLER_THAN_SENDER_BALANCE = 10;

    @BeforeEach
    void setUp() {
        initMocks(this);
        StackdriverMeterRegistry meterRegistry = new StackdriverMeterRegistry(new StackdriverConfig() {
              @Override
              public boolean enabled() {
                return false;
              }

              @Override
              public String projectId() {
                return "test";
              }

              @Override
              @Nullable
              public String get(String key) {
                return null;
              }
          }, clock);

        ledgerWriterController = new LedgerWriterController(verifier,
                meterRegistry,
                transactionRepository, transactionValidator,
                LOCAL_ROUTING_NUM, BALANCES_API_ADDR, VERSION);

        when(verifier.verify(TOKEN)).thenReturn(jwt);
        when(jwt.getClaim(
                LedgerWriterController.JWT_ACCOUNT_KEY)).thenReturn(claim);
    }

    @Test
    @DisplayName("Given version number in the environment, " +
            "return a ResponseEntity with the version number")
    void version() {
        // When
        final ResponseEntity actualResult = ledgerWriterController.version();

        // Then
        assertNotNull(actualResult);
        assertEquals(VERSION, actualResult.getBody());
        assertEquals(HttpStatus.OK, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the server is serving requests, return HTTP Status 200")
    void readiness() {
        // When
        final ResponseEntity actualResult = ledgerWriterController.readiness();

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.READINESS_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.OK, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is external, return HTTP Status 201")
    void addTransactionSuccessWhenDiffThanLocalRoutingNum(TestInfo testInfo) {
        // Given
        when(transaction.getFromRoutingNum()).thenReturn(NON_LOCAL_ROUTING_NUM);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());

        // When
        final ResponseEntity actualResult =
                ledgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.READINESS_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.CREATED, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is internal and the transaction amount == sender balance, " +
            "return HTTP Status 201")
    void addTransactionSuccessWhenAmountEqualToBalance(TestInfo testInfo) {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getFromRoutingNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getAmount()).thenReturn(SENDER_BALANCE);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doReturn(SENDER_BALANCE).when(
                spyLedgerWriterController).getAvailableBalance(
                TOKEN, AUTHED_ACCOUNT_NUM);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.READINESS_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.CREATED, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is internal and the transaction amount < sender balance, " +
            "return HTTP Status 201")
    void addTransactionSuccessWhenAmountSmallerThanBalance(TestInfo testInfo) {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getFromRoutingNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getAmount()).thenReturn(SMALLER_THAN_SENDER_BALANCE);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doReturn(SENDER_BALANCE).when(
                spyLedgerWriterController).getAvailableBalance(
                TOKEN, AUTHED_ACCOUNT_NUM);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.READINESS_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.CREATED, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is internal and the transaction amount > sender balance, " +
            "return HTTP Status 400")
    void addTransactionFailWhenWhenAmountLargerThanBalance(TestInfo testInfo) {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getFromAccountNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getAmount()).thenReturn(LARGER_THAN_SENDER_BALANCE);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doReturn(SENDER_BALANCE).when(
                spyLedgerWriterController).getAvailableBalance(
                TOKEN, AUTHED_ACCOUNT_NUM);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(
                EXCEPTION_MESSAGE_INSUFFICIENT_BALANCE,
                actualResult.getBody());
        assertEquals(HttpStatus.BAD_REQUEST, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given JWT verifier cannot verify the given bearer token, " +
            "return HTTP Status 401")
    void addTransactionWhenJWTVerificationExceptionThrown() {
        // Given
        when(verifier.verify(TOKEN)).thenThrow(
                JWTVerificationException.class);

        // When
        final ResponseEntity actualResult =
                ledgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.UNAUTHORIZED_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.UNAUTHORIZED, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given exception thrown on validation, return HTTP Status 400")
    void addTransactionWhenIllegalArgumentExceptionThrown() {
        // Given
        when(claim.asString()).thenReturn(AUTHED_ACCOUNT_NUM);
        doThrow(new IllegalArgumentException(EXCEPTION_MESSAGE)).
                when(transactionValidator).validateTransaction(
                        LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);

        // When
        final ResponseEntity actualResult =
                ledgerWriterController.addTransaction(
                BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(EXCEPTION_MESSAGE,
                actualResult.getBody());
        assertEquals(HttpStatus.BAD_REQUEST, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given HTTP request 'Authorization' header is null, " +
            "return HTTP Status 400")
    void addTransactionWhenBearerTokenNull() {
        // When
        final ResponseEntity actualResult =
                ledgerWriterController.addTransaction(
                        null, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(EXCEPTION_MESSAGE_WHEN_AUTHORIZATION_HEADER_NULL,
                actualResult.getBody());
        assertEquals(HttpStatus.BAD_REQUEST, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is internal, check available balance and the balance " +
            "reader throws an error, return HTTP Status 500")
    void addTransactionWhenResourceAccessExceptionThrown(TestInfo testInfo) {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getFromAccountNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doThrow(new ResourceAccessException(EXCEPTION_MESSAGE)).when(
                spyLedgerWriterController).getAvailableBalance(
                TOKEN, AUTHED_ACCOUNT_NUM);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(EXCEPTION_MESSAGE, actualResult.getBody());
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR,
                actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is external and the transaction cannot be saved to the " +
            "transaction repository, return HTTP Status 500")
    void addTransactionWhenCannotCreateTransactionExceptionExceptionThrown(TestInfo testInfo) {
        // Given
        when(transaction.getFromRoutingNum()).thenReturn(NON_LOCAL_ROUTING_NUM);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doThrow(new CannotCreateTransactionException(EXCEPTION_MESSAGE)).when(
                transactionRepository).save(transaction);

        // When
        final ResponseEntity actualResult =
                ledgerWriterController.addTransaction(
                        TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(EXCEPTION_MESSAGE, actualResult.getBody());
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR,
                actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given the transaction is internal, check available balance and the balance " +
            "service returns 500, return HTTP Status 500")
    void addTransactionWhenHttpServerErrorExceptionThrown(TestInfo testInfo) {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getFromAccountNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doThrow(new HttpServerErrorException(
                HttpStatus.INTERNAL_SERVER_ERROR)).when(
                        spyLedgerWriterController).getAvailableBalance(
                TOKEN, AUTHED_ACCOUNT_NUM);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR.toString(),
                actualResult.getBody());
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR,
                actualResult.getStatusCode());
    }

    @Test
    @DisplayName("When duplicate UUID transactions are sent, " +
            "second one is rejected with HTTP status 400")
    void addTransactionWhenDuplicateUuidExceptionThrown(TestInfo testInfo) {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getFromRoutingNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getAmount()).thenReturn(SMALLER_THAN_SENDER_BALANCE);
        when(transaction.getRequestUuid()).thenReturn(testInfo.getDisplayName());
        doReturn(SENDER_BALANCE).when(
                spyLedgerWriterController).getAvailableBalance(
                TOKEN, AUTHED_ACCOUNT_NUM);

        // When
        final ResponseEntity originalResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);
        final ResponseEntity duplicateResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(originalResult);
        assertEquals(ledgerWriterController.READINESS_CODE,
                originalResult.getBody());
        assertEquals(HttpStatus.CREATED, originalResult.getStatusCode());

        assertNotNull(duplicateResult);
        assertEquals(
                EXCEPTION_MESSAGE_DUPLICATE_TRANSACTION,
                duplicateResult.getBody());
        assertEquals(HttpStatus.BAD_REQUEST, duplicateResult.getStatusCode());
    }
}
