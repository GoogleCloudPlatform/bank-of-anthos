#!/bin/bash
# Copyright 2020 Google LLC
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

set -euo pipefail

# install git, kubectl, maven, jdk, pip
sudo apt-get -y install git kubectl maven default-jdk python3-pip python3-venv

# install go
curl -O https://storage.googleapis.com/golang/go1.17.5.linux-amd64.tar.gz
tar -xvf go1.17.5.linux-amd64.tar.gz
sudo chown -R root:root ./go
sudo mv go /usr/local
echo 'export GOPATH=$HOME/go' >> ~/.profile
echo 'export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin' >> ~/.profile
source ~/.profile

# install addlicense
go install github.com/google/addlicense@latest
sudo ln -s $HOME/go/bin/addlicense /bin

# install pylint
sudo pip3 install pylint

# install kind
curl -Lo ./kind "https://github.com/kubernetes-sigs/kind/releases/download/v0.7.0/kind-$(uname)-amd64" && \
chmod +x ./kind && \
sudo mv ./kind /usr/local/bin

# install skaffold
curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64 && \
chmod +x skaffold && \
sudo mv skaffold /usr/local/bin

# install docker
sudo apt -y install apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add - && \
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
sudo apt update && \
sudo apt -y install docker-ce && \
sudo usermod -aG docker ${USER}

# reboot for docker setup
sudo reboot

# download jdk 17
wget https://download.java.net/java/GA/jdk17.0.1/2a2082e5a09d4267845be086888add4f/12/GPL/openjdk-17.0.1_linux-x64_bin.tar.gz
sudo tar xf openjdk-*.tar.gz -C /opt

# download maven 3.8
wget https://dlcdn.apache.org/maven/maven-3/3.8.5/binaries/apache-maven-3.8.5-bin.tar.gz
sudo tar xf apache-maven-*.tar.gz -C /opt

# set up profile for jdk and maven
sudo tee /etc/profile.d/java.sh <<EOF
export JAVA_HOME=/opt/jdk-17.0.1
export M2_HOME=/opt/apache-maven-3.8.5
export MAVEN_HOME=/opt/apache-maven-3.8.5
export PATH=\$JAVA_HOME/bin:\$M2_HOME/bin:\$PATH
EOF
sudo chmod +x /etc/profile.d/java.sh
source /etc/profile.d/java.sh