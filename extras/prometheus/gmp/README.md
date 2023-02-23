# Google Managed Prometheus (GMP) on a GKE cluster

This directory contains files essential to setup liveness probes for Bank of Anthos' microservices running in GKE using GMP.

* `blackbox-exporter.yaml` - contains the Deployment of [Blackbox exporter](https://github.com/prometheus/blackbox_exporter/).
* `probes.yaml` - contains the GMP PodMonitoring custom resource per microservice. One monitoring configuration per microservice is defined to be run by the Blackbox exporter.
* `rules.yaml` - contains the GMP Rules custom resource.
* `alertmanager.yaml` - contains configuration of Alertmanager to send notifications to Slack channel via Webhook URL.

## How to apply configurations

1. Install Bank of Anthos on your GKE cluster
2. . [Create the Slack application and setup Incoming Webhook.](https://cloud.google.com/kubernetes-engine/docs/tutorials/cluster-notifications-slack#slack_notifications).
3. Edit `alertmanager.yaml` configuration and store it as a Kubernetes secret.

    ```bash
    export SLACK_WEBHOOK_URL="<YOUR_SLACK_WEBHOOK_URL>"
    echo $SLACK_WEBHOOK_URL
    sed -i "s@SLACK_WEBHOOK_URL@$SLACK_WEBHOOK_URL@g" "alertmanager.yaml"
    kubectl create secret generic alertmanager \
        -n gmp-public \
        --from-file=alertmanager.yaml
    ```

4. Deploy [Blackbox exporter](https://github.com/prometheus/blackbox_exporter/).

    ```bash
    kubectl apply -f blackbox-exporter.yaml
    ```

5. Create GMP custom resources

    ```bash
    kubectl apply -f probes.yaml
    kubectl apply -f rules.yaml
    ```
