
# Setup for Workload Identity clusters

If you have enabled [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) on your GKE cluster ([a requirement for Anthos Service Mesh](https://cloud.google.com/service-mesh/docs/gke-anthos-cli-new-cluster#requirements)), follow these instructions to ensure that Bank of Anthos pods can communicate with GCP APIs.

*Note* - These instructions have only been validated in GKE on GCP clusters. [Workload Identity is not yet supported](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#creating_a_relationship_between_ksas_and_gsas) in Anthos GKE on Prem. 


1. **Set up Workload Identity** on your GKE cluster [using the instructions here](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#enable_on_new_cluster). These instructions create the Kubernetes Service Account (KSA) and Google Service Account (GSA) that the Bank of Anthos pods will use to authenticate to GCP. Take note of what Kubernetes `namespace` you use during setup.

2. **Add IAM Roles** to your GSA. These roles allow workload identity-enabled Bank of Anthos pods to send traces and metrics to GCP. 

```bash
PROJECT_ID=<your-gcp-project-id>
GSA_NAME=<your-gsa>

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/cloudtrace.agent

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/monitoring.metricWriter
```

3. **Generate Bank of Anthos manifests** using your KSA as the Pod service account. In `kubernetes-manifests/`, replace `serviceAccountName: default` with the name of your KSA. (**Note** - sample below is Bash.)

```bash

KSA_NAME=<your-ksa>

mkdir -p wi-kubernetes-manifests
FILES="`pwd`/kubernetes-manifests/*"
for f in $FILES; do
    echo "Processing $f..."
    sed "s/serviceAccountName: default/serviceAccountName: ${KSA_NAME}/g" $f > wi-kubernetes-manifests/`basename $f`
done
```

4. **Deploy Bank of Anthos** to your GKE cluster using the install instructions above, except make sure that instead of the default namespace, you're deploying the manifests into your KSA namespace: 

```bash
NAMESPACE=<your-ksa-namespace>
kubectl apply -n ${NAMESPACE} -f ./wi-kubernetes-manifests 
```
