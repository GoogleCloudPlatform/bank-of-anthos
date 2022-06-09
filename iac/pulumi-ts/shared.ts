import * as pulumi from "@pulumi/pulumi";
import * as google_native from "@pulumi/google-native";
import api from "./api";

const config = new pulumi.Config();
const registryName = config.require("registryName");
const gcpConfig = new pulumi.Config("google-native")
const projectId = gcpConfig.require("project");
const projectInfo = google_native.cloudresourcemanager.v1.getProject({ project: projectId });

export const createArtifactRegistry = () => new google_native.artifactregistry.v1.Repository("artifact-registry", {
    format: google_native.artifactregistry.v1.RepositoryFormat.Docker,
    repositoryId: registryName,
}, {
    dependsOn: [api.artifactregistry],
});

export const createSharedResources = (projectIamBindings: google_native.cloudresourcemanager.v3.ProjectIamPolicy, clusters: google_native.container.v1.Cluster[], artifactRegistry: google_native.artifactregistry.v1.Repository, saGkeWorkload: google_native.iam.v1.ServiceAccount) => {
    const cacheBucket = createCacheBucket();
    const sourceMirror = createSourceRepo(projectIamBindings);
    const roleBindings = createRoleBindings(projectIamBindings, clusters, artifactRegistry, saGkeWorkload);
    return { cacheBucket, sourceMirror, roleBindings };
}

const createCacheBucket = () => new google_native.storage.v1.Bucket("cache-bucket", {
    name: projectInfo.then(projectInfo => `skaffold-cache-${projectInfo.projectNumber}`),
    iamConfiguration: {
        uniformBucketLevelAccess: {
            enabled: true
        }
    }
});

const createSourceRepo = (projectIamBindings: google_native.cloudresourcemanager.v3.ProjectIamPolicy) => new google_native.sourcerepo.v1.Repo("source-mirror", { name: `projects/${projectId}/repos/${registryName}` }, {
    dependsOn: [
        api.sourcerepo,
        projectIamBindings,
    ],
});

const createRoleBindings = (projectIamBindings: google_native.cloudresourcemanager.v3.ProjectIamPolicy, clusters: google_native.container.v1.Cluster[], artifactRegistry: google_native.artifactregistry.v1.Repository, saGkeWorkload: google_native.iam.v1.ServiceAccount) => {
    new google_native.artifactregistry.v1.RepositoryIamPolicy("artifact-registry-iam", {
        repositoryId: registryName,
        bindings: [{
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}-compute@developer.gserviceaccount.com`)],
            role: "roles/artifactregistry.reader",
        }],
    }, {
        dependsOn: [
            api.compute,
            artifactRegistry,
            projectIamBindings,
            ...clusters,
        ],
    });
    new google_native.iam.v1.ServiceAccountIamPolicy("sa-gke-workload-iam", {
        serviceAccountId: saGkeWorkload.email,
        bindings: [{
            members: [`serviceAccount:${projectId}.svc.id.goog[default/default]`],
            role: "roles/iam.workloadIdentityUser",
        }],
    }, {
        dependsOn: clusters,
    });
    new google_native.iam.v1.ServiceAccountIamPolicy("cloud-build-impersonate-compute-sa", {
        serviceAccountId: projectInfo.then(projectInfo => `${projectInfo.projectNumber}-compute@developer.gserviceaccount.com`),
        bindings: [{
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}@cloudbuild.gserviceaccount.com`)],
            role: "roles/iam.serviceAccountUser",
        }],
    }, {
        dependsOn: [api.compute],
    });
}