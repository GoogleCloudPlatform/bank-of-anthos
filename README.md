![Continuous Integration](https://github.com/GoogleCloudPlatform/anthos-finance-demo/workflows/Continuous%20Integration/badge.svg)

# Bank of Anthos

This project simulates a bank's payment processing network using [Anthos](https://cloud.google.com/anthos/).
Bank of Anthos allows users to create artificial accounts and simulate transactions between accounts.
Bank of Anthos was developed to create an end-to-end sample demonstrating Anthos best practices.

## Architecture

![Architecture Diagram](./architecture.png)


| Service                                          | Language      | Description                                                                                                                                  |
| ------------------------------------------------ | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [frontend](./src/frontend)                       | Python        | Exposes an HTTP server to serve the website. Contains login page, signup page, and home page.                                                |
| [ledger-writer](./src/ledgerwriter)              | Java          | Accepts and validates incoming transactions before writing them to the ledger.                                                               |
| [balance-reader](./src/balancereader)            | Java          | Provides efficient readable cache of user balances, as read from `ledger-db`.                                                                |
| [transaction-history](./src/transactionhistory)  | Java          | Provides efficient readable cache of past transactions, as read from `ledger-db`.                                                            |
| [ledger-db](./src/ledger-db)                     | Redis Streams | Append-only ledger of all transactions. Comes pre-populated with past transaction data for default user.                                     |
| [user-service](./src/userservice)                | Python        | Manages user accounts and authentication. Signs JWTs used for authentication by other services.                                              |
| [contacts](./src/contacts)                       | Python        | Stores list of other accounts associated with a user. Used for drop down in "Send Payment" and "Deposit" forms (mock, uses hard-coded data). |
| [accounts-db](./src/accounts-db)                 | MongoDB       | Database for user accounts and associated data. Comes pre-populated with default user.                                                       |
| [loadgenerator](./src/loadgenerator)             | Python/Locust | Continuously sends requests imitating users to the frontend. Periodically created new accounts and simulates transactions between them.      |


## Installation

### Creating a Cluster

```
  make cluster \
    PROJECT_ID=$(gcloud config get-value project) \ # required
    ZONE=us-west1-a \                               # optional. default: us-west1-a
    CLUSTER=cloud-bank                              # optional. default: cloud-bank
```

### Deployment

```
skaffold run --default-repo=gcr.io/${PROJECT_ID}
```

## Continuous Integratioon

GitHub Actions workflows [described here](./.github/workflows)

---

This is not an official Google project.
