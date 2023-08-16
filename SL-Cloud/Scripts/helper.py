
from google.cloud import bigquery
import pandas as pd

def ConvertGene(client, input_vector, input_type, output_type):
    '''
    Description: This function provides conversion between EntrezID, Gene and Alias
    Inputs:
        client:BigQueryClient, the Bigquery client that will do the operation
        input_vector:list of integers or  strings (depending on the input)	
        input_type: string,  valid values: 'Alias', 'Gene', 'EntrezID'
        output_type:list of strings,  output type must a vector like ['Gene', 'EntrezID']
    '''
    sql='''
    SELECT DISTINCT __IN_TYPE__,  __OUT_TYPE__
   
    FROM  `isb-cgc-bq.annotations.gene_info_human_NCBI_current`
    where  __IN_TYPE__  in (__IN_VECTOR__)
    '''

    if input_type=='EntrezID':
        intermediate_representation = [str(x) for x in input_vector]
    else:
        intermediate_representation = ["'"+str(x)+"'" for x in input_vector]

    input_vector_query= ','.join(intermediate_representation)

    out_type_intermediate_representation = [str(x) for x in output_type]
    output_type_for_query= ','.join(out_type_intermediate_representation)

    sql=sql.replace('__OUT_TYPE__', output_type_for_query)
    sql=sql.replace('__IN_TYPE__', input_type)
    sql=sql.replace('__IN_VECTOR__', input_vector_query)

    result= client.query(sql).result().to_dataframe()
    return(result)


def WriteToExcel(excel_file, data_to_write, excel_tab_names):
    '''
    Description: This function writes the dataframes whose names are given
    in data_to-write parameter to the excel files whose names
    given in excel_file_names parameter
    Inputs:
       excel_file:string, the name of the excel file that the data will be written into. 
       data_to_write:list of dataframes, the dataframes that will be written into the tabs of the excel file
       excel_tab_names:list of strings, the tab names of the excel file, in the same order with the dataframes that will be written.
    
    '''
    with pd.ExcelWriter(excel_file) as writer:
        for i in range(len(excel_tab_names)):
            data_to_write[i].to_excel(writer, sheet_name=excel_tab_names[i], index=False)

