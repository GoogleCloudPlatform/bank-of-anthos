#!/bin/bash

source .env.sh

gcloud config configurations create $GCLOUD_CONFIG |
gcloud config configurations activate $GCLOUD_CONFIG || 
    gcloud config configurations create $GCLOUD_CONFIG  
gcloud config set account $ACCOUNT
gcloud config set project $PROJECT_ID 
PROJECT_ID=$(gcloud config get-value project)

    # Enable APIs...
gcloud services enable logging
gcloud services enable compute
#gcloud services enable run
gcloud services enable cloudbuild
gcloud services enable container
gcloud services enable monitoring

    # Se hai EventArc o simili..
#gcloud eventarc locations list
#gcloud eventarc locations list | grep $REGION ||
#    fatal "Region non esiste x sto servizio: $REGION"

# Set defaults..
#gcloud config set run/region $REGION
#gcloud config set run/platform managed
#gcloud config set eventarc/location $REGION

gcloud config list | lolcat

    # If you need to aunthenticate your app
#This is needed when you want to use Python, Node, .. APIs and you cant / dont
#want to use a service account.
#
# gcloud auth application-default login
#
#Once I got a mysterious error which asked me to RE-authorize:
#
# gcloud auth login --update-adc
#

#touch ".$APPNAME.appname"
