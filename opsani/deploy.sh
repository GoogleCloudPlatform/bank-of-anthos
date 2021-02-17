#!/bin/bash

if [ ! "`kubectl version ; echo $?`" ]; then
  echo "kubectl is either not installed or can not determine its version"
  echo "please install and configure kubectl to talk to your cluster"
  echo "See: https://kubernetes.io/docs/tasks/tools/install-kubectl/"
  echo ""
  echo ""
  exit 1
else
  echo "kubectl installed"
  echo ""
  echo ""
fi

if [ "`kubectl get nodes | grep Ready | wc -l`" -lt "8" ] ; then 
  echo "it appears that you do not have enough worker nodes to run this test"
  echo "currently there are `kubectl get nodes | grep internal | wc -l` nodes available"
  echo "the minimum is 8 nodes (and it is recommended that they be AWS m5.xl or larger)"
  echo ""
  echo ""
  exit 1
else
  echo "It appears that you have at least 8 nodes available"
  echo ""
  echo ""
fi


NAMESPACE=${NAMESPACE:-`kubectl config get-contexts | awk '/^\*/ {print $5}'`}
if [ ! "`kubectl get ns ${NAMESPACE:-bank-of-anthos-opsani} >& /dev/null; echo $?`" ]; then
  NAMESPACE=bank-of-anthos-opsani
  echo "Namespace 'bank-of-anthos-opsani' exists"
  echo ""
  echo "You will need to ensure that your opsani services use"
  echo "this same namespace parameter"
  echo ""
  echo "you can set this as your default with:"
  echo "kubectl config set-context `kubectl config get-contexts | awk '/^\*/ {print $2}'` --namespace ${NAMESPACE}"
  echo ""
else
  echo "Creating bank-of-anthos-opsani namespace"
  if [ ! "`kubectl create ns bank-of-anthos-opsani >& /dev/null; echo $?`" ]; then
    echo "Couldn't create kubernetes namespace 'bank-of-anthos-opsani'"
    echo "You must set the NAMESPACE enviornment variable for the target "
    echo "e.g. `export NAMESPACE=bank-of-anthos-opsani`"
    exit 1
  else
    NAMESPACE=bank-of-anthos-opsani
    echo "created namespace $NAMESPACE"
    echo "deploying into ${NAMESPACE}"
    echo ""
    echo ""
  fi
fi

echo ""

if [ "`kubectl get --raw '/apis/metrics.k8s.io/v1beta1/nodes' >& /dev/null; echo $?`" ]; then
  echo "default metrics-server is not installed, this is a requirement"
  echo "to support proper functioning of the HPA service against the frontend and userdata services"
  echo ""
  echo "attempting install"
  if [ ! "`kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`; echo $?" ]; then
    echo "Unable to install metrics server. Please contact your systems administrator to"
    echo "enable this function."
    echo "Normally this is accomplished by running:"
    echo "kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
    echo ""
    echo ""
    exit 1
  fi
  echo "installed"
fi
echo ""
echo ""

echo "create JWT token and store in k8s secret for Bank-of-Anthos"
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create -n ${NAMESPACE} secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
rm ./jwt*key*

echo ""
echo ""
echo "Launch Bank-of-Anthos into ${NAMESPACE}"

kubectl apply -n ${NAMESPACE} -f ../kubernetes-manifests/
if [ ! "echo $?" ]; then
  echo ""
  echo "a component may have failed to install.  Please look at the above output for errors"
  exit 1
else
  echo ""
  echo ""
  echo "Bank-of-Anthos was installed in ${NAMESPACE}"
  echo "You can try to port-forward to the frontend service with"
  echo "kubectl port-forward -n ${NAMESPACE} svc/frontend 8080:http &"
  echo "and point a web browser to http://localhost:8080/"
  echo "the default user and password are 'testuser' and 'password'"
fi
