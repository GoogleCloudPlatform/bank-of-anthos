# Bank of Anthos Helm Chart

This Helm chart deploys the Bank of Anthos (formerly Cymbal Bank) microservices application on Kubernetes. Bank of Anthos is a sample retail banking application that demonstrates modern cloud-native development practices and Google Cloud technologies.

## Architecture Overview

Bank of Anthos consists of multiple microservices:

- **Frontend** - Web interface for the banking application
- **User Service** - Handles user authentication and JWT token management
- **Contacts** - Manages user contact information
- **Balance Reader** - Provides account balance information
- **Ledger Writer** - Processes financial transactions
- **Transaction History** - Retrieves transaction records
- **Accounts DB** - PostgreSQL database for user accounts
- **Ledger DB** - PostgreSQL database for financial transactions
- **Load Generator** - Simulates user traffic for testing

## JWT Authentication

As described in the [Google Cloud GKE scalable apps tutorial](https://cloud.google.com/kubernetes-engine/docs/learn/scalable-apps-basic-deployment), Bank of Anthos uses JSON Web Tokens (JWTs) to handle user authentication. JWTs use asymmetric key pairs to sign and verify tokens. In Bank of Anthos, the `userservice` creates and signs tokens with an RSA private key when a user signs in, and the other services use the corresponding public key to validate the user.

### Creating JWT Keys

Create an RS256 JWT that's 4,096 bits in strength:

```bash
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
```

_If needed, download and install the OpenSSL tools for your platform._

### Creating Kubernetes Secret

A Kubernetes Secret can store sensitive data like keys or passwords. Workloads that run in your cluster can then access the Secret to get the sensitive data instead of hard-coding it in the application.

Create a Kubernetes Secret from the key file you created in the previous step for Bank of Anthos to use with authentication requests:

```bash
kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

## Monitoring and Tracing Configuration

### Why Monitoring and Tracing are Disabled by Default

In this Helm chart configuration, monitoring and tracing are set to `false` by default for the following reasons:

1. **Simplified Local Development** - Reduces complexity during initial deployment and local testing
2. **Resource Optimization** - Avoids overhead from monitoring agents in development environments
3. **Step-by-step Learning** - Allows users to enable monitoring in later stages to demonstrate proper observability setup
4. **Cost Management** - Prevents unnecessary charges during development phases

### Spring Autoconfigure Exclusion

The `SPRING_AUTOCONFIGURE_EXCLUDE` environment variable is configured to exclude Google Cloud Platform (GCP) autoconfiguration:

```yaml
springAutoconfigureExclude: "com.google.cloud.spring.autoconfigure.core.GcpContextAutoConfiguration,com.google.cloud.spring.autoconfigure.metrics.GcpStackdriverMetricsAutoConfiguration,com.google.cloud.spring.autoconfigure.trace.StackdriverTraceAutoConfiguration"
```

**Purpose**: This is a configuration hack to exclude the GCP autoconfiguration for straightforward local development. It prevents Spring Boot from automatically configuring GCP services like Stackdriver (Cloud Monitoring) when running outside of Google Cloud Platform.

## Service Account Setup

### Default Configuration

The Helm chart uses a default service account configuration suitable for development:

```yaml
global:
  serviceAccountName: bank-of-anthos
```

### Production Setup with Workload Identity

For production deployments on Google Kubernetes Engine (GKE), you should configure Workload Identity as mentioned in the [Google Cloud documentation](https://cloud.google.com/kubernetes-engine/docs/learn/scalable-apps-basic-deployment):

1. **Create a Google Service Account**:

```bash
gcloud iam service-accounts create bank-of-anthos-sa
```

2. **Grant necessary permissions**:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:bank-of-anthos-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudtrace.agent"
```

3. **Configure Workload Identity**:

```bash
gcloud iam service-accounts add-iam-policy-binding \
    bank-of-anthos-sa@PROJECT_ID.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:PROJECT_ID.svc.id.goog[default/bank-of-anthos]"
```

4. **Update the service account annotation** in your values.yaml:

```yaml
# In production, replace with proper workload identity annotation:
# iam.gke.io/gcp-service-account: bank-of-anthos-sa@PROJECT_ID.iam.gserviceaccount.com
```

## Prerequisites

- Kubernetes cluster (GKE Autopilot recommended)
- Helm 3.x
- OpenSSL (for JWT key generation)
- kubectl configured for your cluster

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/GoogleCloudPlatform/bank-of-anthos.git
cd bank-of-anthos/helm-charts/bank-of-anthos-chart
```

2. **Generate JWT keys** (if not already created):

```bash
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
```

3. **Create JWT secret**:

```bash
kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

4. **Install the Helm chart**:

```bash
helm install bank-of-anthos . --namespace default
```

## Configuration

### Key Configuration Options

| Parameter                    | Description                | Default                                                       |
| ---------------------------- | -------------------------- | ------------------------------------------------------------- |
| `global.application`         | Application name           | `bank-of-anthos`                                              |
| `global.environment`         | Environment name           | `development`                                                 |
| `global.version`             | Application version        | `v0.6.7`                                                      |
| `global.imageRegistry`       | Container registry         | `us-central1-docker.pkg.dev/bank-of-anthos-ci/bank-of-anthos` |
| `frontend.service.type`      | Frontend service type      | `LoadBalancer`                                                |
| `config.demo.enabled`        | Enable demo data           | `true`                                                        |
| `config.demo.username`       | Demo username              | `testuser`                                                    |
| `config.demo.password`       | Demo password              | `bankofanthos`                                                |
| `istio.enabled`              | Enable Istio service mesh  | `false`                                                       |
| `monitoring.tracing.enabled` | Enable distributed tracing | `false`                                                       |
| `monitoring.metrics.enabled` | Enable metrics collection  | `false`                                                       |

### Enabling Production Features

For production deployments, update your values.yaml:

```yaml
global:
  environment: production

monitoring:
  tracing:
    enabled: true
  metrics:
    enabled: true

istio:
  enabled: true

config:
  demo:
    enabled: false
```

## Accessing the Application

After deployment, get the external IP address:

```bash
kubectl get ingress frontend | awk '{print $4}'
```

Or if using LoadBalancer service:

```bash
kubectl get service frontend
```

Open the IP address in your web browser to access Bank of Anthos.

**Default credentials**:

- Username: `testuser`
- Password: `bankofanthos`

## Monitoring and Observability

### Enable Google Cloud Monitoring

To enable comprehensive monitoring as described in the [Google Cloud tutorial](https://cloud.google.com/kubernetes-engine/docs/learn/scalable-apps-basic-deployment):

1. **Update values.yaml**:

```yaml
monitoring:
  tracing:
    enabled: true
  metrics:
    enabled: true
```

2. **Remove Spring autoconfigure exclusions** for production:

```yaml
balanceReader:
  env:
    springAutoconfigureExclude: ""
```

### View Cluster Metrics

1. Go to the Google Kubernetes Engine **Clusters** page in the Google Cloud console
2. Select your cluster and navigate to the **Observability** tab
3. Examine CPU, Memory, and other metrics
4. Use the **Logs** tab to view application logs
5. Check the **App Errors** tab for warnings and events

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check if JWT secret exists

```bash
kubectl get secret jwt-key
```

2. **Service mesh issues**: Ensure Istio is properly configured if enabled

3. **Database connection failures**: Verify database services are running

```bash
kubectl get pods -l tier=db
```

4. **Resource constraints**: Check if your cluster has sufficient resources

### Useful Commands

```bash
# Check all pods status
kubectl get pods

# View pod logs
kubectl logs -l app=frontend

# Check services
kubectl get services

# Describe problematic pods
kubectl describe pod <pod-name>
```

## Security Considerations

- JWT keys should be rotated regularly in production
- Use proper RBAC configurations
- Enable Pod Security Standards
- Configure network policies
- Use Workload Identity for GKE deployments
- Disable demo data in production environments

## References

- [Bank of Anthos GitHub Repository](https://github.com/GoogleCloudPlatform/bank-of-anthos)
- [Google Cloud GKE Scalable Apps Tutorial](https://cloud.google.com/kubernetes-engine/docs/learn/scalable-apps-basic-deployment)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Istio Service Mesh](https://istio.io/latest/docs/)

## Contributing

This Helm chart is based on the Bank of Anthos sample application. For contributions and issues, please refer to the main [Bank of Anthos repository](https://github.com/GoogleCloudPlatform/bank-of-anthos).
