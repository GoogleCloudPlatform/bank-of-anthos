![Continuous Integration](https://github.com/GoogleCloudPlatform/anthos-finance-demo/workflows/Continuous%20Integration/badge.svg)

# Cloud Bank - Anthos Sample Application

This project simulates a bank's payment processing network using [Anthos](https://cloud.google.com/anthos/).
Cloud Bank allows users to create artificial accounts and simulate transactions between accounts.
Cloud Bank was developed to demonstrate how Anthos can be beneficial to financial services companies.


## Architecture

![Architecture Diagram](./architecture.png)

## Installation

Creating a cluster
```
  make cluster \
    PROJECT_ID=$(gcloud config get-value project) ZONE=us-west1-a ACCOUNT=$(gcloud config list account --format "value(core.account)")
```

Deploying Cloud Bank
```
  make deploy \
    PROJECT_ID=$(gcloud config get-value project) ZONE=us-west1-a ACCOUNT=$(gcloud config list account --format "value(core.account)")
```

---

This is not an official Google project.
