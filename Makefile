.PHONY: cluster deploy logs

PROJECT_ID=hybwksp34
ZONE=us-central1-a
CLUSTER=financial-app-istio

cluster:
	gcloud beta container clusters create ${CLUSTER} \
		--project=${PROJECT_ID} --zone=${ZONE} \
		--cluster-version=1.13.11-gke.9 \
		--machine-type=n1-standard-2 --num-nodes=4 \
		--enable-stackdriver-kubernetes --subnetwork=default \
		--identity-namespace=${PROJECT_ID}.svc.id.goog --labels csm=
	# install istio
	curl -L https://git.io/getLatestIstio |  ISTIO_VERSION=1.3.0 sh -
	kubectl create namespace istio-system
	helm template istio-1.3.0/install/kubernetes/helm/istio-init \
		--name istio-init --namespace istio-system | kubectl apply -f -
	kubectl -n istio-system wait --for=condition=complete job --all
	helm template istio-1.3.0/install/kubernetes/helm/istio \
		--name istio --namespace istio-system | kubectl apply -f -

deploy:
	#kubectl delete deployment ledgerwriter 2> /dev/null
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold run --default-repo=gcr.io/${PROJECT_ID}

logs:
	 kubectl logs -l app=ledgerwriter -f
