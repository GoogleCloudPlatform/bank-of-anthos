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
import org.junit.Rule;
import org.junit.contrib.java.lang.system.EnvironmentVariables;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;

class LedgerWriterControllerTest {

    private LedgerWriterController ledgerWriterController;

    @Mock
    private JWTVerifier verifier;

    @Rule
    private EnvironmentVariables environmentVariables;

    private static final String VERSION = "v0.1.0";
    private static final String LOCAL_ROUTING_NUM = "123456789";
    private static final String BALANCES_API_ADDR = "balancereader:8080";

    @BeforeEach
    void setUp() {
        environmentVariables = new EnvironmentVariables();
        ledgerWriterController = new LedgerWriterController(verifier,
                LOCAL_ROUTING_NUM, BALANCES_API_ADDR, VERSION);
    }

    @Test
    @DisplayName("Given version number in the environment, " +
            "return a ResponseEntity with the version number")
    void version() {
        // Given
        environmentVariables.set("VERSION", VERSION);

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
    void addTransaction() {
        // TODO: [issue-52] add tests to addTransaction
    }
}
