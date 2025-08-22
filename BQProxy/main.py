from flask import Flask, request
from bqroutes import pjob_path,  pquery_path, project_path
from bqroutes import submit_job, check_job, get_results, list_datasets, list_tables


app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def life_check():
    return "app is alive"

@app.route(pjob_path, methods=['POST'])
def flask_submit_job():
    return submit_job(request)


@app.route(pjob_path+'/'+'<path:jobid>', methods=['GET'])
def flask_check_job(jobid):
    return check_job(request,jobid)

@app.route(pquery_path+'/'+'<string:jobid>', methods=['GET'])
def flask_get_results(jobid):
    return get_results(request,jobid)

@app.route(project_path+'/'+'<string:projid>'+'/datasets', methods=['GET'])
def flask_list_datasets(projid):
    return list_datasets(request,projid)

@app.route(project_path+'/'+'<string:projid>'+'/datasets/'+'<string:dsetid>'+'/tables', methods=['GET'])
def flask_list_tables(projid,dsetid):
    return list_tables(request,projid,dsetid)


if __name__ == '__main__':
    app.run()
