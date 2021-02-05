#!/bin/bash
source bank-of-anthos.source

if [ $# -ne 1 ]; then
  echo "Usage: $0 {envoy|app}"
  exit 1
elif [ $1 == 'envoy' ]; then
  PORT=9980
elif [ $1 == app ]; then
  PORT=${SERVICE_PORT:-8080}
fi


echo "---
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE}
spec:
  type: ClusterIP
  selector:
    app: ${DEPLOYMENT}
  ports:
  - name: http
    port: 80
    targetPort: ${PORT}
"  | kubectl apply -f -
