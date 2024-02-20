# Setup for Fleet Workload Identity

[fleet Workload Identity](https://cloud.google.com/anthos/fleet-management/docs/use-workload-identity)

Must use skaffold

# Local

Not yet implemented

# Development

Not yet implemented

# Staging

Not yet implemented

# Production

- Set the required environment variables

  ```
  PROD_PROJECT_ID="<your project ID>"
  PROD_FWI_WORKLOAD_IDENTITY_POOL="${PROJECT_ID}.svc.id.goog"

  CLUSTER_MEMBERSHIP_NAME="cluster-prod"
  PROD_FWI_PROVIDER="https://gkehub.googleapis.com/projects/${PROD_PROJECT_ID}/locations/global/memberships/${CLUSTER_MEMBERSHIP_NAME}"

  PROD_GOOGLE_CLOUD_BACKEND_SERVICE_ACCOUNT="backend@${PROD_PROJECT_ID}.iam.gserviceaccount.com"
  PROD_K8S_BACKEND_SERVICE_ACCOUNT="backend"
  PROD_GOOGLE_CLOUD_FRONTEND_SERVICE_ACCOUNT="backend@${PROD_PROJECT_ID}.iam.gserviceaccount.com"
  PROD_K8S_FRONTEND_SERVICE_ACCOUNT="frontend"

  PROD_K8S_NAMESPACE="cymbal-bank"
  PROD_ACCOUNT_DB_DATABASE_NAME="account-db"
  PROD_ACCOUNT_DB_USERNAME="admin"
  PROD_ACCOUNT_DB_PASSWORD="admin"
  PROD_LEDGER_DB_DATABASE_NAME="account-db"
  PROD_LEDGER_DB_USERNAME="admin"
  PROD_LEDGER_DB_PASSWORD="admin"
  ```

- Prepare the manifest files

  ```
  echo "Configure the Kubernetes namespace" && \
  git restore src/components/production/kustomization.yaml && \
  sed -i "s/namespace: bank-of-anthos-production/namespace: ${PROD_K8S_NAMESPACE}/" src/components/production/kustomization.yaml
  ```

  ```
  echo "Configure the Kubernetes service accounts" && \
  git restore src/components/backend/kustomization.yaml && \
  sed -i "s/value: bank-of-anthos/value: ${PROD_K8S_BACKEND_SERVICE_ACCOUNT}/" src/components/backend/kustomization.yaml  && \
  git restore src/components/bank-of-anthos/kustomization.yaml && \
  sed -i "s/value: bank-of-anthos/value: ${PROD_K8S_BACKEND_SERVICE_ACCOUNT}/" src/components/bank-of-anthos/kustomization.yaml && \
  git restore src/components/frontend/kustomization.yaml && \
  sed -i "s/value: bank-of-anthos/value: ${PROD_K8S_FRONTEND_SERVICE_ACCOUNT}/" src/components/frontend/kustomization.yaml
  ```

  ```
  echo "Configure the account-db settings" && \
  git restore src/accounts/accounts-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)ACCOUNTS_DB_URI:.*$|\1ACCOUNTS_DB_URI: postgresql://${PROD_ACCOUNT_DB_USERNAME}:${PROD_ACCOUNT_DB_PASSWORD}@127.0.0.1:5432/${PROD_ACCOUNT_DB_DATABASE_NAME}|' src/accounts/accounts-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_DB:.*$|\1POSTGRES_DB: ${PROD_ACCOUNT_DB_DATABASE_NAME}|' src/accounts/accounts-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_PASSWORD:.*$|\1POSTGRES_PASSWORD: ${PROD_ACCOUNT_DB_PASSWORD}|' src/accounts/accounts-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_USER:.*$|\1POSTGRES_USER: ${PROD_ACCOUNT_DB_USERNAME}|' src/accounts/accounts-db/k8s/base/config.yaml && \
  git restore src/components/cloud-sql/accounts-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)ACCOUNTS_DB_URI:.*$|\1ACCOUNTS_DB_URI: postgresql://${PROD_ACCOUNT_DB_USERNAME}:${PROD_ACCOUNT_DB_PASSWORD}@127.0.0.1:5432/${PROD_ACCOUNT_DB_DATABASE_NAME}|' src/components/cloud-sql/accounts-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_DB:.*$|\1POSTGRES_DB: ${PROD_ACCOUNT_DB_DATABASE_NAME}|' src/components/cloud-sql/accounts-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_PASSWORD:.*$|\1POSTGRES_PASSWORD: ${PROD_ACCOUNT_DB_PASSWORD}|' src/components/cloud-sql/accounts-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_USER:.*$|\1POSTGRES_USER: ${PROD_ACCOUNT_DB_USERNAME}|' src/components/cloud-sql/accounts-db.yaml
  ```

  ```
  echo "Configure the ledger-db settings" && \
  git restore src/ledger/ledger-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_DB:.*$|\1POSTGRES_DB: ${PROD_LEDGER_DB_DATABASE_NAME}|' src/ledger/ledger-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_PASSWORD:.*$|\1POSTGRES_PASSWORD: ${PROD_LEDGER_DB_PASSWORD}|' src/ledger/ledger-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_USER:.*$|\1POSTGRES_USER: ${PROD_LEDGER_DB_USERNAME}|' src/ledger/ledger-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)SPRING_DATASOURCE_PASSWORD:.*$|\1SPRING_DATASOURCE_PASSWORD: ${PROD_LEDGER_DB_PASSWORD}|' src/ledger/ledger-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)SPRING_DATASOURCE_URL:.*$|\1SPRING_DATASOURCE_URL: jdbc:postgresql://127.0.0.1:5432/${PROD_LEDGER_DB_DATABASE_NAME}|' src/ledger/ledger-db/k8s/base/config.yaml && \
  sed -i 's|^\([[:blank:]]*\)SPRING_DATASOURCE_USERNAME:.*$|\1SPRING_DATASOURCE_USERNAME: ${PROD_LEDGER_DB_USERNAME}|' src/ledger/ledger-db/k8s/base/config.yaml && \
  git restore src/components/cloud-sql/ledger-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_DB:.*$|\1POSTGRES_DB: ${PROD_LEDGER_DB_DATABASE_NAME}|' src/components/cloud-sql/ledger-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_PASSWORD:.*$|\1POSTGRES_PASSWORD: ${PROD_LEDGER_DB_PASSWORD}|' src/components/cloud-sql/ledger-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)POSTGRES_USER:.*$|\1POSTGRES_USER: ${PROD_LEDGER_DB_USERNAME}|' src/components/cloud-sql/ledger-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)SPRING_DATASOURCE_PASSWORD:.*$|\1SPRING_DATASOURCE_PASSWORD: ${google_sql_user.cloud_sql_admin_user.password}|' src/components/cloud-sql/ledger-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)SPRING_DATASOURCE_URL:.*$|\1SPRING_DATASOURCE_URL: jdbc:postgresql://127.0.0.1:5432/${PROD_LEDGER_DB_DATABASE_NAME}|' src/components/cloud-sql/ledger-db.yaml && \
  sed -i 's|^\([[:blank:]]*\)SPRING_DATASOURCE_USERNAME:.*$|\1SPRING_DATASOURCE_USERNAME: ${PROD_LEDGER_DB_USERNAME}|' src/components/cloud-sql/ledger-db.yaml
  ```

  ```
  echo "Configure FWI audience" && \
  git restore src/components/backend-fwi/add-fwi.yaml && \
  sed -i 's|audience: FWI_WORKLOAD_IDENTITY_POOL|audience: ${PROD_FWI_WORKLOAD_IDENTITY_POOL}|' src/components/backend-fwi/add-fwi.yaml && \
  git restore src/components/cloud-sql-fwi/add-fwi.yaml && \
  sed -i 's|audience: FWI_WORKLOAD_IDENTITY_POOL|audience: ${PROD_FWI_WORKLOAD_IDENTITY_POOL}|' src/components/cloud-sql-fwi/add-fwi.yaml && \
  git restore src/components/frontend-fwi/add-fwi.yaml && \
  sed -i 's|audience: FWI_WORKLOAD_IDENTITY_POOL|audience: ${PROD_FWI_WORKLOAD_IDENTITY_POOL}|' src/components/frontend-fwi/add-fwi.yaml
  ```

- Create the Kubernetes configmaps

  ```
  cat <<EOT > backend-adc.json
  {
      "audience": "identitynamespace:${PROD_FWI_WORKLOAD_IDENTITY_POOL}:${PROD_FWI_PROVIDER}",
      "credential_source": {
          "file": "/var/run/secrets/tokens/gcp-ksa/token"
      },
      "project_id": "${PROD_PROJECT_ID}",
      "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${PROD_GOOGLE_CLOUD_BACKEND_SERVICE_ACCOUNT}:generateAccessToken",
      "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
      "token_url": "https://sts.googleapis.com/v1/token",
      "type": "external_account"
  }
  EOT && \
  kubectl create --namespace=${PROD_K8S_NAMESPACE} configmap backend-adc --from-file=backend-adc.json
  ```

  ```
  cat <<EOT > frontend-adc.json
  {
      "audience": "identitynamespace:${PROD_FWI_WORKLOAD_IDENTITY_POOL}:${PROD_FWI_PROVIDER}",
      "credential_source": {
          "file": "/var/run/secrets/tokens/gcp-ksa/token"
      },
      "project_id": "${PROD_PROJECT_ID}",
      "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${PROD_GOOGLE_CLOUD_FRONTEND_SERVICE_ACCOUNT}:generateAccessToken",
      "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
      "token_url": "https://sts.googleapis.com/v1/token",
      "type": "external_account"
  }
  EOT && \
  kubectl create --namespace=${PROD_K8S_NAMESPACE} configmap frontend-adc --from-file=frontend-adc.json
  ```

- Deploy the application

  ```
  skaffold run \
  --profile production,production-fwi \
  --skip-tests=true
  ```
