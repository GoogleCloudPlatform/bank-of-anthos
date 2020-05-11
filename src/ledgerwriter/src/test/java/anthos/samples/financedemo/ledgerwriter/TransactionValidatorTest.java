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
    private static final String AUTHED_ACCOUNT_NUM = "1234567890";
    private static final String NON_AUTHED_ACCOUNT_NUM = "0987654321";
    private static final String TO_ACCOUNT_NUM = "5678901234";
    private static final String TO_ROUTING_NUM = "567891234";


    private static final String INVALID_NUM_8_DIGITS = "12345678";
    private static final String INVALID_NUM_9_DIGITS = "123456789";
    private static final String INVALID_NUM_11_DIGITS = "12345678900";
    private static final String INVALID_NUM_EMPTY = "";
    private static final String INVALID_NUM_CHAR = "12345678j";
    private static final String INVALID_NUM_ALL_CHARS = "abcdefghij";
    private static final String INVALID_NUM_SPACE = "123 456789";
    private static final String INVALID_NUM_All_SPACES = "          ";
    private static final String INVALID_NUM_DECIMAL = "1234567.89";
    private static final String INVALID_NUM_UNDERSCORE = "123_456789";
    private static final String INVALID_NUM_JAPANESE_CHAR = "12345仮6789";
    private static final String INVALID_NUM_BEAR_EMOJI = "12341545\ud83d\udc3b";

    private static final Integer VALID_AMOUNT_ONE = 1;
    private static final Integer VALID_AMOUNT_REGULAR = 3755;
    private static final Integer VALID_AMOUNT_LARGE = Integer.MAX_VALUE;

    private static final Integer INVALID_AMOUNT_ZERO = 0;
    private static final Integer INVALID_AMOUNT_NEGATIVE = -23;
    private static final Integer INVALID_AMOUNT_SMALL = Integer.MIN_VALUE;

    @BeforeEach
    void setUp() {
        initMocks(this);
        transactionValidator = new TransactionValidator();

        when(transaction.getFromAccountNum()).thenReturn(AUTHED_ACCOUNT_NUM);
        when(transaction.getFromRoutingNum()).thenReturn(LOCAL_ROUTING_NUM);
        when(transaction.getToAccountNum()).thenReturn(TO_ACCOUNT_NUM);
        when(transaction.getToRoutingNum()).thenReturn(TO_ROUTING_NUM);
        when(transaction.getAmount()).thenReturn(VALID_AMOUNT_REGULAR);
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
    @DisplayName("Given 9-digit sender account number, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_Is9Digits() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_9_DIGITS);

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
    @DisplayName("Given 11-digit sender account number, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_Is11Digits() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_11_DIGITS);

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
    @DisplayName("Given empty sender account number, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_IsEmpty() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_EMPTY);

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
    @DisplayName("Given sender account number contains English characters, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_ContainsEnglishChars() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_CHAR);

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
    @DisplayName("Given sender account number contains Japanese characters , " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_ContainsJapaneseChars() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_JAPANESE_CHAR);

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
    @DisplayName("Given sender account number as characters, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_IsChars() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_ALL_CHARS);

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
    @DisplayName("Given sender account number contains spaces, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_ContainsSpaces() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_SPACE);

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
    @DisplayName("Given sender account number as spaces, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_IsSpaces() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_All_SPACES);

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
    @DisplayName("Given sender account number as decimal number, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_IsDecimal() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_DECIMAL);

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
    @DisplayName("Given sender account number contains underscores, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_ContainsUnderscores() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_UNDERSCORE);

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
    @DisplayName("Given sender account number contains emojis, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenSenderAccountNumber_ContainsEmojis() {
        // Given
        when(transaction.getFromAccountNum()).thenReturn(INVALID_NUM_BEAR_EMOJI);

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
        when(transaction.getToAccountNum()).thenReturn(INVALID_NUM_9_DIGITS);

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
        when(transaction.getFromRoutingNum()).thenReturn(INVALID_NUM_8_DIGITS);

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
        when(transaction.getToRoutingNum()).thenReturn(INVALID_NUM_8_DIGITS);

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
    @DisplayName("Given transaction amount is one, " +
            "IllegalArgumentException is thrown")
    void validationSucceed_WhenTransactionAmountIsOne() {
        // Given
        when(transaction.getAmount()).thenReturn(VALID_AMOUNT_ONE);

        // Then
        assertDoesNotThrow(() -> {
            transactionValidator.validateTransaction(
                    LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
        });
    }

    @Test
    @DisplayName("Given transaction amount is very large, " +
            "IllegalArgumentException is thrown")
    void validationSucceed_WhenTransactionAmountIsLarge() {
        // Given
        when(transaction.getAmount()).thenReturn(VALID_AMOUNT_LARGE);

        // Then
        assertDoesNotThrow(() -> {
            transactionValidator.validateTransaction(
                    LOCAL_ROUTING_NUM, AUTHED_ACCOUNT_NUM, transaction);
        });
    }

    @Test
    @DisplayName("Given transaction amount is zero, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenTransactionAmountIsZero() {
        // Given
        when(transaction.getAmount()).thenReturn(INVALID_AMOUNT_ZERO);

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

    @Test
    @DisplayName("Given transaction amount is negative, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenTransactionAmountIsNegative() {
        // Given
        when(transaction.getAmount()).thenReturn(INVALID_AMOUNT_NEGATIVE);

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

    @Test
    @DisplayName("Given transaction amount is negative and very small, " +
            "IllegalArgumentException is thrown")
    void validationFail_WhenTransactionAmountIsNegativeAndSmall() {
        // Given
        when(transaction.getAmount()).thenReturn(INVALID_AMOUNT_SMALL);

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
