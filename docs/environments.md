# Running in Kubernetes Environments

## GKE

Use the default instructions in the [README](/README.md). When Workload Identity is enabled, use the [Workload Identity instructions](/docs/workload-identity.md).

## Non-GKE Kubernetes Clusters

Bank of Anthos was designed to work on any Kubernetes cluster and has no GCP-specific requirements except for Google Cloud Operations instrumentation - the source code of Bank of Anthos will try to export logs, metrics, and traces to GCP by default. This requires authentication to a GCP project - in GKE, this authentication (`GOOGLE_APPLICATION_CREDENTIALS`) [is inferred](https://cloud.google.com/kubernetes-engine/docs/tutorials/authenticating-to-cloud-platform#authenticating_with_service_accounts) from the Node's Compute Engine instance service account (or, if Workload identity is enabled, from a separate service account). In a non GKE cluster, you have to mount those GCP credentials into your Pods directly.

**If you want to turn off metrics/logs/traces export from a non-GKE cluster into Google Cloud Operations**: set `ENABLE_METRICS=false` and `ENABLE_TRACING=false` in each Deployment YAML. No further action is needed, and the Bank of Anthos services will not look for `GOOGLE_APPLICATION_CREDENTIALS` since they don't need to send any telemetry to GCP.

**If you want to export metrics/logs/traces from a non-GKE cluster into Google Cloud Operations**:

1. Create a Google Cloud project or navigate into one you've already created. Ensure you've created a Google Cloud Operations workspace for your project.

2. Create a Service Account. Grant the Service Account the following roles: `Monitoring Metric Writer`, `Cloud Trace Agent`, `Logs Writer`.

3. Download a Service Account key (JSON) to your local machine.

4. Create a Kubernetes secret in your non-GKE cluster, using the key you downloaded:

```
kubectl create secret generic pubsub-key --from-file=key.json=PATH-TO-KEY-FILE.json
```

5. Update your Deployment YAMLs to mount in that secret as your `GOOGLE_APPLICATION_CREDENTIALS` env variable. [See this example](https://cloud.google.com/kubernetes-engine/docs/tutorials/authenticating-to-cloud-platform#importing_credentials_as_a_secret) for how to mount a secret as an env variable in a Pod.

6. Deploy the app, where the `ENABLE_METRICS` and `ENABLE_TRACING` variables are both set to `true`.


