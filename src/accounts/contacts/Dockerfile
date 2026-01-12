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
FROM python:3.14.2-slim@sha256:3955a7dd66ccf92b68d0232f7f86d892eaf75255511dc7e98961bdc990dc6c9b AS base

FROM base AS builder

# Install dependencies.
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base

# Set our working directory
WORKDIR /app

COPY --from=builder /install /usr/local

# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# explicitly set a fallback log level in case no log level is defined by Kubernetes
ENV LOG_LEVEL info

# Add application code.
COPY . .

# Ensure files are readable for non-root users
RUN chmod a+r *

CMD gunicorn -b :$PORT --threads 4 --log-config logging.conf --log-level=$LOG_LEVEL "contacts:create_app()"
