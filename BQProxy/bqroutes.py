import os
from flask import jsonify
from google.auth.transport.requests import Request
import json
import requests
from collab_queries import set_queries
from google.oauth2 import service_account
from google.auth import default
import redis
import uuid
import time


byte_to_gb = 1.0 * pow(10, -9)
# 24 hr in seconds
expiry_time_seconds= 24*60*60


has_daily_quota = ((os.environ["HAS_DAILY_QUOTA"]).lower() == "true")
daily_quota_gb = float(os.environ["DAILY_QUOTA_GB"])
query_quota_gb = float(os.environ["QUERY_QUOTA_GB"])
user_query_ok = ((os.environ["USER_QUERY_OK"]).lower() == "true")
redis_client=None

if has_daily_quota:
    daily_quota_gb = float(os.environ["DAILY_QUOTA_GB"])
    redis_host = os.environ["REDIS_HOST"]
    redis_port = os.environ["REDIS_PORT"]
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)


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


def safe_key_delete(ip):
    lockkey = ip + "_lock"
    lockval = str(uuid.uuid4())
    lock_aquired = False
    while not lock_acquired:
        lock_acquired = redis_client.set(lockkey, lockval, nx=True, ex=5)
        if lock_aquired:
            redis_client.delete(ip)
            redis_client.delete(lockkey)



# one key, which is the users ip, records total bytes processed via BigQuery per ip. Is deleted after 24 hours
# ip+"_"+jobid exists if the bytes processed for a jobid have already been counted. This has a short lifespan (2 min.).
# Safeguard against adding the bytes per job twice
# ip+"_lock" is used 'lock' the ip key and make sure one process updates the ip key at a time. This key is deleted after update.
# It has a 5 second lifespan to prevent blocking.
def update_daily_cache(resp_data,ip):
    update_needed = True
    cache_updated = None
    try:
        g_bytes = float(resp_data['statistics']['totalBytesProcessed']) * byte_to_gb
    except:
        g_bytes = 0.0

    # only update if g_bytes>0.
    if (g_bytes>0):
        lockkey=ip+"_lock"
        lockval = str(uuid.uuid4())
        lock_acquired = False
        while not lock_acquired and update_needed:
            # this succeeds unless another process created the lockkey. Expired (lock release after 5 seconds) in
            # which case the report for the query may not be recorded
            lock_acquired = redis_client.set(lockkey, lockval, nx=True, ex=5)
            if lock_acquired:
                jobid = resp_data['jobReference']['jobId']
                jobid_key = ip + "_" + jobid
                #make sure a previous BQ api call with this job id did not already add the bytes for this job
                if not redis_client.exists(jobid_key):
                    if redis_client.exists(ip):
                        redis_client.ttl(ip)
                        cur_g_bytes = float(redis_client.get(ip))
                        new_g_bytes = g_bytes+cur_g_bytes
                        redis_client.set(ip,new_g_bytes,keepttl=True)

                        # our key lock won't prevent the key from expiring. Key could expire between existence check
                        # and time we set it. In which case keepttl=True creates a permanent key!
                        # In that case redis_client.ttl(ip) returns -1
                        # We reset the key with only the bytes just processed. cur_g_bytes accumulated with the not expired key
                        if (redis_client.ttl(ip)==-1):
                            redis_client.set(ip, g_bytes, expiry_time_seconds)
                        cache_updated = True
                    else:
                        redis_client.set(ip, g_bytes, expiry_time_seconds)
                        cache_updated = True
                    redis_client.set(jobid_key, 'true', 120)
                # this jobid was handled already so break
                else:
                    update_needed = False
                    cache_updated = False
            #jobid needs to be added but another process has this ip key locked
            else:
                time.sleep(0.001)
            redis_client.delete(lockkey)
    return cache_updated


def check_query_format(query_req_data):
    format_ok = True
    is_user_query = False
    query_id=""
    err=""

    new_params=[]
    query_id_found=False
    query_id_confirmed = False

    if ('configuration' in query_req_data) and ('query' in query_req_data['configuration']):
        if ('queryParameters' in query_req_data['configuration']['query']):
            for param in query_req_data['configuration']['query']['queryParameters']:
                # look for a queryid in the params and use that to set the sql
                if (param['name'] == "queryid"):
                    query_id_found = True
                    is_user_query= False
                    if (param['parameterValue']['value'] in set_queries):
                        query_id=param['parameterValue']['value']
                        query_id_confirmed=True
                    else:
                        query_id_confirmed=False
                        break
                else:
                    new_params.append(param)

            # found an expected query id
            if query_id_found and query_id_confirmed:
                format_ok= True
                is_user_query = False
            # found an unexpected query id
            elif query_id_found and not query_id_confirmed:
                format_ok = False
                err = "unrecognized query id"
            # no query id but any query accepted
            elif not query_id_found and user_query_ok:
                format_ok = True
                is_user_query = True
            #no queryid provided and not allowing user queries
            else:
                format_ok= False
                err= "no query id provided, user defined queries are not allowed"

        #no queryParameters but user query ok
        elif user_query_ok:
            format_ok = True
            is_user_query = True
        # no queryParameters and user query disallowed
        else:
            format_ok= False
            err= "no query id provided, user defined queries are not allowed"
    else:
        format_ok=False
        err = 'missing configuration and/or query data'

    return ([format_ok, is_user_query, query_id, err, new_params])

