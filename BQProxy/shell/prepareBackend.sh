#! /bin/bash

#TRUE or FALSE: does AppEngine need first-time set up in the project?"
NEED_APP_ENGINE_SETUP="FALSE"
#your app engine region
REGION="us-central1"
#your google project
PROJECT_ID="isb-cgc-dev-1"
#your redis cache name
REDIS_NAME="bq-proxy-cache"
#name for your connector
VAC_NAME="bq-proxy-connector"
# Recommended sizing
REDIS_SIZE_GB=1
VPC_MIN_INSTANCES=2
VPC_MAX_INSTANCES=3
VPC_MACHINE_TYPE="e2-micro"
#"TRUE or FALSE, using AppEngine Standard"
USING_AE_STANDARD=TRUE

# NOTE! Hardwired variables below to configure REDIS and the VPC connector! Edit if you don't like them


#
# If you have not yet created an AppEngine application in this project, this needs to happen first.
#

if [ "${NEED_APP_ENGINE_SETUP}" = "TRUE" ]; then
    gcloud app create --region=${REGION} --project=${PROJECT_ID}
fi

#
# We need two apis enabled to get the redis cache and the vpc connector installed:
#

gcloud services enable redis.googleapis.com --project=${PROJECT_ID}
gcloud services enable vpcaccess.googleapis.com --project=${PROJECT_ID}

#
# Create the redis cache for the proxy.
#

gcloud redis instances create ${REDIS_NAME} --size=${REDIS_SIZE_GB} --region=${REGION} --project=${PROJECT_ID}

#
# For app engine standard, we need to have a connector to talk to redis. If you are deciding to
# use AppEngine Flex, this is not needed. Change min, max instances ond machine type as desirec
#

if [ "${USING_AE_STANDARD}" = "TRUE" ]; then
  gcloud compute networks vpc-access connectors create ${VAC_NAME} \
       --region ${REGION} \
       --network default \
       --range 10.1.0.0/28 \
       --min-instances ${VPC_MIN_INSTANCES} \
       --max-instances ${VPC_MAX_INSTANCES} \
       --machine-type ${VPC_MACHINE_TYPE} \
       --project=${PROJECT_ID}
fi


#
# You will need the IP address for this to add to config.txt file
echo "Use this IP address for the REDIS Cache in config.txt:"
gcloud redis instances describe ${REDIS_NAME} --region=${REGION} --project=${PROJECT_ID} | grep "host"
