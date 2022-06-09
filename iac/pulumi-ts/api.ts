import * as gcp from "@pulumi/gcp";

// define required apis
const enabledApis = [
    "container",
    "compute",
    "artifactregistry",
    "sourcerepo",
    "cloudbuild",
    "clouddeploy"
].map(api => ({
    [api]: new gcp.projects.Service(`api-${api}`, {
        disableDependentServices: true,
        service: `${api}.googleapis.com`
    })
}))

export default Object.assign({}, ...enabledApis);

export type Apis = {string: gcp.projects.Service};