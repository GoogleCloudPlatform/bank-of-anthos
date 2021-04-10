# HTTPS Frontend with GCP ManagedCerts + Static IP

This directory contains manifests for setting up an HTTPS-only Bank of Anthos frontend, using a GCP Static IP, a ManagedCertificate configured through GKE, and a domain. 

### Prerequisites 

1. Bank of Anthos deployed to a GKE cluster
2. A domain name you own (+ can manage DNS for)


### Setup 


2. Delete the existing Bank of Anthos frontend service (type=Loadbalancer). 

```
kubectl delete svc frontend 
```

1. Create a global static IP. 

```
gcloud compute addresses create frontend-ip --global
```

1. Get the IP address you just created. 

```
gcloud compute addresses describe frontend-ip --global
```

1. Deploy the frontend Nodeport service in this directory. 

```
kubectl apply -f frontend-nodeport.yaml
```

4. Edit `managed-cert.yaml` and replace `domain` with your domain. 

```
apiVersion: networking.gke.io/v1beta2
kind: ManagedCertificate
metadata:
  name: boa-frontend-cert
spec:
  domains:
    - [YOUR_DOMAIN]
```


5. Apply `managed-cert.yaml` to your cluster. 

```
kubectl apply -f managed-cert.yaml 
```

6. Deploy the frontend ingress resource to your cluster. 

```
kubectl apply -f frontend-ingress.yaml
```

1. Update your DNS A-Record to point to that IP. 


1. Make sure the managedcertificate becomes active. This can take about 10 minutes. 

### Validating the HTTPS Frontend 

You should only be able to access the frontend in a browser with a valid certificate: 


If you try to access the ingress IP with HTTP in a browser or using curl, you should get this error: 

```

```


### Cleanup 

To delete your static 

```
gcloud compute addresses delete frontend-ip --global --quiet
kubectl delete -f .
```