
# Setup for using a CloudSQL database for the accounts-db

This setup assumes you have enabled [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) on your GKE cluster ([a requirement for Anthos Service Mesh](https://cloud.google.com/service-mesh/docs/gke-anthos-cli-new-cluster#requirements) to ensure that Bank of Anthos pods can communicate with GCP APIs.

*Note* - These instructions have only been validated in GKE on GCP clusters. [Workload Identity is not yet supported](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#creating_a_relationship_between_ksas_and_gsas) in Anthos GKE on Prem. 

## Cloud SQL instance and database
1. Create instance
```bash
INSTANCE_NAME='bofa-instance'
PROJECT_ID=<your-gcp-project-id>
gcloud sql instances create $INSTANCE_NAME --database-version=POSTGRES_12 --tier=db-custom-1-3840 --region=us-west1
```
2. Get instance connection name and store in env variable
```bash
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format='value(connectionName)')
```
3. Create `accounts-admin` user. Note: The username and password here must match those in `extras/cloudsql/accounts-db.yaml`
```bash
gcloud sql users create accounts-admin \
   --instance=$INSTANCE_NAME --password=accounts-pwd
```
4. Create `accounts-db` database
```bash
gcloud sql databases create accounts-db --instance=$INSTANCE_NAME
```
5. Install the Cloud SQL proxy by following the instructions [here](https://cloud.google.com/sql/docs/mysql/sql-proxy#install)
Note: if you are running this from Cloud Shell you can skip this step.)
6. Connect to the database
```bash
gcloud beta sql connect $INSTANCE_NAME --project=$PROJECT_ID --user=accounts-admin --database=accounts-db
```
7. Run the SQL commands in [0-accounts-schema.sql](../src/accounts-db/initdb/0-accounts-schema.sql) script on your database to create the tables.

## GSA, KSA and permissions
1. **Create namespace** for Bank of Anthos services
```bash
kubectl create namespace bofa
```
2. **Create Kubernetes Service Account** used by services
```bash
NAMESPACE=bofa
KSA_NAME=bofa-ksa
kubectl create serviceaccount --namespace $NAMESPACE $KSA_NAME
```
3. **Create Google Service Account**
```bash
GSA_NAME=bofa-gsa
gcloud iam service-accounts create $GSA_NAME
```
4. **Allow the KSA to impersonate the GSA**
```bash
GKE_PROJECT_ID=<your-cluster-project-id>
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$GKE_PROJECT_ID.svc.id.goog[$NAMESPACE/$KSA_NAME]" \
  $GSA_NAME@$PROJECT_ID.iam.gserviceaccount.com
```
5. **Annotate the Kubernetes service account,** using the email address of the Google service account.
```bash
kubectl annotate serviceaccount \
  --namespace $NAMESPACE \
  $KSA_NAME \
  iam.gke.io/gcp-service-account=$GSA_NAME@$PROJECT_ID.iam.gserviceaccount.com
```
6. **Add IAM Roles** to your GSA. These roles allow workload identity-enabled Bank of Anthos pods to connect to the database and send traces and metrics to GCP. 

```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/cloudtrace.agent

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/monitoring.metricWriter

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role roles/cloudsql.client
```
6. **Generate Bank of Anthos manifests** using your KSA as the Pod service account. In `kubernetes-manifests/`, replace `serviceAccountName: default` with the name of your KSA. (**Note** - sample below is Bash.)
```bash
mkdir -p wi-kubernetes-manifests
FILES="`pwd`/kubernetes-manifests/*"
for f in $FILES; do
    echo "Processing $f..."
    sed "s/serviceAccountName: default/serviceAccountName: ${KSA_NAME}/g" $f > wi-kubernetes-manifests/`basename $f`
done
```
7. **Generate updated Bank of Anthos manifests** for using Cloud SQL `accounts-db` database
```bash
FILES="`pwd`/extras/cloudsql/*"
for f in $FILES; do
    echo "Processing $f..."
    sed "s/serviceAccountName: default/serviceAccountName: ${KSA_NAME}/g;s/INSTANCE_CONNECTION_NAME/${INSTANCE_CONNECTION_NAME}/g" $f > wi-kubernetes-manifests/`basename $f`
done
```
8. **Deploy Bank of Anthos** to your GKE cluster using the install instructions above, except make sure that instead of the default namespace, you're deploying the manifests into your KSA namespace: 

```bash
NAMESPACE=<your-ksa-namespace>
kubectl apply -n ${NAMESPACE} -f ./wi-kubernetes-manifests 
```
