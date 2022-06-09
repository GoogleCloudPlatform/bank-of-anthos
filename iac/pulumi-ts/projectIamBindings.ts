import * as pulumi from "@pulumi/pulumi";
import * as google_native from "@pulumi/google-native";
import api from "./api";

const config = new pulumi.Config();
const gcpConfig = new pulumi.Config("google-native")
const projectId = gcpConfig.require("project");
const projectInfo = google_native.cloudresourcemanager.v1.getProject({ project: projectId });
const boaProjectOwner = config.require("projectOwner");

export const createProjectIamBindings = (saGkeWorkload: google_native.iam.v1.ServiceAccount, artifactRegistry: google_native.artifactregistry.v1.Repository) => new google_native.cloudresourcemanager.v3.ProjectIamPolicy("project-iam-bindings", {
    bindings: [
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:service-${projectInfo.projectNumber}@gcp-sa-artifactregistry.iam.gserviceaccount.com`)],
            role: "roles/artifactregistry.serviceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}@cloudbuild.gserviceaccount.com`)],
            role: "roles/cloudbuild.builds.builder",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:service-${projectInfo.projectNumber}@gcp-sa-cloudbuild.iam.gserviceaccount.com`)],
            role: "roles/cloudbuild.serviceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}@cloudbuild.gserviceaccount.com`)],
            role: "roles/clouddeploy.releaser",
        },
        {
            members: [pulumi.interpolate`serviceAccount:${saGkeWorkload.email}`],
            role: "roles/cloudtrace.agent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:service-${projectInfo.projectNumber}@compute-system.iam.gserviceaccount.com`)],
            role: "roles/compute.serviceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}-compute@developer.gserviceaccount.com`)],
            role: "roles/container.nodeServiceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:service-${projectInfo.projectNumber}@container-engine-robot.iam.gserviceaccount.com`)],
            role: "roles/container.serviceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:service-${projectInfo.projectNumber}@containerregistry.iam.gserviceaccount.com`)],
            role: "roles/containerregistry.ServiceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}@cloudservices.gserviceaccount.com`)],
            role: "roles/editor",
        },
        {
            members: [
                projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}-compute@developer.gserviceaccount.com`),
                pulumi.interpolate`serviceAccount:${saGkeWorkload.email}`,
            ],
            role: "roles/logging.logWriter",
        },
        {
            members: [pulumi.interpolate`serviceAccount:${saGkeWorkload.email}`],
            role: "roles/monitoring.metricWriter",
        },
        {
            members: [`user:${boaProjectOwner}`],
            role: "roles/owner",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:service-${projectInfo.projectNumber}@gcp-sa-pubsub.iam.gserviceaccount.com`)],
            role: "roles/pubsub.serviceAgent",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}-compute@developer.gserviceaccount.com`)],
            role: "roles/storage.objectCreator",
        },
        {
            members: [projectInfo.then(projectInfo => `serviceAccount:${projectInfo.projectNumber}-compute@developer.gserviceaccount.com`)],
            role: "roles/container.developer",
        },
    ]
}, {
    dependsOn: [
        api.artifactregistry,
        api.sourcerepo,
        api.cloudbuild,
        api.clouddeploy,
        api.container,
        api.compute,
        saGkeWorkload,
        artifactRegistry,
    ],
});