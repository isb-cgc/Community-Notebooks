import os
from flask import jsonify
from google.auth.transport.requests import Request
import json
import requests
from collab_queries import set_queries
from google.oauth2 import service_account
from google.auth import default


# set the env variable "credentials_file_needed" to true and env variable 'credentials_path'' to the file path containing the gcp credentials file
# if running locally


project_id = os.environ["PROJECT_ID"]
credentials_file_needed = ((os.environ["CREDENTIALS_FILE_NEEDED"]).lower() == "true")
if credentials_file_needed:
    credentials_file=os.environ['CREDENTIALS_FILE']
    credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=[
    'https://www.googleapis.com/auth/cloud-platform'])
else:
    credentials, _ = default()

# Endpoints and URLS for proxy and GCS BQ
job_url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/jobs"
pjob_path=f"/bqproxy/bigquery/v2/projects/{project_id}/jobs"
pjob_path_parts=len(pjob_path.split('/'))

query_url=f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/queries"
pquery_path=f"/bqproxy/bigquery/v2/projects/{project_id}/queries"
pquery_path_parts=len(pjob_path.split('/'))

# Job configuration template
job_config = {
    "configuration": {
        "query": {
            "query": "",
            "useLegacySql": False  # Use standard SQL
        }
    }
}




def submit_job(request):
    resp_data={"error":"unsuccessful"}
    credentials.refresh(Request())
    access_token = credentials.token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = request.get_json()
    if ('jobReference' in data):
        data['jobReference']['projectId']=project_id
    # Send the POST request
    if ('configuration' in data) and ('query' in data['configuration']) and ('queryParameters' in data['configuration']['query']):
        #erase whatever initial query is
        data['configuration']['query']['query'] = ''
        nparams = []
        for param in data['configuration']['query']['queryParameters']:
            # look for a queryid in the params and use that to set the sql
            if (param['name'] == "queryid") and (param['parameterValue']['value'] in set_queries):
                queryid=param['parameterValue']['value']
                data['configuration']['query']['query'] = set_queries[queryid]["sql"]
            else:
                nparams.append(param)
        if len(nparams) > 0:
            data['configuration']['query']['queryParameters'] = nparams
        else:
            del data['configuration']['query']['queryParameters']
        jdata = json.dumps(data)
        response = requests.post(job_url, headers=headers, data=jdata)
        resp_data=json.loads(response.content)

    return jsonify(resp_data)


def check_job(request,jobid):
    resp_data = {"error": "unsuccessful"}
    credentials.refresh(Request())
    access_token = credentials.token
    url=job_url+'/'+jobid
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    resp_data = json.loads(response.content)
    return jsonify(resp_data)


def get_results(request,jobid):
    resp_data = {"error": "unsuccessful"}
    credentials.refresh(Request())
    access_token = credentials.token
    url=query_url+'/'+jobid
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    resp_data = json.loads(response.content)
    return jsonify(resp_data)
