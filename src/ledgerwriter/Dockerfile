# Copyright 2019 Google LLC
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

# Use maven to compile the java application.
FROM docker.io/maven AS build-env

WORKDIR /app

# copy the pom.xml file to download dependencies
COPY pom.xml ./

# download dependencies as specified in pom.xml
RUN mvn verify --fail-never

# Copy the rest of the working directory contents into the container.
COPY . ./

# Compile the application.
RUN mvn -Dmaven.test.skip=true package

# Build runtime image.
FROM docker.io/openjdk:8-jdk-alpine

# Copy the compiled files over.
COPY --from=build-env /app/target /app/

# Starts java app with debugging server at port 5005.
ENTRYPOINT ["java", "-jar", "/app/ledgerwriter-1.0.jar"]
