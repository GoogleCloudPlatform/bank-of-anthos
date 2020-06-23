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

ZONE=us-west1-a
CLUSTER=bank-of-anthos

cluster: check-env
	gcloud beta container clusters create ${CLUSTER} \
		--project=${PROJECT_ID} --zone=${ZONE} \
		--machine-type=n1-standard-2 --num-nodes=4 \
		--enable-stackdriver-kubernetes --subnetwork=default \
		--labels csm=
	skaffold run --default-repo=gcr.io/${PROJECT_ID} -l skaffold.dev/run-id=${CLUSTER}-${PROJECT_ID}-${ZONE}

deploy: check-env
	echo ${CLUSTER}
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold run --default-repo=gcr.io/${PROJECT_ID} -l skaffold.dev/run-id=${CLUSTER}-${PROJECT_ID}-${ZONE}

deploy-continuous: check-env
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold dev --default-repo=gcr.io/${PROJECT_ID}

checkstyle:
	mvn checkstyle:check
	# disable warnings: import loading, todos, function members, duplicate code, public methods
	pylint --rcfile=./.pylintrc ./src/*/*.py

check-env:
ifndef PROJECT_ID
	$(error PROJECT_ID is undefined)
endif

ifndef ZONE
	$(error ZONE is undefined)
endif
