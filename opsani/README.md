# Deploy Bank-of-Anthos for Opsani Optimization Trials

Bank-of-Anthos is a polyglot application that can be used for a number of purposes. Opsani is providing this update to support optmization trials with enough scale and a transaction-defined load generator.

This will support your efforts in deploying and validating this application.

## Prerequistes and Components

1. `kubectl` cli command version appropriate to your cluster
2. bash command line interpreter (to run the deployment scripts)
3. target kubernetes cluster with at least 6 AWS m5.xl equivalent nodes avaialble exclusively for this test
4. ability to create a namespace, or define a namespace in the NAMESPACE environment variable for Bank of Anthos
5. ability to create the metrics-service (or already have it installed) in the kube-systems administrative namespace

## Install Bank of Anthos

The following commands will deploy the basic Bank of Anthos app, updated to use more realistic resources (requests/limits), and a loadgenerator deployment that should drive ~ 5 frontend pods to run.

Run the following script in order to enable Bank of Anthos:

```sh
deploy.sh
```
Alternatively, you can run the following commands manually:

```sh
echo "ensure NAMESPACE is an environment variable":
export NAMESPACE=${NAMESPACE:-bank-of-anthos-opsani}

echo "create JWT token and store in k8s secret"
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create -n ${NAMESPACE} secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
rm ./jwt*key*

echo "Launch into ${NAMESPACE}"

kubectl apply -n ${NAMESPACE} -f ../kubernetes-manifests/
```

## Load generation

Currently a single instance of a transaction load generator (based on locust.io) is launched along with the Bank of Anthos application.

To create load that Opsani can optimize run the following script:

```sh
genload.sh
```
Alternatively, you can run the following commands manually:

```sh
nohup ./genload.sh &
tail -f nohup.out
```
# Next Steps for Opsani Optimization

Now that you have the Bank of Anthos application running with load, it is time to install the Opsani Servo onto your cluster to begin optimization. To do so, we suggest you follow [dev-trial-README](dev-trial/README.md) for the simplest installation process. Alternatively, the README.md file located in `servo_install.tar.gz` that you downloaded with the Servo manifest is also suitable, although requires more effort.

# Uninstall Bank of Anthos

If a namespace was created for this project, the simplest approach is to simply delete the namespace.

Alternatively, clean out the deployed manifests:

```sh
kubectl delete -n ${NAMESPACE} -f ../kubernetes-manifests/
```

We will also want to clean up the manually deployed jwt-key secret:

```sh
kubectl delete secret jwt-key
```


