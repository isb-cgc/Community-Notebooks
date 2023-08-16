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

source ./setEnvVars.sh

EXTR_ADDR=`gcloud compute addresses describe ${ADDRESS_NAME} --region ${REGION} --project ${PROJECT} | grep "address:" | awk -F: '{print $2}'`

EXTR_ADDR="$(echo -e "${EXTR_ADDR}" | tr -d '[:space:]')"
python -m webbrowser -t "https://${EXTR_ADDR}:${SERV_PORT}"