# Apigee + ASM

[Apigee](https://cloud.google.com/apigee) + [Anthos Service Mesh](https://cloud.google.com/anthos/service-mesh) can be leveraged to expose the Bank of Anthos microservices as a set of secure, managed APIs which can be accessed by other applications (e.g. mobile apps, voice assistants and more) or by partner developers.

[Apigee Developer Portals](https://cloud.google.com/apigee/docs/api-platform/publish/publishing-overview) provide self-service developer onboarding and allow for creation of easy-to-use [API documentation with try-it functionality](https://cloud.google.com/apigee/docs/api-platform/publish/intro-portals).

[Apigee Analytics](https://cloud.google.com/apigee/docs/api-platform/analytics/analytics-services-overview) provides API teams with rich dashboards, including operational metrics and detailed API product usage stats, plus [API Monitoring](https://cloud.google.com/apigee/docs/api-monitoring) capabilities.

[Apigee Monetization](https://cloud.google.com/apigee/docs/api-platform/monetization/overview) allows you to build paid rate plans to monetize access to API products.

Bank of Anthos supports the ability to authorize external access requests made using an [OAuth 2.0 Authorization Code grant type](https://oauth.net/2/grant-types/authorization-code/). Apigee can act as the [authorization server](https://cloud.google.com/apigee/docs/api-platform/security/oauth/oauth-home) that issues and validates the access tokens used to call the APIs securely. This directory contains a [ConfigMap](https://kubernetes.io/docs/concepts/configuration/configmap/) that defines an allowed OAuth client ID and redirect URI. The frontend service will use these to validate incoming OAuth requests. These values should be replaced with a client ID and redirect URI that is defined in an Apigee [API proxy](https://cloud.google.com/apigee/docs/api-platform/fundamentals/understanding-apis-and-api-proxies) that implements the [authorization code grant type](https://cloud.google.com/apigee/docs/api-platform/security/oauth/oauth-v2-policy-authorization-code-grant-type).

## Prerequisites

This requires an Apigee Organization that has already been provisioned. Learn how to provision a free eval org [here](https://cloud.google.com/apigee/docs/api-platform/get-started/eval-orgs).