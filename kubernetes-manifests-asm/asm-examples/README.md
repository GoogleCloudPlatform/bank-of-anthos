# Bank of Anthos - Anthos Service Mesh Examples

This directory contains a range of manifests that enable you to explore the functionality of Anthos Service Mesh with the Bank of Anthos.

Before performing any of the steps documented below - you should perform the standard deployment using the [provided ASM Manifests](./kubernetes-manifests-asm/README.md).

### 1 - Fault Injection
First - we will experiment with the [Fault Injection capability](https://istio.io/latest/docs/tasks/traffic-management/fault-injection/) of Anthos Service Mesh and inject some faults into the [frontend](/) service. 