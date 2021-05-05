# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/bin/bash


echo "☸️ Creating clusters..." 
gcloud container clusters create ${CLUSTER_1_NAME} \
	--project=${PROJECT_ID} --zone=${CLUSTER_1_ZONE} \
	--machine-type=e2-standard-4 --num-nodes=4 \
	--workload-pool="${PROJECT_ID}.svc.id.goog" --enable-ip-alias --async

gcloud container clusters create ${CLUSTER_2_NAME} \
	--project=${PROJECT_ID} --zone=${CLUSTER_2_ZONE} \
	--machine-type=e2-standard-4 --num-nodes=4 \
	--workload-pool="${PROJECT_ID}.svc.id.goog" --enable-ip-alias


gcloud container clusters get-credentials ${CLUSTER_1_NAME} --zone ${CLUSTER_1_ZONE} --project ${PROJECT_ID}
kubectx cluster1="gke_${PROJECT_ID}_${CLUSTER_1_ZONE}_${CLUSTER_1_NAME}"

gcloud container clusters get-credentials ${CLUSTER_2_NAME} --zone ${CLUSTER_2_ZONE} --project ${PROJECT_ID}
kubectx cluster2="gke_${PROJECT_ID}_${CLUSTER_2_ZONE}_${CLUSTER_2_NAME}"

echo "Registering clusters to Anthos..."
../cloudsql-multicluster/register_clusters.sh

echo "🌨️ Setting up Workload Identity..."
kubectx cluster1
../cloudsql/setup_workload_identity.sh

kubectx cluster2
../cloudsql/setup_workload_identity.sh

echo "Setting up cloud SQL..."
../cloudsql/create_cloudsql_instance.sh
INSTANCE_NAME='bank-of-anthos-db-multi'
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format='value(connectionName)')

kubectx cluster1
kubectl create secret -n ${NAMESPACE} generic cloud-sql-admin \
 --from-literal=username=admin --from-literal=password=admin \
 --from-literal=connectionName=${INSTANCE_CONNECTION_NAME}

kubectx cluster2
kubectl create secret -n ${NAMESPACE} generic cloud-sql-admin \
 --from-literal=username=admin --from-literal=password=admin \
 --from-literal=connectionName=${INSTANCE_CONNECTION_NAME}

echo "Deploying Bank of Anthos..."
kubectx cluster1
kubectl apply  -n ${NAMESPACE} -f ../cloudsql/kubernetes-manifests/config.yaml
kubectl apply -n ${NAMESPACE} -f ../cloudsql/populate-jobs
kubectl apply  -n ${NAMESPACE} -f ../cloudsql/kubernetes-manifests
kubectl delete svc frontend

kubectx cluster2
kubectl apply  -n ${NAMESPACE} -f ../cloudsql/kubernetes-manifests
kubectl delete svc frontend

echo "Creating a static IP..."
gcloud compute addresses create boa-multi-cluster-ip --global
IP=`gcloud compute addresses describe boa-multi-cluster-ip --global --format="value(address)"`

echo "Injecting the static IP value into the MCI resource..."
gsed -i "s/STATIC_IP/${IP}/g" multicluster-ingress-https.yaml

echo "Creating SSL certificate..."
openssl genrsa -out private.key 2048

openssl req -new -key private.key -out frontend.csr \
    -subj "/CN=${IP}"

openssl x509 -req -days 365 -in frontend.csr -signkey private.key \
    -out public.crt

kubectx cluster1 
kubectl create secret tls frontend-tls-multi --cert=public.crt --key=private.key

echo "Deploying Multicluster Ingress..."
kubectl apply -n ${NAMESPACE} -f multicluster-ingress-https.yaml