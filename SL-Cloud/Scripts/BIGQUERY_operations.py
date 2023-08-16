
import sys
import numpy as np
import pandas as pd
from google.cloud import bigquery
import pandas_gbq as gbq

def CreateDataSet(client, dataset_name, project_id, dataset_description):

    '''
    Description:This function creates a dataset named dataset_name into the project given
    project_id, with the data_description provided,if it does not already exist, if it exists it returns a message 
    Inputs:
        client:BigQueryClient, the Bigquery client that will create the dataset
        dataset_name:string, the name of dataset that will be created
        project_id:string, the project that the dataset will be created in.
        dataset_description:string, the description of the dataset
    '''

    dataset_id = client.dataset(dataset_name, project=project_id)
    try:
        dataset=client.get_dataset(dataset_id)
        print('Dataset {} already exists.'.format(dataset.dataset_id))
    except:
        dataset = bigquery.Dataset(dataset_id)
        dataset = client.create_dataset(dataset)
        dataset.description =dataset_description
        dataset = client.update_dataset(dataset, ["description"])
        print('Dataset {} created.'.format(dataset.dataset_id))



def CreateTable(client, data, dataset_name, table_name, project_id, table_desc, table_annotation=None):
    '''
     Description: This function creates a dataset named dataset_name into the project given
     project_id, with the data_description provided, it overwrites if a table exists with the same name
     Inputs:
         client:BigQueryClient, the Bigquery client that will create the dataset
         data:dataframe, the data that will be saved in the BigQuery table
         dataset_name:string, the dataset where the table will be saved into 
         table_name:string, the name of table that will be created
         project_id:string, the project that the dataset will be saved.
         table_desc:string, the description of the table
         table_annotation:dictionary, the dictionary of table column names and their annotations.
    '''

    dataset_id = client.dataset(dataset_name, project=project_id)
    try:
        dataset=client.get_dataset(dataset_id)
        if table_annotation is None:
            gbq.to_gbq(data, dataset.dataset_id +'.'+ table_name, project_id=project_id, if_exists='replace')

        else:
            gbq.to_gbq(data, dataset.dataset_id +'.'+ table_name, project_id=project_id, table_schema = table_annotation , if_exists='replace')
        print("Table created successfully")

    except:
        print('Table could not be created')
    try:
        table=client.get_table(dataset.dataset_id +'.'+ table_name)
        table.description =table_desc
        table = client.update_table(table, ["description"])
        #print("Table description added successfully")
    except:
        print('Table description could not be updated')
