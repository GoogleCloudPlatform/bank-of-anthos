#!/bin/bash

# Copyright 2022 Google LLC
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

if [ -z "$PROJECT" ]
then
echo "No PROJECT variable set"
exit
fi

if [ -z "$BOA_NAMESPACE" ]
then
echo "No BOA_NAMESPACE variable set"
exit
fi

if [ -z "$APIGEE_HOST" ]
then
echo "No APIGEE_HOST variable set"
exit
fi

if [ -z "$APIGEE_ENV" ]
then
echo "No APIGEE_ENV variable set"
exit
fi

if [ -z "$ILB_IP" ]
then
  echo "No ILB_IP variable set"
  function get_ilb()  {
    kubectl get services api-ingressgateway -n $BOA_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
  }
  until [ -n "$(get_ilb)" ] ;
  do
    echo "Waiting for the ILB to be ready ..."
    sleep 10
  done
  export ILB_IP=$(get_ilb)
fi

if [ -z "$FRONTEND_XLB_IP" ]
then
  echo "No FRONTEND_XLB_IP variable set"
  function get_xlb()  {
     kubectl get services frontend -n $BOA_NAMESPACE  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
  }
  until [ -n "$(get_xlb)" ] ;
  do
    echo "Waiting for the XLB to be ready ..."
    sleep 10
  done
  export FRONTEND_XLB_IP=$(get_xlb)
fi

echo "Checking if apigeecli is installed..."
APIGEE_CLI=$(which apigeecli)
if [[ -z "$APIGEE_CLI" ]];
then
echo "apigeecli not found in PATH, exiting"
exit
fi

