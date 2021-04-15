# TLS with Google Managed Certificates

This directory contains a Kubernetes manifest that can be modified to enable secure TLS
for Bank of Anthos. More information can be found in the [GCP docs](https://cloud.google.com/kubernetes-engine/docs/how-to/managed-certs)

## Steps

1. Obtain a static IP address
    - `gcloud compute addresses create bank-address --global`
2. Obtain a domain name
    - From [Google Domains](https://domains.google/), or any other registrar
3. Create an A record to point your domain name to your static IP
    - [Instructions for Google Domains](https://support.google.com/domains/answer/9211383)
4. Modify `managed-certificates.yaml` as necessary
    - ensure `domains` and `kubernetes.io/ingress.global-static-ip-name` match your domain and static IP name
    - http can be optionally disabled with the `kubernetes.io/ingress.allow-http: "false"` annotation
5. Apply the manifest
    - `kubectl apply -f ./managed-certificates.yaml`
6. Update the `SCHEME` environment variable for the `frontend` service to `https`
7. Access your application at `https://YOUR_DOMAIN`
    - It may take a couple minutes for the Ingress resource to provision your LoadBalancer and certificates.
      You will see 502 and 404 errors in the mean time.
