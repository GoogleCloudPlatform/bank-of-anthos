# CI/CD Setup Guide for Bank of Anthos

This guide will help you set up automated CI/CD deployment to Google Kubernetes Engine (GKE) using GitHub Actions.

## Prerequisites

1. A Google Cloud Project with billing enabled
2. A GKE cluster named `bank-of-anthos` in the `us-central1` region
3. A GitHub repository with the Bank of Anthos code

## Step 1: Create a Service Account

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** > **Service Accounts**
3. Click **Create Service Account**
4. Name: `github-actions-sa`
5. Description: `Service account for GitHub Actions CI/CD`
6. Click **Create and Continue**

## Step 2: Assign Required Roles

Assign these roles to your service account:
- **Kubernetes Engine Developer**
- **Container Registry Service Agent**
- **Storage Admin** (for GCR access)

## Step 3: Create and Download Service Account Key

1. Click on your service account
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Choose **JSON** format
5. Download the key file

## Step 4: Configure GitHub Secrets

Go to your GitHub repository and add these secrets:

### Required Secrets

1. **GCP_PROJECT_ID**: Your Google Cloud Project ID
2. **GCP_SA_KEY**: The entire contents of the JSON key file you downloaded

### How to add secrets:

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add each secret with the exact names above

## Step 5: Choose Your Workflow

I've created three workflow options for you:

### Option 1: Simple Deployment (Recommended)
- **File**: `.github/workflows/deploy-to-gke-simple.yml`
- **Description**: Uses existing Docker images from the Bank of Anthos repository
- **Best for**: Quick setup, uses pre-built images

### Option 2: Basic Deployment
- **File**: `.github/workflows/deploy-to-gke.yml`
- **Description**: Basic deployment without image building
- **Best for**: Simple deployments

### Option 3: Advanced Deployment
- **File**: `.github/workflows/deploy-to-gke-advanced.yml`
- **Description**: Builds and pushes custom Docker images
- **Best for**: Custom modifications, full CI/CD pipeline

## Step 6: Enable the Workflow

1. Choose one of the workflow files above
2. Rename it to `deploy-to-gke.yml` (or keep the current name)
3. Commit and push to your main branch
4. The workflow will automatically trigger on the next push to main

## Step 7: Test the Deployment

1. Make a small change to your code
2. Commit and push to the main branch
3. Go to **Actions** tab in your GitHub repository
4. Watch the workflow run
5. Once complete, get your cluster credentials and check the deployment:

```bash
gcloud container clusters get-credentials bank-of-anthos --zone us-central1
kubectl get pods
kubectl get services
```

## Troubleshooting

### Common Issues:

1. **Authentication Error**: Verify your service account key is correct
2. **Cluster Not Found**: Ensure your cluster name and zone match the workflow
3. **Permission Denied**: Check that your service account has the required roles
4. **Image Pull Errors**: For the simple workflow, ensure the cluster can access gcr.io

### Useful Commands:

```bash
# Check cluster status
gcloud container clusters list

# Get cluster credentials
gcloud container clusters get-credentials bank-of-anthos --zone us-central1

# Check pod status
kubectl get pods

# Check service status
kubectl get services

# View logs
kubectl logs -f deployment/frontend
```

## Customization

You can customize the workflows by:
- Changing the cluster name or zone
- Adding environment-specific configurations
- Modifying the deployment strategy
- Adding additional verification steps

## Security Notes

- Never commit service account keys to your repository
- Use GitHub Secrets for all sensitive information
- Regularly rotate your service account keys
- Consider using Workload Identity for production deployments
