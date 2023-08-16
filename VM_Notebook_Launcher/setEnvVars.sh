#!/usr/bin/env bash

# Copyright 2019, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

USER_NAME=your_user_name
MACHINE_NAME=${USER_NAME}-unique-machine-name-1
FIREWALL_TAG=${USER_NAME}-restricted-jupyter
FIREWALL_RULE_NAME=${USER_NAME}-jupyter-firewall-rule
# Choose one format and change to your IP range for your desktop:
FIREWALL_IP_RANGE=10.0.0.1
#FIREWALL_IP_RANGE=10.0.0.1,10.0.0.2
#FIREWALL_IP_RANGE=10.0.0.0/16
DISK_SIZE=30GB
MACHINE_TYPE=n1-standard-1
SERV_PORT=5000
MACHINE_DESC="Jupyter Notebook Server for ${USER_NAME}"
PROJECT=your-project-id
USER_AND_MACHINE=${USER_NAME}@${MACHINE_NAME}
ZONE=us-central1-c
REGION=us-central1
ADDRESS_NAME=${USER_NAME}-jupyter-address
CERT_SUBJ='/C=US/ST=MyState/L=MyCity/O=MyInstitution/OU=MyDepartment/CN='