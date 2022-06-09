import * as pulumi from "@pulumi/pulumi";
import * as google_native from "@pulumi/google-native";
import api from "./api";
import { createEnv } from "./env";
import { createPipelines } from "./pipeline";
import { createProjectIamBindings } from "./projectIamBindings";
import { createArtifactRegistry, createSharedResources } from "./shared";

// configuration
const gcpConfig = new pulumi.Config("google-native")
const projectId = gcpConfig.require("project");
const region = gcpConfig.require("region");
const config = new pulumi.Config();
const registryName = config.require("registryName")

const envNames = [
    "development",
    "staging",
    "production",
]
const teams = [
    "accounts",
    "frontend",
    "ledger",
];

// create service account for GKE workloads
const saGkeWorkload = new google_native.iam.v1.ServiceAccount("sa-gke-workload", { accountId: "gke-workload" });
// create environments (gke, network, cloud deploy target)
const envs = Object.assign({}, ...(envNames.map(name => ({ [name]: createEnv(name) }))));
const clusters = envNames.map(name => envs[name].cluster);
// create artifact registry
const artifactRegistry = createArtifactRegistry();
// create project level iam bindings
const projectIamBindings = createProjectIamBindings(saGkeWorkload, artifactRegistry);
// create shared resources (GCS bucket for caching, source repo for code mirroring, adds rolebindings)
const { cacheBucket } = createSharedResources(projectIamBindings, clusters, artifactRegistry, saGkeWorkload);
// create ci & cd pipeline per team
teams.map(team => ({ [team]: createPipelines(team, cacheBucket, ["staging", "production"], envs) }));
// output follow-up commands
console.log("Finish setup with commands below:");
const finalizingCommands = envNames.reduce((prev, curr) => prev + `gcloud container clusters get-credentials ${curr} --region ${region} --project=${projectId} && kubectl annotate serviceaccount default --namespace=default iam.gke.io/gcp-service-account=gke-workload@${projectId}.iam.gserviceaccount.com && \\\n`, "") +
    `gcloud auth configure-docker europe-west1-docker.pkg.dev && skaffold config set default-repo ${region}-docker.pkg.dev/${projectId}/${registryName} && \\\n` +
    `git remote add ${projectId} https://source.developers.google.com/p/${projectId}/r/${registryName} && git push --all ${projectId}`;
console.log(finalizingCommands);
