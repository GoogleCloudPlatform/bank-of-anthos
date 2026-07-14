### Fixes #2309

### Background 
The Java ledger services (`balancereader`, `ledgerwriter`, `transactionhistory`) were resolving their GCP Project ID solely via `MetadataConfig.getProjectId()`, which queries the GCE metadata server. This meant they always used the hosting project's ID, ignoring the `GOOGLE_CLOUD_PROJECT` environment variable. This behavior broke cross-project Workload Identity setups (e.g., GKE cluster in Project A, Service Account/Monitoring in Project B).

### Change Summary
- **Java Services:** Updated `projectId()` in `BalanceReaderApplication.java`, `LedgerWriterApplication.java`, and `TransactionHistoryApplication.java` to check `System.getenv("GOOGLE_CLOUD_PROJECT")` first. It falls back to the metadata server only if the env var is missing.
- **Spring Config:** Added `spring.cloud.gcp.project-id=${GOOGLE_CLOUD_PROJECT:}` to `application.properties` for all three services to ensure Spring Cloud GCP tracing also respects the environment variable.
- **Kubernetes Manifests:** Added a commented-out `GOOGLE_CLOUD_PROJECT` field to the `environment-config` ConfigMap in `config.yaml` to document how to configure this.
- **Tests:** Added unit tests for `resolveProjectId` logic in all three services.

### Additional Notes
This change is non-breaking for existing deployments as usage of the `GOOGLE_CLOUD_PROJECT` environment variable is optional. Behavior defaults to the metadata server (existing behavior) if the variable is unset.

### Testing Procedure
**Automated Testing:**
- Ran `mvnw test` for all 3 services.
- **Results:** 53 tests passed, 0 failures.

**Manual Verification (GKE):**
1. Built custom Jib images for the 3 modified services.
2. Deployed to a GKE cluster with `GOOGLE_CLOUD_PROJECT` set in the ConfigMap.
3. **Verification:**
    - Confirmed `config.yaml` applied the environment variable.
    - Verified pods started successfully (`Running` status).
    - Verified metrics and logs were correctly exported to the target GCP project in Cloud Monitoring.

### Related PRs or Issues 
Fixes #2309
