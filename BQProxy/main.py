from flask import Flask, request
from bqroutes import pjob_path,  pquery_path
from bqroutes import submit_job, check_job, get_results


app = Flask(__name__)

@app.route(pjob_path, methods=['POST'])
def flask_submit_job():
    return submit_job(request)


@app.route(pjob_path+'/'+'<path:jobid>', methods=['GET'])
def flask_check_job(jobid):
    return check_job(request,jobid)

@app.route(pquery_path+'/'+'<string:jobid>', methods=['GET'])
def flask_get_results(jobid):
    return get_results(request,jobid)


if __name__ == '__main__':
    app.run()
