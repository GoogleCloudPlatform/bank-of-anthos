#!/bin/bash

# Created with codelabba.rb v.1.4a
source .env.sh || fatal 'Couldnt source this'
set -x
set -e

# Add your code here:
#REGION=us-central1
#gcloud services enable container.googleapis.com monitoring.googleapis.com \
#  --project ${PROJECT_ID}

gcloud container clusters create-auto bank-of-anthos \
  --project=${PROJECT_ID} --region=${REGION}

gcloud container clusters get-credentials bank-of-anthos \
  --project=${PROJECT_ID} --region=${REGION}


# Alternatively, you can deploy using GKE Standard instead:

# ```
# ZONE=us-central1-b
# gcloud beta container clusters create bank-of-anthos \
#   --project=${PROJECT_ID} --zone=${ZONE} \
#   --machine-type=e2-standard-2 --num-nodes=4 \
#   --monitoring=SYSTEM --logging=SYSTEM,WORKLOAD --subnetwork=default \
#   --tags=bank-of-anthos --labels csm=

# gcloud container clusters get-credentials bank-of-anthos \
#   --project=${PROJECT_ID} --zone=${ZONE}
# ```




# End of your code here
echo All good.
