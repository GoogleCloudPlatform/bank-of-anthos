# Kubernetes, Helm Prometheus and Grafana for Bank-of-Anthos

## Verify Prerequisites and install the running application

### 1 - Ensure you have a k8s cluster and can reach it

```sh
kubectl version
```

Ensure that helm 3 is installed

```sh
helm version
```

### 2 - Install Prometheus and Grafana

Install prometheus with Helm via the setup_prometheus.sh script

```sh
bash setup_grafana_prometheus.sh
```

Port forward access to prometheus (http://localhost:9090) and Grafana (http://localhost:3000)

```sh
kubectl port-forward svc/kube-prometheus-stack-server -n monitoring 9090:80 >& /dev/null &

kubectl port-forward svc/grafana -n monitoring 3000:80 >& /dev/hull &
```

