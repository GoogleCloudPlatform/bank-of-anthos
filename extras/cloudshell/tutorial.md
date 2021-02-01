# Bank of Anthos Minikube Quickstart

## 
This tutorial shows you how to deploy the Bank of Anthos app to a local Kubernetes cluster using [minikube](https://minikube.sigs.k8s.io/docs/) on Cloud Shell.

Let's get started!


## Start minikube

Minikube creates a local Kubernetes cluster on Cloud Shell.

1. Click <walkthrough-editor-spotlight spotlightId="minikube-status-bar">Minikube Stopped</walkthrough-editor-spotlight> on the status bar.

2. Click **Start**. 

3. If prompted, authorize Cloud Shell to make a GCP API call with your credentials.

Once the status bar says <walkthrough-editor-spotlight spotlightId="minikube-status-bar">Minikube Running</walkthrough-editor-spotlight>, you're ready to move on to the next step.


## Deploy JWT token

Bank of Anthos uses a JWT token for user account creation and authentication. 

To deploy the token:

1. Open <walkthrough-editor-open-file filePath="extras/jwt/jwt-secret.yaml">jwt-secret.yaml
</walkthrough-editor-open-file>. 

2. Access the command palette by going to **View > Find Command**.

3. Run the command **"Cloud Code: Apply the current JSON/YAML file to the kubernetes deployed resource"**.   

4. The following warning will pop up:  

> ⚠️ **"Resource Secret/jwt-key does not exist - this will create a new resource."**

5. Click **Create**.   

This deploys the demo JWT public key to the minikube cluster as a Secret.


## Run on minikube

Now you can run Bank of Anthos on your minikube cluster!

1. Launch the <walkthrough-editor-spotlight spotlightId="cloud-code-status-bar">Cloud Code menu</walkthrough-editor-spotlight> from the status bar and select <walkthrough-editor-spotlight spotlightId="cloud-code-run-on-k8s">Run on Kubernetes</walkthrough-editor-spotlight>.

2. Cloud Code uses configurations defined in <walkthrough-editor-open-file filePath="skaffold.yaml">`skaffold.yaml`</walkthrough-editor-open-file> to build and deploy the app. This may take a minute.

3. Once the app is running, the local URLs will be displayed in the <walkthrough-editor-spotlight spotlightId="output">Output</walkthrough-editor-spotlight> terminal.

4. Launch your Bank of Anthos app in your browser by clicking on the `frontend` URL.


## Stop the app

To stop running the app: 
1. Go to the <walkthrough-editor-spotlight spotlightId="activity-bar-debug">Debug view</walkthrough-editor-spotlight> 
2. Click the 'Stop' icon. 🟥

You can start, stop, and debug apps from the Debug view.

## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Congratulations! You've successfully deployed Bank of Anthos using Cloud Shell.

##### What's next?

Explore the GCP products used in Bank of Anthos: [GKE](https://cloud.google.com/kubernetes-engine), [Anthos Service Mesh](https://cloud.google.com/anthos/service-mesh), [Anthos Config Management](https://cloud.google.com/anthos/config-management), [Migrate for Anthos](https://cloud.google.com/migrate/anthos), [Spring Cloud GCP](https://spring.io/projects/spring-cloud-gcp), and [Cloud Operations](https://cloud.google.com/products/operations).

Learn more about the [Cloud Shell](https://cloud.google.com/shell) IDE environment and the [Cloud Code](https://cloud.google.com/code) extension.
