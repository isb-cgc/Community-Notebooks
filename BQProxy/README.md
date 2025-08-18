A service that allows ISB-CGC users to run the bigquery statements in the COLLAB notebooks without using a billable account. 
They do this by running the Notebooks in a 'demo mode' in which the normal BigQuery endpoint is replaced by an endpoint for this service. 
This service can be deployed to provide the user full access to bigquery,
or to restrict access to only queries used in the notebooks, as specified in collab_queries.py. 
See "How_to_make_a_heatmap_using_BigQuery.ipynb" for a demonstration


The service is configured by the following environmental variables:

PROJECT_ID- the google project id billed for BigQuery usage through this service
CREDENTIALS_FILE_NEEDED - a string ("true" or "false") declaring if a credentials file 
needs to be read to acquire google authentication. Generally "false" if running via the Google app engine
CREDENTIALS_FILE - full path for the optional credentials file
QUERY_QUOTA_GB - float, maximum # of GB that can be processed in one query. The service always does a 'dry run' of a query
with the query cache set to false to check the estimated # of GB that may be processed. A query is only allowed 
if it does not exceed this limit
HAS_DAILY_QUOTA - a string ("true" or "false") that indicates if we have a daily limit on
the # of gb a user can process in a day. If set to "true" new query requests are checked against 
the user's daily limit via a dry run of the query. As we have no user accounts, users are only 
identified by IP. 
DAILY_QUOTA_GB - float that gives the maximum # of GB a user can process in a day if HAS_DAILY_QUOTA is true
REDIS_HOST - IP of redis host that tracks the daily # of GB processed per day per IP, using keys that expire in 24hr. 
This is only provisioned when a daily quota is tracked
REDIS_PORT - port for above mentioned redis host
USER_QUERY_OK -a string ("true" or "false") that determines whether any user query will be sent to BigQuery or 
only predetermined queries (possible with parameters) specified in the collab_queries.py file. Besides the processing limit,
if USER_QUERY_OK is set to "true", this service DOES NOT in any way restrict the queries being sent to BigQuery. To my knowledge 
there does not exist a straightforward and guaranteed way to examine a query and determine which datasets are involved, 
whether the query is strictly reading or writing data etc. A query 'dry run' does not provide such information. 
If USER_QUERY_OK is set to true, the GOOGLE CREDENTIALS should be set to provide minimum allowed access.