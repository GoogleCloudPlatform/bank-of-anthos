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
FROM python:3.14.6-slim@sha256:44dd04494ee8f3b538294360e7c4b3acb87c8268e4d0a4828a6500b1eff50061 AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

FROM base AS builder

# Set working directory
WORKDIR /app

# Install dependencies.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM base

# Set our working directory
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# show python logs as they occur (any non-empty value enables unbuffered
# mode in Python, but use "1" so it doesn't read as "disabled" at a glance)
ENV PYTHONUNBUFFERED=1

# explicitly set a fallback log level in case no log level is defined by Kubernetes
ENV LOG_LEVEL info

# Add application code.
COPY . .

# Create the same non-root UID/GID that the Kubernetes securityContext uses
# (runAsUser/runAsGroup: 1000 in kubernetes-manifests/userservice.yaml), and make
# app files readable by it, so `docker run` locally behaves the same as it
# does in the cluster.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser \
    && chmod -R a+rX .

USER 1000:1000

# Start server using gunicorn
CMD gunicorn -b :$PORT --threads 2 --log-config logging.conf --log-level=$LOG_LEVEL "userservice:create_app()"
