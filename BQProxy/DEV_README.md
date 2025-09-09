PROJECT_ID - the google project id billed for BigQuery usage through this service

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

REDIS_PORT - port for redis host