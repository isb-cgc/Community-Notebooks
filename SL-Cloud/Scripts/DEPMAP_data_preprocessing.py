import sys
import numpy as np
import pandas as pd
from google.cloud import bigquery
import pandas_gbq as gbq

def shRNAPreprocess(input_data, col_name):
    '''
    Description:Preprocesses DEPMAP DEMETER2 data and converts into it long format
    Inputs:
        input_data: dataframe,either gene expression, cnv or gene effect
        col_name: string, the colunm name  for measurements e.g CNA
    Output:
        long_table: dataframe, long format of the input data given in wide format
    '''

    data=input_data.copy(deep=False)
    data=pd.DataFrame.transpose(data)
    id='CCLE_ID'
    long_table=CRISPRPreprocess(data, col_name, id)
    return(long_table)

def CRISPRPreprocess(input_data, col_name, id='DepMap_ID'):
    '''
    Description:Preprocesses DEPMAP CRISPR data and converts into into long format
    Inputs:
       input_data: dataframe,either gene expression, cnv or gene effect
       col_name: string, the colunm name  for measurements e.g CNA
    Output:
        long_table: dataframe, long format of the input data given in wide format
    
    '''

    data=input_data.copy(deep=False)
    gene_names= [colname.split(' (')[0] for colname in data.columns]
    entrez_ids= [(colname.split('(', 1)[1].split(')')[0]) for colname in data.columns]

    if 'NA' in entrez_ids:
        index_rem_list = [ i for i in range(len(entrez_ids)) if entrez_ids[i] == 'NA' ]
        for index in sorted(index_rem_list, reverse=True):
            del entrez_ids[index]
            del gene_names[index]
        data.drop(data.columns[index_rem_list], axis=1, inplace=True)
    if 'nan' in entrez_ids:
        index_rem_list = [ i for i in range(len(entrez_ids)) if entrez_ids[i] == 'nan' ]
        for index in sorted(index_rem_list, reverse=True):
            del entrez_ids[index]
            del gene_names[index]
        data.drop(data.columns[index_rem_list], axis=1, inplace=True)

    gene_entrez_map=dict(zip(gene_names, entrez_ids))
    data.columns=gene_names
    long_table = data.unstack().reset_index()
    long_table = long_table.set_axis(['Hugo_Symbol', id, col_name], axis=1, inplace=False)
    long_table['Entrez_ID']=[gene_entrez_map.get(x) for x in long_table['Hugo_Symbol']]
  # long_table['Entrez_ID']= pd.to_numeric(long_table['Entrez_ID'])

    long_table=long_table[['Entrez_ID','Hugo_Symbol',id, col_name]]
    return(long_table)
