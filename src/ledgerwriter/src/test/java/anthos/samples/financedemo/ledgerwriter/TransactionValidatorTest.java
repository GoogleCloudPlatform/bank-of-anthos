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

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

class TransactionValidatorTest {

    private TransactionValidator transactionValidator;

    @Mock
    private Transaction transaction;

    private static final String LOCAL_ROUTING_NUM = "123456789";
    private static final String INVALID_NUM = "123456";
    private static final String AUTHED_ACCOUNT_NUM = "1234567890";
    private static final String NON_AUTHED_ACCOUNT_NUM = "0987654321";
    private static final String TO_ACCOUNT_NUM = "5678901234";
    private static final String TO_ROUTING_NUM = "567891234";
    private static final Integer VALIDAMOUNT = 3755;
    private static final Integer INVALIDAMOUNT = -23;

    @BeforeEach
    void setUp() {
        initMocks(this);
        transactionValidator = new TransactionValidator();

        when(transaction.getFromAccountNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getToAccountNum()).thenReturn(TO_ACCOUNT_NUM);
        when(transaction.getToRoutingNum()).thenReturn(TO_ROUTING_NUM);
        when(transaction.getAmount()).thenReturn(VALIDAMOUNT);
    }

    @Test
    @DisplayName("Given the transaction is validated, no exception is thrown")
    void validateTransactionSuccess() {
        assertDoesNotThrow(() -> {
            transactionValidator.validateTransaction(
                    LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
        });
    }

    @Test
    @DisplayName("Given invalid sender account number, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenInvalidFromAccountNumber() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                            LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_INVALID_NUMBER,
                exceptionThrown.getMessage());
    }

    @Test
    @DisplayName("Given invalid receiver account number, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenInvalidToAccountNumber() {
        // Given
        when(transaction.getToAccountNum()).thenReturn(INVALID_NUM);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                            LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_INVALID_NUMBER,
                exceptionThrown.getMessage());
    }

    @Test
    @DisplayName("Given invalid sender routing number, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenInvalidFromRoutingNumber() {
        // Given
        when(transaction.getFromRoutingNum()).thenReturn(INVALID_NUM);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                            LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_INVALID_NUMBER,
                exceptionThrown.getMessage());
    }

    @Test
    @DisplayName("Given invalid receiver routing number, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenInvalidToRoutingNumber() {
        // Given
        when(transaction.getToRoutingNum()).thenReturn(INVALID_NUM);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                            LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_INVALID_NUMBER,
                exceptionThrown.getMessage());
    }

    @Test
    @DisplayName("Given the sender is not authenticated, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenNotAuthenticated() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(
                NON_AUTHED_ACCOUNT_NUM);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                            LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_NOT_AUTHENTICATED,
                exceptionThrown.getMessage());
    }

    @Test
    @DisplayName("Given the sender is the receiver, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenSenderIsReceiver() {
        // Given
        when(transaction.getToAccountNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getToRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                            LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_SEND_TO_SELF,
                exceptionThrown.getMessage());
    }

    @Test
    @DisplayName("Given an invalid transaction amount, " +
            "IllegalArgumentException is thrown")
    void validateTransactionFailWhenAmountNotValid() {
        // Given
        when(transaction.getAmount()).thenReturn(INVALIDAMOUNT);

        // When
        IllegalArgumentException exceptionThrown = assertThrows(
                IllegalArgumentException.class, () -> {
                    transactionValidator.validateTransaction(
                        LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
                });

        // Then
        assertNotNull(exceptionThrown);
        assertEquals(transactionValidator.EXCEPTION_MESSAGE_INVALID_AMOUNT,
                exceptionThrown.getMessage());
    }
}
