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

#
# Set all the personal information in this file:
#

source ./setEnvVars.sh

#
# Tear down the firewall rule:
#

echo "Deleting firewall rule"
gcloud compute firewall-rules delete ${FIREWALL_RULE_NAME} --project ${PROJECT}

#
# Release the static external IP:
#

echo "Releasing the static external IP"
gcloud compute addresses delete ${ADDRESS_NAME} --region ${REGION} --project ${PROJECT}
