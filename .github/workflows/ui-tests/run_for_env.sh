# if cypress_baseurl is not set
if [[ -z "${CYPRESS_baseUrl}" ]]; then
    # Get credentials for current Anthos cluster (staging/production)
    export ANTHOS_MEMBERSHIP_SHORT=$(echo $ANTHOS_MEMBERSHIP | rev | cut -d/ -f1 | rev)
    gcloud container fleet memberships get-credentials $ANTHOS_MEMBERSHIP_SHORT
    if [[ "$ANTHOS_MEMBERSHIP_SHORT" == "staging-membership" ]]; then
        export CYPRESS_baseUrl=$(kubectl get service frontend --namespace bank-of-anthos-staging -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    elif [[ "$ANTHOS_MEMBERSHIP_SHORT" == "production-membership" ]]; then
        export CYPRESS_baseUrl=$(kubectl get ingress frontend-ingress --namespace bank-of-anthos-production -o jsonpath='{.status.loadBalancer.ingress[0].ip}') # TODO: consider switching to domain name
    else
        echo ERROR: CYPRESS_baseUrl is not set and cannot be automatically determined. Exiting with status code 1.
        exit 1
    fi
fi

# run tests
cypress run
