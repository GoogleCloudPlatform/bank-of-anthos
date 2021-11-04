# Enable TLS support on the Multi Cluster Ingress
---

In this section we will enable **TLS** support _(with
**HTTP to HTTPS** redirection)_ on the **Multi Cluster Ingress** resource that was
created in the [Multi Cluster Bank of Anthos with Cloud SQL](README.md) guide.

## Prerequisites

- Bank of Anthos deployed in multiple clusters with access to Cloud SQL as shown
  in the [previous guide](README.md).
- This guide assumes that all the environment variables and **kubectx**(s) -
  _cluster1 & cluster2_ - are still valid
- This guide assumes that all the commands are executed from the same directory
  as this file ***`(extras/cloudsql-multicluster/tls-for-mci.md)`***

---

## Part 2

1. **Create a static IP address**. This will be used to generate the _self-signed_
   certificate.
```sh
gcloud compute addresses create boa-multi-cluster-ip --global
export STATIC_IP=`gcloud compute addresses describe boa-multi-cluster-ip --global --format="value(address)"`

echo $STATIC_IP
```

2. **Create the TLS certificate**
```sh
openssl genrsa -out private.key 2048
openssl req -new -key private.key -out frontend.csr -subj "/CN=${STATIC_IP}"
openssl x509 -req -days 365 -in frontend.csr -signkey private.key -out public.crt
```

3. **Install the TLS certificate as a Kubernetes secret in cluster1**. We use
   _cluster1_ here because that is the **config cluster** for
   MutliClusterIngress resources.
```sh
kubectx cluster1
kubectl create secret tls frontend-tls-multi --cert=public.crt --key=private.key
```

4. **Create the yaml configuration for the `FrontendConfig` and the updated `MultiClusterIngress` resource**.
   The `FrontendConfig` defines the redirection behaviour for HTTP to HTTPS.
   We then annotate the `MultiClusterIngress` resource with the `FrontendConfig`
   and the static IP we created. The `MultiClusterIngress` definition is also
   updated to use the TLS certificate via the Kubernetes secret we created.

```sh
envsubst < multicluster-ingress-https.template > multicluster-ingress-https.yaml
```

5. **Install the `FrontendConfig` and update the `MultiClusterIngress`**
```sh
kubectl apply -n ${NAMESPACE} -f multicluster-ingress-https.yaml
```

6. **Verify that the Multi Cluster Ingress resource was updated.**
   This may take a few minutes. Wait until the **VIP** of the `MultiClusterIngress`
   has been updated to your newly created STATIC_IP.

```sh
watch kubectl describe mci frontend-global-ingress -n ${NAMESPACE}
```

Expected output:

```sh
Status:
...
...
    URL Map:  mci-ddwsrr-default-frontend-global-ingress
  VIP:        <YOUR_STATIC_IP>
```

7. **Test HTTP to HTTPS redirection**

> **Note:** It may take several minutes _(approximately 5 minutes)_ for the
> ingress routes to be propagated and configured. So you might see **404** or
> **502** errors until the setup is complete.

```sh
curl -k -I http://$STATIC_IP
```

Expected output:

```sh
HTTP/1.1 301 Moved Permanently
Cache-Control: private
Content-Type: text/html; charset=UTF-8
Referrer-Policy: no-referrer
Location: https://<YOUR_STATIC_IP>/
Content-Length: 219
Date: Thu, 14 Oct 2021 03:11:00 GMT
```

8. **Test TLS connection via HTTPS**
```sh
curl -k -I https://$STATIC_IP
```

Expected output:

```sh
HTTP/2 200
content-type: text/html; charset=utf-8
content-length: 7025
date: Thu, 14 Oct 2021 03:12:44 GMT
via: 1.1 google
alt-svc: clear
```

🎉 **Congrats!** You can try accessing the application in your browser and
notice that you are automatically re-directed to **HTTPS**.
