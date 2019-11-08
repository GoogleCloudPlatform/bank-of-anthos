KEYRING_NAME=financial-app
PROJECT=hybwksp34
K8S_NAMESPACE=default

cd $(dirname $0)

gcloud kms keyrings create $KEYRING_NAME  --location global --project $PROJECT

for BANK_NAME in "bank-0"; do
    gcloud kms keys create $BANK_NAME \
      --location global \
      --keyring $KEYRING_NAME \
      --purpose asymmetric-signing \
      --default-algorithm ec-sign-p256-sha256 \
      --protection-level software \
      --project $PROJECT

    gcloud iam service-accounts create $BANK_NAME \
        --description "$BANK_NAME signing/verification" \
        --display-name "$BANK_NAME" \
        --project $PROJECT

    # todo: split up sign/verification permissions
    gcloud kms keys add-iam-policy-binding \
      $BANK_NAME --location global --keyring $KEYRING_NAME \
      --member serviceAccount:$BANK_NAME@$PROJECT.iam.gserviceaccount.com \
      --role roles/cloudkms.signerVerifier \
      --project $PROJECT

    # create a workload identity service account
    K8S_SA=$BANK_NAME-keys
    kubectl create serviceaccount --namespace $K8S_NAMESPACE $K8S_SA
    gcloud iam service-accounts add-iam-policy-binding \
        --role roles/iam.workloadIdentityUser \
        --member "serviceAccount:$PROJECT.svc.id.goog[$K8S_NAMESPACE/$K8S_SA]" \
        $BANK_NAME@$PROJECT.iam.gserviceaccount.com
    kubectl annotate serviceaccount \
        --namespace $K8S_NAMESPACE \
        $K8S_SA \
        iam.gke.io/gcp-service-account=$BANK_NAME@$PROJECT.iam.gserviceaccount.com

    gcloud kms keys versions get-public-key --project $PROJECT --key $BANK_NAME --keyring $KEYRING_NAME --location global 1 > $BANK_NAME.pub
    echo -n "projects/$PROJECT/locations/global/keyRings/$KEYRING_NAME/cryptoKeys/$BANK_NAME/cryptoKeyVersions/1" > $BANK_NAME-key-path.txt

    kubectl create secret generic $BANK_NAME-public-key --from-file=./$BANK_NAME.pub
    kubectl create secret generic $BANK_NAME-key-path --from-file=./$BANK_NAME-key-path.txt
done


