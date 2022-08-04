# Bank of Anthos quickstart

This tutorial shows you how to deploy **[Bank of Anthos](https://github.com/GoogleCloudPlatform/bank-of-anthos)** to a Kubernetes cluster.

You'll be able to run Bank of Anthos on:
- a local **[minikube](https://minikube.sigs.k8s.io/docs/)** cluster, which comes built in to the Cloud Shell instance
- a **[Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine)** cluster using a new or existing [Google Cloud Platform project](https://cloud.google.com/resource-manager/docs/creating-managing-projects#creating_a_project)

Let's get started!


## Select a GCP project

In order to create a Google Kubernetes Engine cluster, you'll need to create a Google Cloud Platform project or use an existing project.

**Note:** If you choose to deploy to minikube instead of GKE, you can skip this step.

<walkthrough-project-setup></walkthrough-project-setup>


## Kubernetes cluster setup

This section shows you how to set up a Kubernetes cluster using either **minikube** or **GKE**.

1. Open the <walkthrough-editor-spotlight spotlightId="activity-bar-cloud-k8s">Cloud Code - Kubernetes</walkthrough-editor-spotlight> sidebar using the left side Activity bar.

2. In the <walkthrough-editor-spotlight spotlightId="cloud-code-k8s-explorer">**Clusters**</walkthrough-editor-spotlight> explorer, click <walkthrough-editor-spotlight spotlightId="cloud-code-k8s-explorer-add-cluster">'+'</walkthrough-editor-spotlight> in the title bar to create a new cluster.

3. Choose either **Minikube** or **Google Kubernetes Engine** and follow the relevant instructions below.

### Minikube
*(skip this section if you're planning on deploying to GKE)*

4. Select the **minikube** [profile](https://minikube.sigs.k8s.io/docs/commands/profile/).

5. Select **Start**. Cloud Code will initiate a minikube cluster.

6. If prompted, authorize Cloud Shell to make a GCP API call with your credentials.

### GKE
*(skip this section if you're planning on deploying to minikube)*

4. Click **+ Create a new GKE Cluster**.

5. Select the cluster mode **Standard**.

6. Apply the following configurations:
> - Zone: us-central1-b
> - Cluster name: bank-of-anthos
> - Node count: 4
> - Machine type: e2-standard-2

7. Click **Create Cluster**. Once the cluster has finished being created, it will be added to the <walkthrough-editor-spotlight spotlightId="cloud-code-k8s-explorer">**Clusters**</walkthrough-editor-spotlight> explorer and set as the default context.

Once you've configured your minikube or GKE cluster, you're ready to move on to the next step.


## Deploy the JWT token

Bank of Anthos uses a JWT token for user account creation and authentication. 

To deploy the token:

1. Open <walkthrough-editor-open-file filePath="extras/jwt/jwt-secret.yaml">jwt-secret.yaml
</walkthrough-editor-open-file>. 

2. Access the command palette by going to **View > Command Palette...**.

3. Run the command **"Cloud Code: Apply the current JSON/YAML file to the kubernetes deployed resource"**.   

4. The following warning will pop up:  

> ⚠️ Resource Secret/jwt-key does not exist - this will create a new resource.

5. Click **Create**.   

This deploys the demo JWT public key to your cluster as a Secret.

For more information about using JWT keys in Bank of Anthos, check out the <walkthrough-editor-open-file filePath="extras/jwt/README.md">JWT Key Pair Secret README</walkthrough-editor-open-file>.


## Run on Kubernetes

Now you can run Bank of Anthos on your Kubernetes cluster!

1. Launch the <walkthrough-editor-spotlight spotlightId="cloud-code-status-bar">Cloud Code menu</walkthrough-editor-spotlight> from the status bar and select <walkthrough-editor-spotlight spotlightId="cloud-code-run-on-k8s">Run on Kubernetes</walkthrough-editor-spotlight>.

2. If prompted to select a Skaffold Profile, select **[default]**.

3. Select **Use current context** to confirm your current context.

4. If you're using a GKE cluster, you'll need to confirm your container image registry.

Cloud Code uses configurations defined in <walkthrough-editor-open-file filePath="skaffold.yaml">skaffold.yaml</walkthrough-editor-open-file> to build and deploy the app. *It may take a few minutes for the deploy to complete.*

5. Once the app is running, the local URLs will be displayed in the <walkthrough-editor-spotlight spotlightId="output">Output</walkthrough-editor-spotlight> terminal. 

7. To access your Bank of Anthos frontend service, click on the <walkthrough-spotlight-pointer spotlightId="devshell-web-preview-button" target="cloudshell">Web Preview button</walkthrough-spotlight-pointer> in the upper right of the editor window.

8. Select **Change Port** and enter '4503' as the port, then click **Change and Preview**. Your app will open in a new window. 
 

## Stop the app

To stop running the app: 

1. Go to the <walkthrough-editor-spotlight spotlightId="activity-bar-debug">Debug view</walkthrough-editor-spotlight> 

2. Click the **Stop** icon.

3. If prompted, select **Yes** to clean up deployed resources.

You can start, stop, and debug apps from the Debug view.

### Cleanup

If you've deployed your app to a GKE cluster in your Google Cloud Platform project, you'll want to delete the cluster to avoid incurring charges.

1. Navigate to the <walkthrough-editor-spotlight spotlightId="activity-bar-cloud-k8s">Cloud Code - Kubernetes view</walkthrough-editor-spotlight> in the Activity bar.

2. Under the <walkthrough-editor-spotlight spotlightId="cloud-code-gke-explorer">**Clusters**</walkthrough-editor-spotlight> explorer, right-click on your cluster and select **Delete Cluster**.


## Conclusion

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

Congratulations! You've successfully deployed Bank of Anthos using Cloud Shell.

<walkthrough-inline-feedback></walkthrough-inline-feedback>

##### What's next?

Explore the GCP products used in Bank of Anthos: [GKE](https://cloud.google.com/kubernetes-engine), [Anthos Service Mesh](https://cloud.google.com/anthos/service-mesh), [Anthos Config Management](https://cloud.google.com/anthos/config-management), [Migrate for Anthos](https://cloud.google.com/migrate/anthos), [Spring Cloud GCP](https://spring.io/projects/spring-cloud-gcp), and [Cloud Operations](https://cloud.google.com/products/operations).

Learn more about the [Cloud Shell](https://cloud.google.com/shell) IDE environment and the [Cloud Code](https://cloud.google.com/code) extension.
