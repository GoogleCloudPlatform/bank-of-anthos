# Open source software (OSS) Prometheus on a GKE cluster

This directory contains files essential to setup liveness probes for Bank of Anthos' microservices running in GKE using OSS Prometheus.

* `values.yaml` - contains the configurations for the [OSS Prometheus helm chart](https://github.com/bitnami/charts/tree/main/bitnami/kube-prometheus).
* `probes.yaml` - contains the Probe custom resource per microservice. One monitoring configuration per microservice is defined.
* `rules.yaml` - contains the PrometheusRule custom resource.
* `alertmanagerconfig.yaml` - contains configuration of AlertmanagerConfig custom resource. This resource defines the configurations necessary to send notifications to a Slack channel via Webhook URL.

## How to apply configurations

1. Install Bank of Anthos on your GKE cluster
2. Install OSS Prometheus with helm.

    ```bash
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm install tutorial bitnami/kube-prometheus \
        --version 8.2.2 \
        --values values.yaml \
        --wait
    ```

3. [Create the Slack application and setup Incoming Webhook.](https://cloud.google.com/kubernetes-engine/docs/tutorials/cluster-notifications-slack#slack_notifications).
4. Create a Kubernetes secret with Slack Webhook Url

    ```bash
    kubectl create secret generic alertmanager-slack-webhook --from-literal webhookURL=<YOUR_SLACK_WEBHOOK_URL>
    ```

5. Create OSS Prometheus operator custom resources.

    ```bash
    kubectl apply -f alertmanagerconfig.yaml
    kubectl apply -f probes.yaml
    kubectl apply -f rules.yaml
    ```
