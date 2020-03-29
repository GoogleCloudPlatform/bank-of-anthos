![Continuous Integration](https://github.com/GoogleCloudPlatform/anthos-finance-demo/workflows/Continuous%20Integration/badge.svg)

# Bank of Anthos

This project simulates a bank's payment processing network using [Anthos](https://cloud.google.com/anthos/).
Bank of Anthos allows users to create artificial accounts and simulate transactions between accounts.
Bank of Anthos was developed to create an end-to-end sample demonstrating Anthos best practices.

## Architecture

![Architecture Diagram](./docs/architecture.png)


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

### 1 - Project setup

Create a GCP project or use an existing project. Then, set the Project ID variable.

```
PROJECT_ID=<your-project-id>
```

### 1 - Create a Kubernetes cluster

```
gcloud beta container clusters create bank-of-anthos \
    --project=${PROJECT_ID} --zone=us-central1-b \
    --machine-type=n1-standard-2 --num-nodes=4
```

### 2 - Generate RSA key pair secret

```
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

### 3 - Deploy Kubernetes manifests

```
kubectl apply -f ./kubernetes-manifests
```

After 1-2 minutes, you should see that all the pods are running:

```
kubectl get pods
```

*Example output - do not copy*

```
NAME                                  READY   STATUS    RESTARTS   AGE
accounts-db-6f589464bc-6r7b7          1/1     Running   0          99s
balancereader-797bf6d7c5-8xvp6        1/1     Running   0          99s
contacts-769c4fb556-25pg2             1/1     Running   0          98s
frontend-7c96b54f6b-zkdbz             1/1     Running   0          98s
ledger-db-5b78474d4f-p6xcb            1/1     Running   0          98s
ledgerwriter-84bf44b95d-65mqf         1/1     Running   0          97s
loadgenerator-559667b6ff-4zsvb        1/1     Running   0          97s
transactionhistory-5569754896-z94cn   1/1     Running   0          97s
userservice-78dc876bff-pdhtl          1/1     Running   0          96s
```

### 4 - Get the frontend IP

```
kubectl get svc frontend | awk '{print $4}'
```

*Example output - do not copy*

```
EXTERNAL-IP
35.223.69.29
```

### 5 - Navigate to the web frontend

Paste the frontend IP into a web browser. You should see a log-in screen:

![](/docs/login.png)

Using the pre-populated username and password fields, log in as `testuser`. You should see a list of transactions, indicating that the frontend can successfully reach the backend transaction services.

![](/docs/transactions.png)


## Local Development

See the [Development Guide](./docs/development.md) for instructions on how to build and develop services locally, and the [Contributing Guide](./CONTRIBUTING.md) for pull request and code review guidelines.

---

This is not an official Google project.