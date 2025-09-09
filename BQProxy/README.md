A service that allows ISB-CGC users to run the bigquery statements in the COLLAB notebooks without using a billable account. 
They do this by running the Notebooks in a 'demo mode' in which the normal BigQuery endpoint is replaced by an endpoint for this service. 
This service restricts access to only queries used in the notebooks, as specified in collab_queries.py. 
See "How_to_make_a_heatmap_using_BigQuery.ipynb" for a demonstration.
