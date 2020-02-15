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

.-PHONY: cluster deploy deploy-continuous logs checkstyle clean

PROJECT_ID=hybwksp34
ZONE=us-west1-a
CLUSTER=financial-demo
ACCOUNT=hybwksp34@anthosworkshop.com

cluster: jwtRS256.key
	./create_cluster.sh ${PROJECT_ID} ${CLUSTER} ${ZONE}
	kubectl create secret generic jwt-key --from-file=./jwtRS256.key --from-file=./jwtRS256.key.pub
	skaffold run --default-repo=gcr.io/${PROJECT_ID}

deploy:
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold run --default-repo=gcr.io/${PROJECT_ID}

deploy-continuous:
	gcloud container clusters get-credentials --project ${PROJECT_ID} ${CLUSTER} --zone ${ZONE}
	skaffold dev --default-repo=gcr.io/${PROJECT_ID}

logs:
	 kubectl logs -l app=frontend -c front

jwtRS256.key:
	openssl genrsa -out jwtRS256.key 4096
	openssl rsa -in jwtRS256.key -outform PEM -pubout -out jwtRS256.key.pub

checkstyle:
	mvn checkstyle:check
	# disable warnings: import loading, todos, function members, duplicate code
	pylint --disable=F0401 --disable=W0511 --disable=E1101 --disable=R0801  ./src/*/*.py

clean:
	rm -f jwtRS256*
