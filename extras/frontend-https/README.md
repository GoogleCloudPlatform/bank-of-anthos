# HTTPS Frontend 

This directory contains instructions for how to deploy the Bank of Anthos frontend with HTTPS, using a GCP Static IP and Ingress. 

## Prerequisites 

- `openssl` tool 
- GKE cluster 


## Steps 

1. Create a global static IP. 

```
gcloud compute addresses create bank-of-anthos-frontend --global 
```

2. Get the IP value and copy the `address` value to the clipboard. 

```
gcloud compute addresses describe bank-of-anthos-frontend --global
```

3. Create a private key. 

```
openssl genrsa -out private.key 2048
```

4. Create a certificate signing request where `CN` (common name) is the global IP value you copied in step 2. 

```
openssl req -new -key private.key -out frontend.csr \
    -subj "/CN=first-domain"

openssl req -new -key private.key -out frontend.csr \
    -subj "/CN=34.117.200.91"
```

5. Create a certificate containing the public key. 

```
openssl x509 -req -days 365 -in frontend.csr -signkey private.key \
    -out public.crt
```

6. Create a Kubernetes secret in your GKE cluster.  

```
kubectl create secret tls frontend-tls --cert=public.crt --key=private.key
```

7. Deploy the app as normal, using `kubectl apply -f kubernetes-manifests`. 


8. Delete the frontend LoadBalancer service. 

```
kubectl delete svc frontend 
```

9.  Deploy the frontend nodeport and ingress resources in this directory. 

```
kubectl apply -f frontend-nodeport.yaml 
kubectl apply -f frontend-ingress.yaml 
```

