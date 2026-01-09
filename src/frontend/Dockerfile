# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Use the official Python docker container, slim version, running Debian
FROM python:3.14.1-slim@sha256:b823ded4377ebb5ff1af5926702df2284e53cecbc6e3549e93a19d8632a1897e AS base

FROM base AS builder

# Install dependencies.
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base

# Set our working directory
WORKDIR /app

COPY --from=builder /install /usr/local

# Show python logs as they occur
ENV PYTHONUNBUFFERED=0

# Explicitly set a fallback log level in case no log level is defined by Kubernetes
ENV LOG_LEVEL info

# Add application code.
COPY . .

# Ensure files are readable for non-root users
RUN find . -type f -name '*' -exec chmod a+r '{}' ';'

# --- START OF CORRECTION FOR ISSUE #517 ---

# Create a non-root user and group
RUN useradd -m -u 1000 appuser

# Change ownership of the application directory to the new user
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# --- END OF CORRECTION ---

# Start server using gunicorn
CMD gunicorn -b :$PORT --threads 4 --log-config logging.conf --log-level=$LOG_LEVEL "frontend:create_app()"