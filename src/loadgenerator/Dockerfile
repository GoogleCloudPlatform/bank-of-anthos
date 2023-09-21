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
FROM python:3.11.5-slim@sha256:edaf703dce209d774af3ff768fc92b1e3b60261e7602126276f9ceb0e3a96874 as base

FROM base as builder

# Install dependencies.
COPY requirements.txt .
RUN pip install --prefix="/install" -r requirements.txt

FROM base

# Set our working directory
WORKDIR /app

COPY --from=builder /install /usr/local

# Add application code.
COPY locustfile.py .

# show python logs as they occur
ENV PYTHONUNBUFFERED=0

# enable gevent support in debugger
ENV GEVENT_SUPPORT=True

# explicitly set a fallback log level in case no log level is defined by Kubernetes
ENV LOG_LEVEL info

# start loadgenerator
ENTRYPOINT locust --host="http://${FRONTEND_ADDR}" --loglevel $LOG_LEVEL --headless --users="${USERS:-10}" 2>&1
