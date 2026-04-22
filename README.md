# Bank of Anthos — AKS Edition

A production-grade deployment of the Bank of Anthos sample application,
running on Azure Kubernetes Service (AKS) with enterprise DevOps practices.

> Originally based on [GoogleCloudPlatform/bank-of-anthos](https://github.com/GoogleCloudPlatform/bank-of-anthos).
> Adapted for Azure AKS with GitHub Actions CI/CD, Azure Container Registry,
> External Secrets Operator, cert-manager, and Prometheus monitoring.

---

## Architecture
Internet → Azure Load Balancer → NGINX Gateway Fabric
→ boa-frontend namespace (frontend)
→ boa-backend namespace (userservice, contacts, ledgerwriter,
balancereader, transactionhistory)
→ boa-database namespace (accounts-db, ledger-db)

---

## Services

| Service | Language | Description |
|---|---|---|
| frontend | Python 3.12 / Flask | Web UI — login, signup, transactions |
| userservice | Python 3.12 / Flask | User authentication and JWT signing |
| contacts | Python 3.12 / Flask | Contact management per user |
| ledgerwriter | Java 17 / Spring Boot 3.x | Writes transactions to ledger |
| balancereader | Java 17 / Spring Boot 3.x | Reads account balances |
| transactionhistory | Java 17 / Spring Boot 3.x | Reads transaction history |
| accounts-db | PostgreSQL | Stores user and contact data |
| ledger-db | PostgreSQL | Stores transaction ledger |
| loadgenerator | Python / Locust | Generates synthetic traffic |

---

## Repository Structure
```text
bank-of-anthos/
├── src/
│   ├── frontend/              # Python Flask web UI
│   │   ├── Dockerfile
│   │   ├── frontend.py
│   │   └── requirements.txt
│   ├── accounts/
│   │   ├── userservice/       # Python Flask — auth + JWT
│   │   │   ├── Dockerfile
│   │   │   ├── userservice.py
│   │   │   └── requirements.txt
│   │   ├── contacts/          # Python Flask — contacts
│   │   │   ├── Dockerfile
│   │   │   ├── contacts.py
│   │   │   └── requirements.txt
│   │   └── accounts-db/       # PostgreSQL init scripts
│   ├── ledger/
│   │   ├── ledgerwriter/      # Java Spring Boot — write transactions
│   │   │   ├── Dockerfile
│   │   │   └── pom.xml
│   │   ├── balancereader/     # Java Spring Boot — read balances
│   │   │   ├── Dockerfile
│   │   │   └── pom.xml
│   │   ├── transactionhistory/ # Java Spring Boot — read history
│   │   │   ├── Dockerfile
│   │   │   └── pom.xml
│   │   └── ledger-db/         # PostgreSQL init scripts
│   ├── components/            # Shared Kubernetes component patches
│   └── loadgenerator/         # Locust load testing
├── .github/
│   └── workflows/
│       ├── _reusable-python.yml       # Reusable — Python build
│       ├── _reusable-java.yml         # Reusable — Java build
│       ├── _reusable-scan-push.yml    # Reusable — Trivy + Cosign + ACR
│       ├── _reusable-gitops.yml       # Reusable — update boa-gitops
│       ├── ci-frontend.yml            # Frontend pipeline
│       ├── ci-userservice.yml         # Userservice pipeline
│       ├── ci-contacts.yml            # Contacts pipeline
│       ├── ci-ledgerwriter.yml        # Ledgerwriter pipeline
│       ├── ci-balancereader.yml       # Balancereader pipeline
│       └── ci-transactionhistory.yml  # Transaction history pipeline
├── pom.xml                    # Maven parent POM
├── mvnw                       # Maven wrapper
└── .gitignore

```
---
## CI/CD Pipeline

Each service has a dedicated GitHub Actions pipeline triggered on
path-specific changes. All pipelines share reusable workflows.

### Pipeline Stages

Code Quality    lint + unit tests
Build           Docker image
Security Scan   Trivy (CVE scanning) — blocks on CRITICAL
Sign            Cosign (image signing via Key Vault)
Push            Azure Container Registry (OIDC auth)
GitOps Update   Update image tag in boa-gitops repo
Deploy          ArgoCD auto-syncs to AKS


### Authentication

All pipelines use **OIDC federation** — no stored credentials:
GitHub Actions → OIDC token → Azure AD → ACR push permission

---

## Related Repositories

| Repository | Purpose |
|---|---|
| [terraform-modules](https://github.com/mohdtarique/terraform-modules) | Reusable Terraform modules |
| [terraform-live](https://github.com/mohdtarique/ent-env) | Environment configurations |
| [boa-gitops](https://github.com/mohdtarique/boa-gitops) | Helm charts + ArgoCD apps |

---

## Infrastructure

| Component | Technology |
|---|---|
| Container Orchestration | Azure Kubernetes Service (AKS) 1.33 |
| CNI | Azure CNI powered by Cilium |
| Container Registry | Azure Container Registry (ACR) |
| Secrets Management | Azure Key Vault + ESO |
| GitOps | ArgoCD (App of Apps pattern) |
| Ingress | NGINX Gateway Fabric + Gateway API |
| TLS | cert-manager (self-signed dev / enterprise CA prod) |
| Monitoring | kube-prometheus-stack + Grafana |
| Autoscaling | HPA + KEDA (Prometheus scaler) |
| Storage | Azure Managed Disk (Premium LRS, Retain) |

---

## Security

- **Pod Security Standards**: baseline enforced on all namespaces
- **NetworkPolicy**: default-deny with explicit allow rules (Cilium)
- **Workload Identity**: OIDC federation — no long-lived credentials
- **Image Signing**: Cosign + Sigstore
- **Vulnerability Scanning**: Trivy on every build
- **Secrets**: Never in git — Key Vault via ESO

---

## Getting Started

### Prerequisites
- Azure subscription
- AKS cluster provisioned via [terraform-live](https://github.com/mohdtarique/ent-env)
- ArgoCD deployed and connected to [boa-gitops](https://github.com/mohdtarique/boa-gitops)

### Access the Application
```bash
# Get Gateway IP
kubectl get gateway boa-gateway -n boa-frontend \
  -o jsonpath='{.status.addresses[0].value}'

# HTTP
http://<GATEWAY-IP>

# HTTPS (self-signed cert)
curl -k --resolve boa.graycaster.dev:443:<GATEWAY-IP> \
  https://boa.graycaster.dev
```

---
