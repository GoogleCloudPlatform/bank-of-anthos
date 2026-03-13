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

/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package anthos.samples.bankofanthos.transactionhistory;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for project ID resolution logic in TransactionHistoryApplication.
 * Verifies fix for issue #2309: GOOGLE_CLOUD_PROJECT env var should
 * take precedence over the GCE metadata server project.
 */
class TransactionHistoryApplicationTest {

    @Test
    @DisplayName("When GOOGLE_CLOUD_PROJECT is set, use it over metadata")
    void resolveProjectIdPrefersEnvVar() {
        String result = TransactionHistoryApplication.resolveProjectId(
                "project-b", "project-a");
        assertEquals("project-b", result);
    }

    @Test
    @DisplayName("When GOOGLE_CLOUD_PROJECT is null, fall back to metadata")
    void resolveProjectIdFallsBackToMetadata() {
        String result = TransactionHistoryApplication.resolveProjectId(
                null, "project-a");
        assertEquals("project-a", result);
    }

    @Test
    @DisplayName("When GOOGLE_CLOUD_PROJECT is empty, fall back to metadata")
    void resolveProjectIdFallsBackToMetadataWhenEmpty() {
        String result = TransactionHistoryApplication.resolveProjectId(
                "", "project-a");
        assertEquals("project-a", result);
    }

    @Test
    @DisplayName("When both are null, return empty string")
    void resolveProjectIdReturnsEmptyWhenBothNull() {
        String result = TransactionHistoryApplication.resolveProjectId(
                null, null);
        assertEquals("", result);
    }

    @Test
    @DisplayName("When env var is set and metadata is null, use env var")
    void resolveProjectIdUsesEnvVarWhenMetadataNull() {
        String result = TransactionHistoryApplication.resolveProjectId(
                "project-b", null);
        assertEquals("project-b", result);
    }
}
