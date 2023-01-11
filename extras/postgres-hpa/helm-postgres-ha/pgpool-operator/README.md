# PGPool operator

Watch for StatefulSet workload with labels `"app.kubernetes.io/component": "postgresql"` and `"app.kubernetes.io/instance": "accounts-db"`. Get number of replicas and update Pgpool deployment with name `accounts-db-pgpool` env variable `PGPOOL_BACKEND_NODES` to add PostgreSQL replicas to Pgpool.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install kopf kubernetes
kopf run pgpool.py --standalone --namespace=default --log-format=plain --liveness=http://0.0.0.0:8080/healthz
```

## See also

* (Docker PGPool)[https://github.com/bitnami/bitnami-docker-pgpool/blob/master/README.md]
* (Python Kopf)[https://kopf.readthedocs.io/en/stable/]