def check_quotas(dry_response,user_ip):
    quotas_ok = True
    quota_err = False
    error_message = ""
    g_bytes= float(dry_response['statistics']['totalBytesProcessed'])*byte_to_gb
    if (g_bytes<query_quota_gb):
        if has_daily_quota:
            if redis_client.exists(user_ip):
                val = float(redis_client.get(user_ip))
                key_expiry_seconds = redis_client.ttl(user_ip)

                key_expiry_hours = float(key_expiry_seconds)/(60.0*60.0)
                #key_expiry_seconds==2 means that the key was just expired since we did the key existence check
                if ((val+g_bytes) < daily_quota_gb) or (key_expiry_seconds==2):
                    quotas_ok = True
                #key_expiry_seconds==1 means a cache update died at the right time and conditions to create a permanent key.
                # This might be near impossible in practice?
                elif (key_expiry_seconds==1):
                    safe_key_delete(user_ip)
                else:
                    quotas_ok = False
                    error_message = '''You cannot run this query as your daily limit using the demo mode may be exceeded with this request. 
                    You have a limit of {q} GB of data processing using the BigQuery demo mode per day. You have already used {u} GB. This query may use {b} GB. 
                    Your daily limit will be reset in {h} hours'''.format(q=daily_quota_gb, u= val, b=g_bytes, h=key_expiry_hours)
            else:
                quotas_ok = True
        else:
            quotas_ok= True

    else:
        quotas_ok = False
        error_message = '''You cannaot run this as tha maximum query limit in the demo mode may be exceeded by this request. " \
                        In demo mode you have a single query limit of {lim} GB of BigQuery data processing. 
                        This query is estimated to require up to {b} GB'''.format(lim=query_quota_gb, b=g_bytes)

    return([quotas_ok,error_message])


def submit_job(request):
    user_ip=request.remote_addr
    dry_run_req =False
    orig_jobReference = None
    response_code=200
    resp_data={"error":"cannot parse request"}
    credentials.refresh(Request())
    access_token = credentials.token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = request.get_json()
    #send in the project_id expected by bigquery.
    if ('jobReference' in data) and ('projectId' in data['jobReference']):
        data['jobReference']['projectId']=project_id
    [format_ok, is_user_query, query_id, err, new_params] = check_query_format(data)
    if format_ok:
        # replace any provided query with that indicated by the query id
        if not is_user_query:
            data['configuration']['query']['query'] = set_queries[query_id]["sql"]
            if len(new_params) > 0:
                data['configuration']['query']['queryParameters'] = new_params
            else:
                del data['configuration']['query']['queryParameters']
        data['configuration']['dry_run'] = True
        data['configuration']['query']['useQueryCache'] = False


        #save original jobRefernce for actual run. make a new jobid for dry run
        if not dry_run_req:
            if 'jobReference' in data:
                orig_jobReference ={}
                for key in data['jobReference']:
                    orig_jobReference[key]=data['jobReference'][key]
                if ('jobId' in  data['jobReference']):
                    data['jobReference']['jobId']=str(uuid.uuid4())

        jdata = json.dumps(data)
        dry_response = requests.post(job_url, headers=headers, data=jdata)

        # if the user requested a dry run or dry run errors, stop and send dry run response to user
        if dry_run_req or not (dry_response.status_code==200):
            resp_data = json.loads(dry_response.content)
            response_code = dry_response.status_code
            #response_code = 200
        else:
            [quotas_ok, err] = check_quotas(json.loads(dry_response.content), user_ip)
            if quotas_ok:
                del (data['configuration']['dry_run'])
                data['configuration']['query']['useQueryCache'] = True
                if (orig_jobReference is not None):
                    data['jobReference'] = orig_jobReference
                jdata = json.dumps(data)
                response = requests.post(job_url, headers=headers, data=jdata)
                resp_data = json.loads(response.content)
                response_code = response.status_code
                if has_daily_quota and ('status' in resp_data) and ('state' in resp_data['status']) and (resp_data['status']['state']=='DONE'):
                    update_daily_cache(resp_data, user_ip)
            else:
                resp_data = {"error":{"code":400, "message":err}}
                response_code = 400
    else:
        resp_data = {"error":{"code":400, "message":err}}
        response_code = 400

    return jsonify(resp_data), response_code


def check_job(request,jobid):
    user_ip = request.remote_addr
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
    if has_daily_quota and ('status' in resp_data) and ('state' in resp_data['status']) and (
            resp_data['status']['state'] == 'DONE'):
        update_daily_cache(resp_data, user_ip)
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
