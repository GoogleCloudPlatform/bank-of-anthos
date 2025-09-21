#!/bin/bash
# Copyright 2020, Google LLC.
# Licensed under the Apache License, Version 2.0

set -e

echo "Loading test data for user-portfolio-db..."

# Load test data SQL file
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < /docker-entrypoint-initdb.d/1-load-testdata.sql

echo "Test data loaded successfully!"
