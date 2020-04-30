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
        // TODO: [issue-52] add tests to addTransaction

        // Given
        when(verifier.verify(anyString())).thenReturn(jwt);
        when(jwt.getClaim("acct")).thenReturn(claim);
        // Skip method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn("SOME STRING");

        // When
        final ResponseEntity actualResult =
                ledgerWriterController.addTransaction(
                        "Bearer abc", transaction);

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
        when(verifier.verify(anyString())).thenReturn(jwt);
        when(jwt.getClaim("acct")).thenReturn(claim);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doNothing().when(spyLedgerWriterController).checkAvailableBalance(
                "abc", transaction);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        "Bearer abc", transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.READINESS_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.CREATED, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given JWTVerificationException return HTTP Status 401")
    void addTransactionWhenUnauthorized() {
        // Given
        when(verifier.verify(anyString())).thenThrow(JWTVerificationException.class);

        // When
        final ResponseEntity actualResult = ledgerWriterController.addTransaction(
                "Bearer abc", transaction);

        // Then
        assertNotNull(actualResult);
        assertEquals(ledgerWriterController.UNAUTHORIZED_CODE,
                actualResult.getBody());
        assertEquals(HttpStatus.UNAUTHORIZED, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given JWTVerificationException return HTTP Status 400")
    void addTransactionWhenBadRequest() {
        // Given
        LedgerWriterController spyLedgerWriterController =
                spy(ledgerWriterController);
        when(verifier.verify(anyString())).thenReturn(jwt);
        when(jwt.getClaim("acct")).thenReturn(claim);
        // Method call checkAvailableBalance
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        doThrow(IllegalStateException.class).when(spyLedgerWriterController).checkAvailableBalance(
                "abc", transaction);

        // When
        final ResponseEntity actualResult =
                spyLedgerWriterController.addTransaction(
                        "Bearer abc", transaction);

        // Then
        assertNotNull(actualResult);
        // TODO: write assert for ResponseEntity body
        assertEquals(HttpStatus.BAD_REQUEST, actualResult.getStatusCode());
    }

    @Test
    @DisplayName("Given ResourceAccessException return HTTP Status 500")
    void addTransactionWhenInternalServerError() {
        // TODO: write test
    }

}
