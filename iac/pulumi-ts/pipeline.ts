import type { Env } from "./env";

import * as pulumi from "@pulumi/pulumi";
import * as google_native from "@pulumi/google-native";
import api from "./api";

const config = new pulumi.Config();
const gcpConfig = new pulumi.Config("google-native")
const projectId = gcpConfig.require("project");
const region = gcpConfig.require("region");
const registryName = config.require("registryName");

export const createPipelines = (team: string, bucket: google_native.storage.v1.Bucket, targetNames: string[], envs: { string: Env }) => {
    const cache = createCache(team, bucket);
    const integrationPipeline = createIntegrationPipeline(team, bucket);
    const deliveryPipeline = createDeliveryPipeline(team, targetNames, envs);
    return { cache, integrationPipeline, deliveryPipeline };
}

const createCache = (team: string, bucket: google_native.storage.v1.Bucket) => new google_native.storage.v1.BucketObject(`cache-${team}`, {
    bucket: bucket.name,
    name: `${team}/cache`,
    source: new pulumi.asset.FileAsset("./resources/cache"),
});

const createIntegrationPipeline = (team: string, bucket: google_native.storage.v1.Bucket) => new google_native.cloudbuild.v1.Trigger(`cloud-build-${team}`, {
    eventType: google_native.cloudbuild.v1.TriggerEventType.Repo,
    filename: team !== "ledger" ? "cloudbuild.yaml" : "cloudbuild-mvnw.yaml",
    includedFiles: [
        `src/${team}/**`,
        "src/components/**",
    ],
    name: `${team}-ci`,
    projectId: projectId,
    triggerTemplate: {
        branchName: `^cicd-skaffold-kustomize$`,
        repoName: "bank-of-anthos",
        project: projectId,
    },
    substitutions: {
        _DEPLOY_UNIT: team,
        _CACHE_URI: pulumi.interpolate`gs://${bucket.name}/${team}/cache`,
        _CONTAINER_REGISTRY: `${region}-docker.pkg.dev/${projectId}/${registryName}`,
    },
}, {
    dependsOn: [api.cloudbuild],
});

const createDeliveryPipeline = (team: string, targetNames: string[], envs: { [key: string]: Env }) => {
    const targets = targetNames.map(name => envs[name].target);
    const stages = targetNames.map(name => ({ targetId: name, profiles: [name] }));
    return new google_native.clouddeploy.v1.DeliveryPipeline(`cloud-deploy-${team}`, {
        deliveryPipelineId: team,
        description: `Delivery pipeline for ${team} team.`,
        serialPipeline: {
            stages
        },
    }, {
        dependsOn: [
            api.clouddeploy,
            ...targets
        ],
    });
}