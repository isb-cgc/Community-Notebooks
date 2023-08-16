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
# Uses netstat and top to determine if child processes of the Jupyter Notebook server have any
# CPU activity. Note that tiny amounts of activity could still present as 0.0 CPU, so it is
# useful to recall this for  e.g. 60 seconds.
# Requires the configuration script to be in the ${HOME}/bin directory
#

#
# Set all the personal information in this file:
#

source ./setEnvVars.sh

#
# Restart the VM:
#

echo "Starting up the server VM"
gcloud compute instances start ${MACHINE_NAME} --zone ${ZONE} --project ${PROJECT}