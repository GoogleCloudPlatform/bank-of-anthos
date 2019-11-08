.PHONY: cluster deploy secrets logs

PROJECT_ID=hybwksp34
ZONE=us-central1-a
CLUSTER=financial-app-istio
ACCOUNT=hybwksp34@anthosworkshop.com

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
	kubectl create clusterrolebinding cluster-admin-binding \
		--clusterrole="cluster-admin" --user=${ACCOUNT}
	gsutil cat gs://csm-artifacts/stackdriver/stackdriver.istio.csm_beta.yaml | \
		sed 's@<mesh_uid>@'${PROJECT_ID}/${ZONE}/${CLUSTER}@g | kubectl apply -f -
	# enable ASM
	gcloud iam service-accounts create istio-mixer --display-name istio-mixer --project ${PROJECT_ID} | true
	gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:istio-mixer@${PROJECT_ID}.iam.gserviceaccount.com --role=roles/contextgraph.asserter
	gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:istio-mixer@${PROJECT_ID}.iam.gserviceaccount.com --role=roles/logging.logWriter
	gcloud projects add-iam-policy-binding ${PROJECT_ID} --member=serviceAccount:istio-mixer@${PROJECT_ID}.iam.gserviceaccount.com --role=roles/monitoring.metricWriter
	gcloud iam service-accounts add-iam-policy-binding --role roles/iam.workloadIdentityUser --member "serviceAccount:${PROJECT_ID}.svc.id.goog[istio-system/istio-mixer-service-account]" istio-mixer@${PROJECT_ID}.iam.gserviceaccount.com
	kubectl annotate serviceaccount --namespace istio-system istio-mixer-service-account iam.gke.io/gcp-service-account=istio-mixer@${PROJECT_ID}.iam.gserviceaccount.com
	# enable sidecars in default namespace
	kubectl label namespace default istio-injection=enabled
	# add secrets
	./secrets/create_keys.sh | true

secrets:
	./secrets/create_keys.sh | true

deploy:
	#kubectl delete deployment ledgerwriter 2> /dev/null
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold run --default-repo=gcr.io/${PROJECT_ID}

logs:
	 kubectl logs -l app=ledgerwriter -f
