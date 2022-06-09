#!/bin/bash

# Created with codelabba.rb v.1.4a
source .env.sh || fatal 'Couldnt source this'
set -x
set -e

# Add your code here:
EXTERNAL_IP=$( kubectl get service frontend 2>/dev/null | tail -1| awk '{print $4}' )

echo "EXTERNAL_IP for Bank of Anthos is: '$EXTERNAL_IP' (if its empty you might want to wait until the cluster is cacthing up with you..)"
echo "If ok, please open on your browser: http://$EXTERNAL_IP"

# If you have GoogleChrome installed, let's open it automatically :)
which google-chrome &&
    google-chrome "http://$EXTERNAL_IP"


# End of your code here
verde Tutto ok.
