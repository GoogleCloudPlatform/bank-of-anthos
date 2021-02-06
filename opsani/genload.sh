#!/bin/bash

DURATION=600
echo ""
echo "Change the load generator deployment scale every ${DURATION} seconds"
while [ true ]; do
    for item in 1 2 3 4 3 2 1 2 1 3 1 2 4 2 1 3 1 4 ; do
	echo "generating load ${item}"
        kubectl scale deployment loadgenerator --replicas ${item}
        sleep $(( ( RANDOM % ${DURATION} )  + 1 ))
    done
done
