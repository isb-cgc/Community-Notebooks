if [ ! -f "${CIRCLE_WORKING_DIRECTORY}/deployment.key.json" ]; then
    echo ${DEPLOYMENT_KEY} | base64 --decode --ignore-garbage > ${CIRCLE_WORKING_DIRECTORY}/deployment.key.json
fi

gcloud auth activate-service-account --key-file ${CIRCLE_WORKING_DIRECTORY}/deployment.key.json
gcloud config set account $DEPLOYMENT_CLIENT_EMAIL
gcloud config set project "$DEPLOYMENT_PROJECT_ID"

echo "GCloud Config for Deployment:"
gcloud config list
