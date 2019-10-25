.PHONY: cluster deploy logs

PROJECT_ID=sanche-testing-project

cluster:
	gcloud container clusters create financial-app --project ${PROJECT_ID} --zone=us-central1-a

deploy:
	gcloud container clusters get-credentials --project ${PROJECT_ID} financial-app --zone us-central1-a
	skaffold run --default-repo=gcr.io/${PROJECT_ID}

logs:
	 kubectl logs -l app=ledgerwriter -f
