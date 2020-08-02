#!/bin/bash

curl -L https://storage.googleapis.com/istio-release/releases/1.6.7/deb/istio-sidecar.deb > istio-sidecar.deb
sudo dpkg -i istio-sidecar.deb

# update /etc/hosts
echo "${ISTIOD_IP} istiod.istio-system.svc" | sudo tee -a /etc/hosts

# install certs
sudo mkdir -p /etc/certs
sudo cp {root-cert.pem,cert-chain.pem,key.pem} /etc/certs
sudo mkdir -p /var/run/secrets/istio/
sudo cp root-cert.pem /var/run/secrets/istio/

# install cluster.env
sudo cp cluster.env /var/lib/istio/envoy

# transfer file ownership to istio proxy
sudo chown -R istio-proxy /etc/certs /var/lib/istio/envoy /var/run/secrets/istio/

# start Istio
sudo systemctl start istio