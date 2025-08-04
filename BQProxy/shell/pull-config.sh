###
# Copyright 2015-2025, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

if [ ! -f "/home/circleci/${CIRCLE_PROJECT_REPONAME}/${DEPLOYMENT_CONFIG}" ]; then
    gsutil cp gs://${DEPLOYMENT_BUCKET}/${DEPLOYMENT_CONFIG} /home/circleci/${CIRCLE_PROJECT_REPONAME}/
    chmod ugo+r /home/circleci/${CIRCLE_PROJECT_REPONAME}/${DEPLOYMENT_CONFIG}
    if [ ! -f "/home/circleci/${CIRCLE_PROJECT_REPONAME}/${DEPLOYMENT_CONFIG}" ]; then
      echo "[ERROR] Couldn't assign deployment configuration file '${DEPLOYMENT_CONFIG}' - exiting."
      exit 1
    else
      echo "Downloaded deployment configuration file."
    fi
else
    echo "Found deployment configuration file."
fi