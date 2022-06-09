import * as pulumi from "@pulumi/pulumi";
import * as google_native from "@pulumi/google-native";
import api from "./api";

const gcpConfig = new pulumi.Config('google-native');
const project = gcpConfig.require("project");
const region = gcpConfig.require("region");

export type Env = {
    network: google_native.compute.v1.Network,
    cluster: google_native.container.v1.Cluster,
    target: google_native.clouddeploy.v1.Target,
}

export const createEnv = (name: string) => {
    const network = createNetwork(name);
    const cluster = createCluster(name, network);
    const target = createTarget(name, cluster);
    return {network, cluster, target};
}

const createNetwork = (name: string) => new google_native.compute.v1.Network(`network-${name}`, {
    name,
    autoCreateSubnetworks: true,
}, {
    dependsOn: [api.compute],
});

const createCluster = (name: string, network: google_native.compute.v1.Network) => new google_native.container.v1.Cluster(`cluster-${name}`, {
    name,
    autopilot: {
        enabled: true,
    },
    network: name,
}, {
    dependsOn: [
        api.container,
        network,
    ],
});

const createTarget = (name: string, cluster: google_native.container.v1.Cluster) => new google_native.clouddeploy.v1.Target(`target-${name}`, {
    targetId: name,
    gke: {
        cluster: `projects/${project}/locations/${region}/clusters/${name}`,
    },
}, {
    dependsOn: [cluster],
});