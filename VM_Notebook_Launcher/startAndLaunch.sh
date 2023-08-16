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
# Build the firewall rule for the project if it does not exist:
#

FIRE=`gcloud compute firewall-rules describe ${FIREWALL_RULE_NAME} --project ${PROJECT} 2>/dev/null`
if [ -z "${FIRE}" ]; then
  echo "Creating a firewall rule for the notebook VM"
  gcloud compute firewall-rules create ${FIREWALL_RULE_NAME} --allow=tcp:${SERV_PORT} --target-tags=${FIREWALL_TAG} --source-ranges=${FIREWALL_IP_RANGE} --project ${PROJECT}
fi

echo "Firewall rule installed:"
gcloud compute firewall-rules describe ${FIREWALL_RULE_NAME} --project ${PROJECT} 2>/dev/null | grep "name:"

#
# Get a static external IP if one does not exist:
#

DESC=`gcloud compute addresses describe ${ADDRESS_NAME} --region ${REGION} --project ${PROJECT} 2>/dev/null`
if [ -z "${DESC}" ]; then
  echo "Creating a static external IP address for the notebook VM"
  gcloud compute addresses create ${ADDRESS_NAME} --region ${REGION} --project ${PROJECT}
fi

EXTR_ADDR=`gcloud compute addresses describe ${ADDRESS_NAME} --region ${REGION} --project ${PROJECT} | grep "address:" | awk -F: '{print $2}'`
echo "Static external IP address reserved:"
echo $EXTR_ADDR

#
# We need to have Stackdriver monitoring API enabled in the project so we can monitor the VM and shut it down if
# it is idle for an extended period of time:
#

NEED_API=monitoring.googleapis.com
MONITOR_API=`gcloud services list --project ${PROJECT} | awk '{print $1}' | grep ${NEED_API}`
if [ -z "${MONITOR_API}" ]; then
  echo "Enabling Google Stackdriver monitoring API for project to track and shutdown idle VMs"
  gcloud services enable ${NEED_API} --project ${PROJECT}
fi


#
# Spin up the VM:
# TODO: Issues with larger disks!
# If you want a machine with more that 10GB, you need to specify a larger disk size.
# Currently that is done with --boot-disk-size argument
# Google complains that "WARNING: You have selected a disk size of under [200GB]. This may result in poor I/O performance."
# Google also compalins that "You might need to resize the root repartition manually if the operating system does not
# support automatic resizing."
#
# At least with Debian 9, I am seeing "/dev/sda1 30G  1.7G   27G   6%" on a fresh machine.
#
# Note the monitoring scope, which we need to do the idle monitoring
#

echo "Starting up the server VM"
gcloud compute instances create "${MACHINE_NAME}" --description "${MACHINE_DESC}" --zone "${ZONE}" \
  --machine-type ${MACHINE_TYPE} --image-project debian-cloud --image-family "debian-9" --boot-disk-size ${DISK_SIZE} \
  --project ${PROJECT} --scopes="bigquery,storage-rw,monitoring" --address ${EXTR_ADDR}  --tags ${FIREWALL_TAG}

#
# Get the password from the user, get it up to the machine:
#

echo
echo "Need the password for the notebook server:"
python3 get_pass.py
gcloud compute scp passhash.txt ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
rm passhash.txt

#
# Get the ssl cert info up to the machine:
#

FULL_CERT_SUBJ=${CERT_SUBJ}${EXTR_ADDR}
echo ${FULL_CERT_SUBJ} > certSubj.txt
gcloud compute scp certSubj.txt ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
rm certSubj.txt

#
# Get the chosen port up to the machine:
#

echo ${SERV_PORT} > port.txt
gcloud compute scp port.txt ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
rm port.txt

#
# Get the setEnvVars file up to the machine so it can use it:
#

echo "Uploading config info to the VM"
gcloud compute scp setEnvVars.sh ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}

#
# Get the install script and run script up to the machine:
#

echo "Uploading installation script to the VM"
gcloud compute scp install_script.sh ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
gcloud compute ssh --project ${PROJECT} --zone ${ZONE} ${USER_AND_MACHINE} --command 'chmod u+x install_script.sh'

#
# Get the idle monitor scripts and idle shutdown script up to the machine:
#

echo "Uploading idle monitor and shutdown scripts"
gcloud compute scp cpuLogger.sh ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
gcloud compute scp idle_checker.py ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
gcloud compute scp idle_log_wrapper.sh ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
gcloud compute scp idle_shutdown.py ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}
gcloud compute scp shutdown_wrapper.sh ${USER_AND_MACHINE}: --zone ${ZONE} --project ${PROJECT}

#
# Run the install script:
#

echo "Running installation script on the VM"
gcloud compute ssh --project ${PROJECT} --zone ${ZONE} ${USER_AND_MACHINE} --command './install_script.sh'

#
# Start the browser:
#

sleep 10

./run_browser.sh