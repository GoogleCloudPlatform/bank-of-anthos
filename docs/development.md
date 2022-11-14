# Development Guide

This document describes how to develop and add features to the Bank of Anthos application in your local environment. 

## Prerequisites 

1. [A GCP project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console), connected to your billing account. 
2. [A GKE cluster in your project](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-cluster#gcloud). We recommend 4 nodes, machine type: `e2-standard-4`. 

## Install Tools 

You can use MacOS or Linux as your dev environment - all these languages and tools support both. 

1. [Docker Desktop](https://www.docker.com/products/docker-desktop) 
1. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) (can be installed separately or via [gcloud](https://cloud.google.com/sdk/install)) 
1. [skaffold **2.0+**](https://skaffold.dev/docs/install/) (latest version recommended)
1. [OpenJDK **17**](https://openjdk.java.net/projects/jdk/17/) (newer versions not tested)
1. [Maven **3.8**](https://downloads.apache.org/maven/maven-3/) (newer versions not tested)
1. [Python **3.7+**](https://www.python.org/downloads/)  
1. [piptools](https://pypi.org/project/pip-tools/)

### Installing JDK 17 and Maven 3.8

If your package manager doesn't allow you to install JDK 17 or Maven 3.8 (for example, if you're on an older version of Ubuntu), you can follow the following instructions.

Find the [latest release of JDK 17](https://jdk.java.net/17/) and extract it to the `/opt` directory:
```
wget https://download.java.net/java/GA/jdk17.0.1/2a2082e5a09d4267845be086888add4f/12/GPL/openjdk-17.0.1_linux-x64_bin.tar.gz
tar xvf openjdk-17.0.1_linux-x64_bin.tar.gz
sudo mv jdk-17*/ /opt/jdk17
```

Find the [latest release of Maven 3.8](https://maven.apache.org/download.cgi) and extract it to the `/opt` directory:
```
wget https://dlcdn.apache.org/maven/maven-3/3.8.5/binaries/apache-maven-3.8.5-bin.tar.gz
sudo tar xf apache-maven-*.tar.gz -C /opt
```

Create a profile containing the paths of the newly extracted JDK and Maven directories:
```
sudo tee /etc/profile.d/java.sh <<EOF
export JAVA_HOME=/opt/jdk17
export M2_HOME=/opt/apache-maven-3.8.5
export MAVEN_HOME=/opt/apache-maven-3.8.5
export PATH=\$JAVA_HOME/bin:\$M2_HOME/bin:\$PATH
EOF
sudo chmod +x /etc/profile.d/java.sh
```

Verify that the versions are correct:
```
source /etc/profile.d/java.sh
java -version
mvn -version
```

## Adding External Packages 

### Python 

If you're adding a new feature that requires a new external Python package in one or more services (`frontend`, `contacts`, `userservice`), you must regenerate the `requirements.txt` file using `piptools`. This is what the Python Dockerfiles use to install external packages inside the containers.

To add a package: 

1. Add the package name to `requirements.in` within the `src/<service>` directory:

2. From inside that directory, run: 

```
python3 -m pip install pip-tools
python3 -m piptools compile --output-file=requirements.txt requirements.in
```

3. Re-run `skaffold dev` or `skaffold run` to trigger a Docker build using the updated `requirements.txt`.  


### Java 

If you're adding a new feature to one or more of the Java services (`ledgerwriter`, `transactionhistory`, `balancereader`) and require a new third-party package, do the following:  

1. Add the package to the `pom.xml` file in the `src/<service>` directory, under `<dependencies>`. You can find specific package info in [Maven Central](https://search.maven.org/) ([example](https://search.maven.org/artifact/org.postgresql/postgresql/42.2.16.jre7/jar)). Example: 

```
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
```


2. Re-run `skaffold dev` or `skaffold run` to trigger a Jib container build using Maven and the updated pom file. 


## Generating your own JWT public key. 

The [extras](/extras/jwt) directory provides the RSA key/pair secret used for demos. To create your own: 

```
openssl genrsa -out jwtRS256.key 4096
openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub
kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
```

## Testing your changes locally 

We recommend you test and build directly on Kubernetes, from your local environment.  This is because there are seven services and for the app to fully function, all the services need to be running. All the services have dependencies, environment variables, and secrets and that are built into the Kubernetes environment / manifests, so testing directly on Kubernetes is the fastest way to see your code changes in action.

You can use the `skaffold` tool to build and deploy your code to the GKE cluster in your project. 

Make sure that you export `PROJECT_ID` as an environment variable (or add to your `.bashrc` before running either of these commands)

### Option 1 - Build and deploy continuously 

The [`skaffold dev`](https://skaffold.dev/docs/references/cli/#skaffold-dev) command watches your local code, and continuously builds and deploys container images to your GKE cluster anytime you save a file. Skaffold uses Docker Desktop to build the Python images, then [Jib](https://github.com/GoogleContainerTools/jib#jib) (installed via Maven) to build the Java images. 

```
skaffold dev --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos
```


### Option 2 - Build and deploy once 

The [`skaffold run`](https://skaffold.dev/docs/references/cli/#skaffold-run) command build and deploys the services to your GKE cluster one time, then exits. 

```
skaffold run --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos
```

### Running services selectively

Skaffold reads the [skaffold.yaml](../skaffold.yaml) file to understand the project setup. Here, it's split into modules that can be iterated on individually:
- the `backend` module comprising of the five backend services.
- the `frontend` module for the single frontend service.
- the `loadbalancer` module for the single loadbalancer service. 

To work with only the `frontend` module, run:

```
skaffold dev --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos -m frontend
```

To work with both `frontend` and `backend` modules, run:

```
skaffold dev --default-repo=gcr.io/${PROJECT_ID}/bank-of-anthos -m frontend -m backend
```

## Continuous Integration

When you're ready to create a Pull Request for your branch, you will notice that the Github Actions CI workflows run on your branch. This includes both code and deploy tests into a separate GKE cluster owned by the maintainers. The GitHub Actions CI workflows are [described here](../.github/workflows).

