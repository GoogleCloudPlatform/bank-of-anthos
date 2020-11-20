# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.-PHONY: cluster deploy deploy-continuous logs checkstyle check-env

CLUSTER=bank-of-anthos
E2E_PATH=${PWD}/.github/workflows/ui-tests/

cluster: check-env
	gcloud container clusters create ${CLUSTER} \
		--project=${PROJECT_ID} --zone=${ZONE} \
		--machine-type=e2-standard-4 --num-nodes=4 \
		--enable-stackdriver-kubernetes --subnetwork=default \
		--labels csm=

deploy: check-env
	echo ${CLUSTER}
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold run --default-repo=gcr.io/${PROJECT_ID} -l skaffold.dev/run-id=${CLUSTER}-${PROJECT_ID}-${ZONE}

deploy-continuous: check-env
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold dev --default-repo=gcr.io/${PROJECT_ID}

monolith: check-env
ifndef GCS_BUCKET
	# GCS_BUCKET is undefined
	# ATTENTION: Deployment proceeding with canonical pre-built monolith artifacts
endif
	# build and deploy Bank of Anthos along with a monolith backend service
	mvn -f src/ledgermonolith/ package
	src/ledgermonolith/scripts/build-artifacts.sh
	src/ledgermonolith/scripts/deploy-monolith.sh
	(cd src/ledgermonolith/kubernetes-manifests; sed 's/\[PROJECT_ID\]/${PROJECT_ID}/g' config.yaml.template > config.yaml)
	(cd src/ledgermonolith; skaffold run --default-repo=gcr.io/${PROJECT_ID} -l skaffold.dev/run-id=${CLUSTER}-${PROJECT_ID}-${ZONE})

monolith-build: check-env
ifndef GCS_BUCKET
	$(error GCS_BUCKET is undefined; specify a Google Cloud Storage bucket to store your build artifacts)
endif
	# build the artifacts for the ledgermonolith service 
	mvn -f src/ledgermonolith/ package
	src/ledgermonolith/scripts/build-artifacts.sh

monolith-deploy: check-env
ifndef GCS_BUCKET
	# GCS_BUCKET is undefined
	# ATTENTION: Deployment proceeding with canonical pre-built monolith artifacts
endif
	# deploy the ledgermonolith service to a GCE VM
	src/ledgermonolith/scripts/deploy-monolith.sh

checkstyle:
	mvn checkstyle:check
	# disable warnings: import loading, todos, function members, duplicate code, public methods
	pylint --rcfile=./.pylintrc ./src/*/*.py

test-e2e:
	E2E_URL="http://$(shell kubectl get service frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')" && \
	docker run -it -v ${E2E_PATH}:/e2e -w /e2e -e CYPRESS_baseUrl=$${E2E_URL} cypress/included:5.0.0 $(E2E_FLAGS)

test-unit:
	mvn test
	for SERVICE in "contacts" "userservice"; \
	do \
		pushd src/$$SERVICE;\
			python3 -m venv $$HOME/venv-$$SERVICE; \
			source $$HOME/venv-$$SERVICE/bin/activate; \
			pip install -r requirements.txt; \
			python -m pytest -v -p no:warnings; \
			deactivate; \
		popd; \
	done

check-env:
ifndef PROJECT_ID
	$(error PROJECT_ID is undefined)
else ifndef ZONE
	$(error ZONE is undefined)
endif
