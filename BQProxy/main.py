import logging
import os
from flask import Flask, request, jsonify
from flask_talisman import Talisman
from bqroutes import pjob_path, pquery_path
from bqroutes import submit_job, check_job, get_results

IS_APP_ENGINE = os.environ.get("IS_APP_ENGINE", "false").lower() == 'true'

if IS_APP_ENGINE:
    import google.cloud.logging
    client = google.cloud.logging_v2.Client()
    client.setup_logging()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
if IS_APP_ENGINE:
    Talisman(app, strict_transport_security_max_age=300, content_security_policy={
        'default-src': [
            '\'self\'',
            '*.googleapis.com',
            '*.swagger.io',
            '\'unsafe-inline\'',
            'data:'
        ]
    })


@app.route(pjob_path, methods=['POST'])
def flask_submit_job():
    return submit_job(request)


@app.route(pjob_path+'/'+'<path:jobid>', methods=['GET'])
def flask_check_job(jobid):
    return check_job(request, jobid)


@app.route(pquery_path+'/'+'<string:jobid>', methods=['GET'])
def flask_get_results(jobid):
    return get_results(request, jobid)


# Error handlers
@app.errorhandler(500)
def unexpected_error(e):
    """Handle exceptions by returning swagger-compliant json."""
    logger.error('[ERROR] An error occurred while processing the request:')
    logger.exception(e)
    response = jsonify({
        'code': 500,
        'message': 'Exception: {}'.format(e)
    })
    response.status_code = 500
    return response


if __name__ == '__main__':
    app.run()