echo "Deploying Apigee artifacts..."
mkdir output
cd output
cp -R ../proxies/* .
cp -R ../sharedflows/* .

cd bank-of-anthos-balancereader-v1
sed -i "s@{SERVER_URL}@https://$APIGEE_HOST@" apiproxy/resources/oas/balancereader.yaml
zip -r ../bank-of-anthos-balancereader-v1.zip apiproxy
cd ..

cd bank-of-anthos-contacts-v1
sed -i "s@{SERVER_URL}@https://$APIGEE_HOST@" apiproxy/resources/oas/contacts.yaml
zip -r ../bank-of-anthos-contacts-v1.zip apiproxy
cd ..

cd bank-of-anthos-transactionhistory-v1
sed -i "s@{SERVER_URL}@https://$APIGEE_HOST@" apiproxy/resources/oas/transactionhistory.yaml
zip -r ../bank-of-anthos-transactionhistory-v1.zip apiproxy
cd ..

cd bank-of-anthos-identity-v1
zip -r ../bank-of-anthos-identity-v1.zip apiproxy
cd ..

cd SF-bank-of-anthos-auth-v1/
zip -r ../SF-bank-of-anthos-auth-v1.zip sharedflowbundle
cd ../../

TOKEN=$(gcloud auth print-access-token)

echo "Configuring Apigee Targetserver..."
TARGETSERVER_NAME=Bank-of-Anthos
apigeecli targetservers get --name $TARGETSERVER_NAME --org $PROJECT --env $APIGEE_ENV --token $TOKEN
if [ $? -eq 0 ]
then
    echo "Updating Target server"
    apigeecli targetservers update --name $TARGETSERVER_NAME --host $ILB_IP --port 80 --enable true --org $PROJECT --env $APIGEE_ENV --token $TOKEN
else
    echo "Creating Target server"
    apigeecli targetservers create --name $TARGETSERVER_NAME --host $ILB_IP --port 80 --enable true --org $PROJECT --env $APIGEE_ENV --token $TOKEN
fi

echo "Importing and Deploying SF-bank-of-anthos-auth-v1 Sharedflow"
REV=$(apigeecli sharedflows import -f output/SF-bank-of-anthos-auth-v1.zip --org $PROJECT --token $TOKEN | grep -v 'WARNING' | jq ."revision" -r)
apigeecli sharedflows deploy --name SF-bank-of-anthos-auth-v1 --ovr --rev $REV --org $PROJECT --env $APIGEE_ENV --token $TOKEN

echo "Importing and Deploying Apigee bank-of-anthos-balancereader-v1 proxy..."
REV=$(apigeecli apis import -f output/bank-of-anthos-balancereader-v1.zip --org $PROJECT --token $TOKEN | grep -v 'WARNING' | jq ."revision" -r)
apigeecli apis deploy --wait --name bank-of-anthos-balancereader-v1 --ovr --rev $REV --org $PROJECT --env $APIGEE_ENV --token $TOKEN

echo "Importing and Deploying Apigee bank-of-anthos-contacts-v1 proxy..."
REV=$(apigeecli apis import -f output/bank-of-anthos-contacts-v1.zip --org $PROJECT --token $TOKEN | grep -v 'WARNING' |jq ."revision" -r)
apigeecli apis deploy --wait --name bank-of-anthos-contacts-v1 --ovr --rev $REV --org $PROJECT --env $APIGEE_ENV --token $TOKEN

echo "Importing and Deploying Apigee bank-of-anthos-transactionhistory-v1 proxy..."
REV=$(apigeecli apis import -f output/bank-of-anthos-transactionhistory-v1.zip --org $PROJECT --token $TOKEN | grep -v 'WARNING' | jq ."revision" -r)
apigeecli apis deploy --wait --name bank-of-anthos-transactionhistory-v1 --ovr --rev $REV --org $PROJECT --env $APIGEE_ENV --token $TOKEN

echo "Importing and Deploying Apigee bank-of-anthos-identity-v1 proxy..."
REV=$(apigeecli apis import -f output/bank-of-anthos-identity-v1.zip --org $PROJECT --token $TOKEN | grep -v 'WARNING' | jq ."revision" -r)
apigeecli apis deploy --wait --name bank-of-anthos-identity-v1 --ovr --rev $REV --org $PROJECT --env $APIGEE_ENV --token $TOKEN

echo "Creating API Products"
apigeecli products import --org $PROJECT --token $TOKEN --file ./products/products.json --upsert

echo "Creating Developer"
apigeecli developers import --org $PROJECT --token $TOKEN --file ./developers/developers.json

echo "Creating Developer App"
sed -i "s@{SERVER_URL}@https://$APIGEE_HOST@" apps/apps.json
apigeecli apps import --org $PROJECT --token $TOKEN --file ./apps/apps.json --dev-file ./developers/developers.json
echo " "

APIKEY=$(apigeecli apps get --name bank-of-anthos-demo-app --org $PROJECT --token $TOKEN | grep -v 'WARNING' | jq ."[0].credentials[0].consumerKey" -r)
APISECRET=$(apigeecli apps get --name bank-of-anthos-demo-app --org $PROJECT --token $TOKEN | grep -v 'WARNING' | jq ."[0].credentials[0].consumerSecret" -r)

# Create boa_config_map KVM and add entries
echo "Creating Config Key Value Map"
apigeecli kvms create --token $TOKEN --org $PROJECT --env $APIGEE_ENV --name boa-config-map
apigeecli kvms entries create --token $TOKEN --org $PROJECT --env $APIGEE_ENV --map boa-config-map create --key login.hostname --value $FRONTEND_XLB_IP
KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
apigeecli kvms entries create --token $TOKEN --org $PROJECT --env $APIGEE_ENV --map boa-config-map create --key apigee.client_id --value $KEY

# Update k8s cluster config map with Apigee callback & key
sed -i "s/.*DEMO_OAUTH_CLIENT_ID.*/  DEMO_OAUTH_CLIENT_ID: \"$KEY\"  # Edited by deploy-apigee-artifacts script/" ./oauth-config.yaml 
sed -i "s@.*DEMO_OAUTH_REDIRECT_URI.*@  DEMO_OAUTH_REDIRECT_URI: \"https://$APIGEE_HOST/oauth/callback\"  # Edited by deploy-apigee-artifacts script@" ./oauth-config.yaml 
kubectl apply -n ${BOA_NAMESPACE} -f ./oauth-config.yaml
kubectl delete pods -n ${BOA_NAMESPACE} -l app=frontend
sleep 10

echo "To generate an auth code, first open this link in your browser, then login and consent: https://$APIGEE_HOST/oauth/authorize?client_id=$APIKEY&response_type=code&redirect_uri=https%3A%2F%2F$APIGEE_HOST%2Foauth%2Fcoderesponse"
echo " "

echo Enter the code from the browser output:
read authcode
echo " "

ACCESS_TOKEN=$(curl --http1.1 -u $APIKEY:$APISECRET -X POST https://$APIGEE_HOST/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&redirect_uri=https://$APIGEE_HOST/oauth/coderesponse&code=$authcode" | jq .access_token)

echo "All the Apigee artifacts are successfully deployed!"
echo "Use the below curl commands to test your demo"
echo " "
echo "To get the account balance"
echo "--------------------------"
echo "curl https://$APIGEE_HOST/v1/boa-balancereader/balances/1011226111 \\
  -H \"Authorization: Bearer $ACCESS_TOKEN\""
echo " "

echo "To get the list of transactions"
echo "-------------------------------"
echo "curl https://$APIGEE_HOST/v1/boa-transactionhistory/transactions/1011226111 \\
  -H \"Authorization: Bearer $ACCESS_TOKEN\""
echo " "

echo "To get the list of user contacts"
echo "--------------------------------"
echo "curl https://$APIGEE_HOST/v1/boa-contacts/contacts/testuser \\
  -H \"Authorization: Bearer $ACCESS_TOKEN\""
echo " "
