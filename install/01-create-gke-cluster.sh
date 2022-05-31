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







# End of your code here
verde Tutto ok.
