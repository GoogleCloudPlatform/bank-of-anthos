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

import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.Claim;
import com.auth0.jwt.interfaces.DecodedJWT;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;
import static org.mockito.MockitoAnnotations.initMocks;

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

    private static final String VERSION = "v0.1.0";
    private static final String LOCAL_ROUTING_NUM = "123456789";
    private static final String BALANCES_API_ADDR = "balancereader:8080";
    private static final String AUTHED_ACCOUNT_NUM = "12345678";
    private static final String BEARER_TOKEN = "Bearer abc";
    private static final String TOKEN = "abc";
    private static final String EXCEPTION_MESSAGE = "Invalid variable";

    @BeforeEach
    void setUp() {
        initMocks(this);
        ledgerWriterController = new LedgerWriterController(verifier,
                transactionRepository, transactionValidator,
                LOCAL_ROUTING_NUM, BALANCES_API_ADDR, VERSION);

        when(verifier.verify(anyString())).thenReturn(jwt);
        when(jwt.getClaim("acct")).thenReturn(claim);
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
    @DisplayName("Given the transaction routing number is different than the" +
            "local routing number, return HTTP Status 201")
    void addTransactionSuccessWhenDiffThanLocalRoutingNum() {
        // Given
        // Skip method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn("SOME STRING");

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
    @DisplayName("Given the transaction routing number is the same as the" +
            "local routing number, return HTTP Status 201")
    void addTransactionSuccessWhenSameLocalRoutingNum() {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doNothing().when(spyLedgerWriterController).checkAvailableBalance(
                TOKEN, transaction);

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
    @DisplayName("Given JWTVerificationException return HTTP Status 401")
    void addTransactionWhenJWTVerificationExceptionThrown() {
        // Given
        when(verifier.verify(anyString())).thenThrow(
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
    @DisplayName("Given validateTransaction() throws " +
            "IllegalArgumentException, return HTTP Status 400")
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
    @DisplayName("Given checkAvailableBalance() throws " +
            "IllegalStateException, return HTTP Status 400")
    void addTransactionWhenIllegalStateExceptionThrown() {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doThrow(new IllegalStateException(EXCEPTION_MESSAGE)).when(
                spyLedgerWriterController).checkAvailableBalance(
                TOKEN, transaction);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        BEARER_TOKEN, transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(EXCEPTION_MESSAGE, actualResult.getBody());
        assertEquals(HttpStatus.BAD_REQUEST, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given ResourceAccessException return HTTP Status 500")
    void addTransactionWhenResourceAccessExceptionThrown() {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doThrow(new ResourceAccessException(EXCEPTION_MESSAGE)).when(
                spyLedgerWriterController).checkAvailableBalance(
                TOKEN, transaction);

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
    @DisplayName("Given CannotCreateTransactionException " +
            "return HTTP Status 500")
    void addTransactionWhenCannotCreateTransactionExceptionExceptionThrown() {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doThrow(new ResourceAccessException(EXCEPTION_MESSAGE)).when(
                spyLedgerWriterController).checkAvailableBalance(
                TOKEN, transaction);

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
    @DisplayName("Given HttpServerErrorException return HTTP Status 500")
    void addTransactionWhenHttpServerErrorExceptionThrown() {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doThrow(new HttpServerErrorException(
                HttpStatus.INTERNAL_SERVER_ERROR)).when(
                        spyLedgerWriterController).checkAvailableBalance(
                TOKEN, transaction);

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
}
