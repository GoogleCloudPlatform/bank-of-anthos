.PHONY: cluster

PROJECT_ID=sanche-testing-project

cluster:
	gcloud container clusters create financial-app --zone=us-central1-a

deploy:
	gcloud container clusters get-credentials financial-app --zone us-central1-a
	skaffold run --default-repo=gcr.io/${PROJECT_ID}
