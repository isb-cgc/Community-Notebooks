from google.cloud import bigquery
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.stats import mstats
import ipywidgets as widgets
from   ipywidgets import Layout

def bqtable_data_cptac( MolecularFeature , study ) :
    
    study2site = { 'CCRCC' : 'Kidney',
                     'GBM' : 'Brain',
                   'HNSCC' : 'Other and ill-defined sites',
                    'LSCC' : 'Bronchus and lung',
                    'LUAD' : 'Bronchus and lung',
                     'PDA' : 'Pancreas',
                    'UCEC' : 'Uterus, NOS',
               'breast_BI' : 'Breast'}

    cptac_tables = { 'Gene Expression' : { 'CCRCC' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'GBM' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'HNSCC' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'LSCC' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'LUAD' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'PDA' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'UCEC' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                           'breast_BI' : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current'},
                     'Protein Expression' : { 'CCRCC' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_CCRCC_discovery_study_pdc_current',
                                              'GBM' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_GBM_discovery_study_pdc_current',
                                              'HNSCC' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_HNSCC_discovery_study_pdc_current',
                                              'LSCC' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_LSCC_discovery_study_pdc_current',
                                              'LUAD' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_LUAD_discovery_study_pdc_current',
                                              'PDA' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_PDA_discovery_study_pdc_current',
                                              'UCEC' : 'isb-cgc-bq.CPTAC.quant_proteome_CPTAC_UCEC_discovery_study_pdc_current',
                                              'breast_BI' : 'isb-cgc-bq.CPTAC.quant_proteome_prospective_breast_BI_pdc_current'}
                   }
    
    mytable = cptac_tables[MolecularFeature][study]
    
    Features = { 'Gene Expression' : { 'table'  : 'isb-cgc-bq.CPTAC.RNAseq_hg38_gdc_current',
                                       'symbol' : 'gene_name',
                                       'study'  : '',
                                       'data'   : 'AVG( LOG10(fpkm_unstranded + 1) ) ',
                                       'rnkdata': '(RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) - 1)/2.0',
                                 'metasampleid' : 'sample_submitter_id',  
                                   'patientcode': 'case_submitter_id',
                                    'samplecode': 'sample_barcode',
                                       'where'  : 'AND fpkm_unstranded IS NOT NULL AND t2.sample_type = \'Primary Tumor\'',
                                       'dattype': 'numeric' },
                'Protein Expression' : {'table' : 'NULL',
                                        'symbol' : 'gene_symbol',
                                        'study'  : '',
                                        'data'   : 'AVG( protein_abundance_log2ratio ) ',
                                        'rnkdata': '(RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) - 1)/2.0',
                                  'metasampleid' : 'aliquot_id',  
                                   'patientcode': 'case_submitter_id',
                                    'samplecode': 'aliquot_id',
                                       'where'  : 'AND protein_abundance_log2ratio IS NOT NULL AND t2.sample_type = \'Primary Tumor\' ',
                                       'dattype': 'numeric' },
                                        
               }
      
    feature = Features[MolecularFeature]
    feature['table'] = mytable 
    
    if ( MolecularFeature == 'Gene Expression' ) :
        feature['where'] = feature['where'] + ' AND t1.primary_site=\''+ study2site[study]  +'\''  
        
    return feature
    
    
def bqtable_data( MolecularFeature  ) :

    Features = { 'Gene Expression' : { 'table'  : 'pancancer-atlas.Filtered.EBpp_AdjustPANCAN_IlluminaHiSeq_RNASeqV2_genExp_filtered',
                                       'symbol' : 'Symbol',
                                       'study'  : 'Study',
                                       'data'   : 'AVG( LOG10( normalized_count + 1 ) ) ',
                                       'rnkdata': '(RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) - 1)/2.0',
                                       'avgdat' : 'avgdata',  
                                   'patientcode': 'ParticipantBarcode',
                                    'samplecode': 'SampleBarcode',
                                       'where'  : 'AND normalized_count IS NOT NULL',
                                       'dattype': 'numeric' },
               'Somatic Copy Number': {'table': 'pancancer-atlas.Filtered.all_CNVR_data_by_gene_filtered',
                                       'symbol' : 'Gene_Symbol',
                                       'study'  : 'Study',
                                       'data'   : 'AVG(GISTIC_Calls)',
                                       'rnkdata': '(RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) - 1)/2.0',
                                       'avgdat' : 'avgdata',  
                                   'patientcode': 'ParticipantBarcode',
                                    'samplecode': 'SampleBarcode',
                                       'where'  : 'AND GISTIC_Calls IS NOT NULL',
                                       'dattype': 'numeric'},
          'Somatic Mutation t-test': { 'table'  : 'pancancer-atlas.Filtered.MC3_MAF_V5_one_per_tumor_sample',
                                       'symbol' : 'Hugo_Symbol',
                                        'study' : 'Study', 
                                       'data'   : '#',
                                       'rnkdata': '#',
                                       'avgdat' : '#',  
                                   'patientcode': 'ParticipantBarcode',
                                    'samplecode': 'Tumor_SampleBarcode',
                                       'where'  : 'AND FILTER = \'PASS\'',
                                       'dattype': 'boolean'},
                 'Somatic Mutation': { 'table'  : 'pancancer-atlas.Filtered.MC3_MAF_V5_one_per_tumor_sample',
                                       'symbol' : 'Hugo_Symbol',
                                        'study' : 'Study',
                                       'data'   : '#',
                                       'rnkdata': '#',
                                       'avgdat' : '#',  
                                   'patientcode': 'ParticipantBarcode',
                                    'samplecode': 'Tumor_SampleBarcode',
                                       'where'  : 'AND FILTER = \'PASS\'',
                                       'dattype': 'boolean'},      
                 'Clinical Numeric': { 'table'  : 'pancancer-atlas.Filtered.clinical_PANCAN_patient_with_followup_filtered',
                                       'symbol' : '\'COLUMN_NAME\'',
                                        'study' : 'acronym',
                                       'data'   : 'COLUMN_NAME',
                                       'rnkdata': '(RANK() OVER (PARTITION BY table_columns.symbol ORDER BY table_columns.data ASC)) + (COUNT(*) OVER ( PARTITION BY table_columns.symbol, CAST(table_columns.data as STRING)) - 1)/2.0',
                                       'avgdat' : 'avgdata',
                                   'patientcode': 'bcr_patient_barcode',
                                    'samplecode': '',
                                       'where'  : '',
                                       'dattype': 'numeric'},
            'Clinical Categorical': {  'table'  : 'pancancer-atlas.Filtered.clinical_PANCAN_patient_with_followup_filtered',
                                       'symbol' : '\'COLUMN_NAME\'',
                                        'study' : 'acronym',
                                       'data'   : 'COLUMN_NAME',
                                       'rnkdata': 'table_columns.data',
                                       'avgdat' : 'avgdata',
                                   'patientcode': 'bcr_patient_barcode',
                                    'samplecode': '',
                                       'where'  : 'AND NOT REGEXP_CONTAINS(table_columns.data,r"^(\[.*\]$)")',
                                       'dattype': 'categorical'},
             'MicroRNA Expression': {  'table'  : 'pancancer-atlas.Filtered.pancanMiRs_EBadjOnProtocolPlatformWithoutRepsWithUnCorrectMiRs_08_04_16_filtered',
                                       'symbol' : 'ID',
                                        'study' : 'Study',
                                       'data'   : 'AVG( miRNAexpr )',
                                       'rnkdata': '(RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) - 1)/2.0',
                                       'avgdat' : 'avgdata',
                                   'patientcode': 'ParticipantBarcode',
                                    'samplecode': 'SampleBarcode',
                                       'where'  : 'AND miRNAexpr IS NOT NULL AND Corrected = \'Corrected\'',
                                       'dattype': 'numeric'}
                
               }

    feature = Features[MolecularFeature]
    return feature      

    

    
def numeric_bqtable_cptac ( tablename, feat, labels ) :
    
    mytable = "\n" + tablename + \
""" AS (
SELECT
   symbol,
   {0} AS rnkdata,
   ParticipantBarcode
FROM (
   SELECT
      t1.{1} AS symbol, 
      {2} AS data,
      t2.{3} AS ParticipantBarcode
   FROM `{4}` t1
   JOIN `isb-cgc-bq.PDC_metadata.aliquot_to_case_mapping_current` as t2
   ON  t1.{6} = t2.{7}   # cohort 
         AND {1} {8}  # labels 
         {5}  
   GROUP BY
      ParticipantBarcode, symbol
   )
)
"""
    table_query= mytable.format(feat['rnkdata'],feat['symbol'],feat['data'],feat['patientcode'],feat['table'],feat['where'],\
                                feat['samplecode'], feat['metasampleid'], labels )

    return  table_query


def generic_numeric_bqtable ( tablename, feat , cohort, labels ) :
    
    mytable = "\n" + tablename + \
""" AS (
SELECT
   symbol,
   {0} AS rnkdata,
   ParticipantBarcode
FROM (
   SELECT
      {1} AS symbol, 
      {2} AS data,
      {3} AS ParticipantBarcode
   FROM `{4}`
   WHERE {6}    # cohort 
         AND {1} {7}  # labels 
         {5}  
   GROUP BY
      ParticipantBarcode, symbol
   )
)
"""
    table_query= mytable.format(feat['rnkdata'],feat['symbol'],feat['data'],feat['patientcode'],feat['table'],feat['where'],\
                                cohort, labels )

    return  table_query

def generic_clinical_bqtable ( tablename, feat, cohort, struct_columns ) :
        
    mytable = "\n" + tablename + \
""" AS (
SELECT
  ParticipantBarcode,
  {0} as rnkdata,
  table_columns.symbol as symbol
FROM (
  SELECT
    {1} as ParticipantBarcode,
    [
"""+ ",\n".join( struct_columns ) + """ 
    ] AS table_columns
  FROM
    `{2}`
  WHERE
     {3}
  )  AS newtable 
CROSS JOIN 
  UNNEST( newtable.table_columns ) AS  table_columns
WHERE 
  table_columns.data IS NOT NULL {4}
)              
"""
    table_query = mytable.format(feat['rnkdata'],feat['patientcode'],feat['table'], cohort, feat['where'] )
    return table_query
    

def get_feature_tables( project, study, feature1, feature2, samplelist, patientlist, labellist ) :

    if ( project == 'TCGA' ) :
        feat1 =  bqtable_data( feature1 )
        feat2 =  bqtable_data( feature2 )
    
        # code to handle a user defined cohort list
        cohort1 = feat1['study'] + " = \'" + study + "\'"
        cohort2 = feat2['study'] + " = \'" + study + "\'"
    
        # Clinical features
        struct_columns = []
        if ( feature1.startswith('Clinical') or feature2.startswith('Clinical') ) :
             struct_columns = clinical_features( 'Clinical Categorical' ) 
        
        # generate table 1:
        table1 = ''
        if ( feature1.startswith('Clinical') ) :
            temp_structs =   find_clinical_features( struct_columns, labellist )
            table1 = generic_clinical_bqtable ( 'table1' , feat1, cohort1, temp_structs )
        
        elif ( feat1['dattype'] == 'numeric' ) :
            table1 = generic_numeric_bqtable ( 'table1', feat1, cohort1,  'IN UNNEST(@GENELIST)' )  
    

        # generate table 2:            
        table2 = ''
        if ( feature2.startswith('Clinical') ) :
            table2 = generic_clinical_bqtable ( 'table2', feat2, cohort2, struct_columns )
        
        elif ( (feat2['dattype'] == 'numeric') or (feat2['dattype'] == 'boolean') ) :
            table2 = generic_numeric_bqtable ( 'table2', feat2, cohort2, 'IS NOT NULL' )    

    elif (project == 'CPTAC' ) :
        feat1 = bqtable_data_cptac( feature1, study )
        feat2 = bqtable_data_cptac( feature2, study )
        
        # generate table 1:
        table1 = ''
        if ( feat1['dattype'] == 'numeric' ) :
            table1 = numeric_bqtable_cptac( 'table1', feat1,  'IN UNNEST(@GENELIST)' )  
    

        # generate table 2:            
        table2 = ''
        if ( feat2['dattype'] == 'numeric'  ) :
            table2 = numeric_bqtable_cptac ( 'table2', feat2,  'IS NOT NULL' )    

        
        
    return table1, table2

def runQuery ( client, qString, GeneList, SampleList, PatientList, dryRun=False ):
#  """
#**`runQuery`**: a relatively generic BigQuery query-execution wrapper function which can be used to run a query in "dry-run"  mode or not:  the call to the `query()` function itself is inside a `try/except` block and if it fails we return `None`;  otherwise a "dry" will return an empty dataframe, and a "live" run will return the query results as a dataframe. This function was modify from previous notebooks to handle user-defined parameteres necessary for the purpose of this notbeook.
#  """
  
  print ( "\n in runQuery ... " )
  if ( dryRun ):
    print ( "    dry-run only " )
    
  ## set up QueryJobConfig object
  job_config = bigquery.QueryJobConfig()
    
  query_params = [
        bigquery.ArrayQueryParameter('GENELIST', 'STRING', GeneList ),
        bigquery.ArrayQueryParameter('SAMPLELIST', 'STRING', SampleList ),
        bigquery.ArrayQueryParameter('PATIENTLIST', 'STRING', PatientList ),
  ]
  job_config.query_parameters = query_params
     
  job_config.dry_run = dryRun
  job_config.use_query_cache = True
  job_config.use_legacy_sql = False
  
  ## run the query
  try:
    query_job = client.query ( qString, job_config=job_config )
    ## print ( "    query job state: ", query_job.state )
  except:
    print ( "  FATAL ERROR: query execution failed " )
    return ( None )
  
  ## return results as a dataframe (or an empty dataframe for a dry-run) 
  if ( not dryRun ):
    try:
      df = query_job.to_dataframe()
      if ( query_job.total_bytes_processed==0 ):
        print ( "    the results for this query were previously cached " )
      else:
        print ( "    this query processed {} bytes ".format(query_job.total_bytes_processed) )
        jobTimeLine = query_job.timeline
        elapsed = 0 
        for entry in jobTimeLine :
            elapsed = int( entry.elapsed_ms  )
            #print( entry.elapsed_ms)
        print ( "    Approx. elpased time : {} miliseconds ".format( elapsed ) )
            
      if ( len(df) < 1 ):
        print ( "  WARNING: this query returned NO results ")
      return ( df )
    except:
      print ( "  FATAL ERROR: query execution failed " )
      return ( None )
    
  else:
    print ( "    if not cached, this query will process {} bytes ".format(query_job.total_bytes_processed) )
    ## return an empty dataframe
    return ( pd.DataFrame() )



# This function is used to 1) unpivot the columns to rows, 
# and 2) to clean the data (cast string to numeric) for the computation of correlation coefficients
def  clinical_features( clinical_feature_name ) :
    
    feat =  bqtable_data( clinical_feature_name ) 
    table_ref = feat['table']
    
    client = bigquery.Client()
    table = client.get_table(table_ref)
  
    fieldNames = list(map(lambda tsf: tsf.name, table.schema))
    fieldTypes = list(map(lambda tsf: tsf.field_type, table.schema))
    Ncolumns = len(fieldNames) 
    
    struct_columns = []

    for i in range(Ncolumns)  :
        iName = fieldNames[i] 
        iType = fieldTypes[i] 
        
        if (  iName in ['bcr_patient_uuid', 'bcr_patient_barcode', 'acronym', 'patient_id' ] ):
            continue 
                
        if ( feat['dattype'] == 'categorical')    :
            if ( iType == 'STRING') : 
                struct = '     STRUCT(\''+ iName +'\' AS symbol, '+ iName +' AS data)'
                struct_columns.append( struct )
        
        elif ( ( feat['dattype'] == 'numeric' ) and ( iType == 'STRING') ) :           
            struct = '     STRUCT(\''+ iName +'\' AS symbol, IF( REGEXP_CONTAINS('+ iName +' ,r"^\d*\.?\d*$"), CAST(' + iName + ' AS NUMERIC), null) AS data)'
            struct_columns.append( struct )
                        
        elif ( ( feat['dattype'] == 'numeric') and ( iType == 'FLOAT'  or  iType == 'INTEGER' )  ) :
            struct = '     STRUCT(\''+ iName +'\' AS symbol, '+ iName +' AS data)'
            struct_columns.append( struct )
                
    return struct_columns 

def find_clinical_features( struct_columns, labellist ) :
    struct_list = []
    
    for mylabel in labellist: 
        for mystruct in struct_columns :
            mystring  = 'STRUCT(\''+ mylabel.strip()  +'\' AS symbol'
            
            if  ( mystruct.find( mystring ) != -1 ) :
                struct_list.append( mystruct )
                break
    
    if ( struct_list == [] ) :
        raise RuntimeError("Feature1 labels not found ..... ")
       
    return struct_list    

def get_summarized_table(project, feature1_name, feature2_name, study ) :
    if ( project == 'TCGA') :
    
        ft1 = bqtable_data(feature1_name )
        ft2 = bqtable_data(feature2_name )
    
    elif ( project == 'CPTAC' ):
        ft1 = bqtable_data_cptac( feature1_name, study )
        ft2 = bqtable_data_cptac( feature2_name, study )
        
    return get_summarized_query( feature1_name, ft1, feature2_name, ft2 ) 
               
def get_summarized_query( feature1_name, ft1, feature2_name, ft2 ) :
    
    
    if ( ft2['dattype']  == 'numeric' ): 
        statistics = """COUNT( n1.ParticipantBarcode ) as n,
   CORR(n1.rnkdata , n2.rnkdata) as correlation
    """
    elif (  ft2['dattype']  == 'boolean') :
        
        data = 'data' 
        if ( feature2_name == 'Somatic Mutation' ):
            data = 'rnkdata'
            
        statistics = """COUNT( n1.ParticipantBarcode) as n_1,
   SUM( n1.{0} )  as sumx_1,
   SUM( n1.{0} * n1.{0} ) as sumx2_1
   """.format(data)
        
    elif (  ft2['dattype'] == 'categorical') :
        statistics = """n2.rnkdata as category, 
   COUNT( n1.ParticipantBarcode) as n,
   SUM( n1.data )  as sumx,
   SUM( n1.data * n1.data ) as sumx2
   """
    else : statistics = ''
    
    
    temp_table="""
SELECT 
   n1.symbol as symbol1,
   n2.symbol as symbol2,
   {0}
FROM
   table1 AS n1
INNER JOIN
   {2} AS n2
ON
   n1.ParticipantBarcode = n2.ParticipantBarcode
   {1}
GROUP BY
   symbol1, symbol2"""

    if (  ft2['dattype'] == 'categorical') : 
        temp_table = temp_table + ', category\n'
    else :
        temp_table = temp_table + '\n'
    
    
    # this is done to handle repetitive pairs
    str_rm_input = '' 
    input_pairs_table = ''
    if ( feature1_name == feature2_name ):
        str_rm_input = 'AND n2.symbol NOT IN UNNEST(@GENELIST)'
        input_pairs_table = 'UNION ALL' + temp_table.format(statistics,'AND n1.symbol < n2.symbol','table1')  
           
    
    summ_table = temp_table.format( statistics, str_rm_input,  'table2' )  
    sql_str = "\nsumm_table AS (" + summ_table + input_pairs_table + ")" 
               
   
    return sql_str

def get_stat_table( project, study, feat_name1, feat_name2, nsamples, alpha ) :
    
    if ( project == 'TCGA') :
        feat1 = bqtable_data(feat_name1 )
        feat2 = bqtable_data(feat_name2 )
    elif( project == 'CPTAC') :
        feat1 = bqtable_data_cptac( feat_name1, study )
        feat2 = bqtable_data_cptac( feat_name2, study )

    return get_stat_query( feat_name1, feat1, feat_name2, feat2, nsamples, alpha )

def get_stat_query( feat_name1, feat1, feat_name2, feat2, nsamples, alpha ) :
  
    stat_table = '' 
    
    if ( feat1['dattype'] == 'numeric' and feat2['dattype'] == 'numeric'  )  :
        
        stat_table = """
SELECT symbol1, symbol2, n, correlation,
    `isb-cgc-bq.functions.corr_pvalue_current`(correlation, n) AS p_value
FROM summ_table
WHERE 
    n > {0} 
GROUP BY 1,2,3,4
HAVING  p_value <= {1}
ORDER BY ABS(correlation) DESC
""".format( str(nsamples) , alpha )
        
    elif ( feat1['dattype'] == 'numeric' and feat_name2 == 'Somatic Mutation t-test'  ) :
        stat_table = """
SELECT 
    symbol1, symbol2,
    n_1, n_0,
    avg1, avg0,
    ABS(avg1 - avg0)/ SQRT( var1 /n_1 + var0/n_0 )  as tscore
FROM (
SELECT symbol1, symbol2, n_1, 
       sumx_1 / n_1 as avg1,
       ( sumx2_1 - sumx_1*sumx_1/n_1 )/(n_1 -1) as var1, 
       n_t - n_1 as n_0,
       (sumx_t - sumx_1)/(n_t - n_1) as avg0,
       (sumx2_t - sumx2_1 - (sumx_t-sumx_1)*(sumx_t-sumx_1)/(n_t - n_1) )/(n_t - n_1 -1 ) as var0
FROM  summ_table
LEFT JOIN ( SELECT symbol, COUNT( ParticipantBarcode ) as n_t, SUM( data ) as sumx_t, SUM( data*data ) as sumx2_t
            FROM table1 
            GROUP BY symbol )
ON symbol1 = symbol      
)
WHERE
   n_1 > {0} AND n_0 > {0} AND var1 > 0 and var0 > 0
ORDER BY tscore DESC
""".format( str(nsamples) )
        
    elif ( feat1['dattype'] == 'numeric' and feat_name2 == 'Somatic Mutation'  ) :
        stat_table = """,
statistics AS (
   SELECT symbol1, symbol2, n_t as n, 
       n_t * sumx_1 - n_1*sumx_t as  cov_xy,
       n_t * sumx2_t - sumx_t*sumx_t  as var_x,
       n_1 * (n_t - n_1 )  as var_y    
   FROM  summ_table
   LEFT JOIN ( SELECT symbol, COUNT( ParticipantBarcode ) as n_t, SUM( rnkdata ) as sumx_t, SUM( rnkdata*rnkdata ) as sumx2_t
            FROM table1 
            GROUP BY symbol )
   ON symbol1 = symbol  
   group by 1,2,3,4,5,6
   having var_x > 0 AND var_y > 0 
)
SELECT symbol1, symbol2, n,
       cov_xy / ( SQRT(var_x) *  SQRT(var_y) ) as correlation
FROM statistics 
where n > {0} AND n < 500 
group by 1,2,3,4
HAVING `cgc-05-0042.functions.significance_level_ttest2`(n-2, ABS(correlation)*SQRT((n-2)/((1+correlation)*(1-correlation)))) <= {1}
UNION ALL
SELECT symbol1, symbol2, n,
       cov_xy / ( SQRT(var_x) *  SQRT(var_y) ) as correlation
FROM statistics 
where n > {0} AND n >= 500 
group by 1,2,3,4
HAVING erfcc( ABS(correlation)*SQRT(n)/1.414213562373095 ) <= {1}
ORDER BY ABS(correlation) DESC
""".format( str(nsamples) , alpha )
        
    
    elif ( feat1['dattype'] == 'numeric' and feat_name2 == 'Clinical Categorical'  ) :
        stat_table = """
SELECT 
    symbol1, symbol2,
    Ngroups,
    N as Nsamples,        
    (N-1)*( sumSi2overni - (sumSi *sumSi)/N ) / (  sumSqi  - (sumSi *sumSi)/N )    AS  Hscore 
FROM (
SELECT symbol1, symbol2,
    SUM( n ) As N, 
    SUM( sumx ) AS sumSi,
    SUM( sumx2 ) AS sumSqi,
    SUM( sumx * sumx  / n ) AS sumSi2overni,
    COUNT ( category ) AS Ngroups
     
FROM  summ_table
WHERE
   n > {0}
GROUP BY
   symbol1, symbol2
)
WHERE 
   Ngroups > 1
ORDER BY Hscore DESC
""".format( str(nsamples) )        
        
    return stat_table 

def WidgetsSelectProject():
    projectList = [ 'TCGA' , 'CPTAC' ] 
    
    project = widgets.Dropdown( 
      options=projectList,
      value='TCGA',
      description='',
      disabled=False
      )
        
    project_title = widgets.HTML('<em>Select a project </em>')
    display(widgets.HBox([ project_title, project]))

    
    return([project])

def makeWidgets( project ):
  
  feature1 = ''
  gene_names = []
  feature2 = ''
  study = ''
  significance = ''
  size = ''
    
    
  if ( project == 'TCGA' ) : 
    
      studyList = [ 'ACC', 'BLCA', 'BRCA', 'CESC', 'CHOL', 'COAD', 'DLBC', 'ESCA', 
                'GBM', 'HNSC', 'KICH', 'KIRC', 'KIRP', 'LAML', 'LGG', 'LIHC', 
                'LUAD', 'LUSC', 'MESO', 'OV', 'PAAD', 'PCPG', 'PRAD', 'READ', 
                'SARC', 'SKCM', 'STAD', 'TGCT', 'THCA', 'THYM', 'UCEC', 'UCS', 
                'UVM' ]

      study = widgets.Dropdown(
          options=studyList,
          value='UCEC',
          description='',
          disabled=False
          )
    
      FeatureList1 = [ 'Gene Expression','MicroRNA Expression' ] ;
      FeatureList2 = [ 'Gene Expression', 'MicroRNA Expression'] ;  

      feature1 = widgets.Dropdown(
          options=FeatureList1,
          value='Gene Expression',
          description='',
          disabled=False
          )

      gene_names = widgets.Text(
          value='IGF2, ADAM6',
          placeholder='Type gene names  ',
          description='',
          disabled=False
          )

      feature2 = widgets.Dropdown(
          options=FeatureList2,
          value='Gene Expression',
          description='',
          disabled=False
          )

      significance = widgets.SelectionSlider( options=['0.05', '0.01', '0.005', '0.001'],
                                   value='0.01',
                                   description='',
                                   disabled=False,
                                   continuous_update=False,
                                   orientation='horizontal',
                                   readout=True
                                 )
    
      size = widgets.IntSlider(value=25, 
                           min=5, 
                           max=50,
                           description=''
                          )  # the n most variable genes
  

  elif ( project == 'CPTAC' ):
        
      studyList = [ 'CCRCC', 'GBM', 'HNSCC', 'LSCC', 'LUAD', 'PDA', 'UCEC', 'breast_BI',  ]

      study = widgets.Dropdown(
          options=studyList,
          value='CCRCC',
          description='',
          disabled=False
          )
    
      FeatureList1 = [ 'Gene Expression', 'Protein Expression'] ;
      FeatureList2 = [ 'Gene Expression', 'Protein Expression'] ;  

      feature1 = widgets.Dropdown(
          options=FeatureList1,
          value='Gene Expression',
          description='',
          disabled=False
          )

      gene_names = widgets.Text(
          value='IGF2, ADAM6',
          placeholder='Type gene names  ',
          description='',
          disabled=False
          )

      feature2 = widgets.Dropdown(
          options=FeatureList2,
          value='Protein Expression',
          description='',
          disabled=False
          )

      significance = widgets.SelectionSlider( options=['0.05', '0.01', '0.005', '0.001'],
                                   value='0.01',
                                   description='',
                                   disabled=False,
                                   continuous_update=False,
                                   orientation='horizontal',
                                   cout=True
                                 )
    
      size = widgets.IntSlider(value=25, 
                           min=5, 
                           max=50,
                           description=''
                          )  # the n most variable genes
        
        
        
  study_title = widgets.HTML('<em>Select a study </em>')
  display(widgets.HBox([study_title, study]))

  genes_title = widgets.HTML('<em>Symbol list </em>')
  display(widgets.HBox([ genes_title, gene_names  ]))

  feature1_title = widgets.HTML('<em>Select Feature1 </em>')  
  display(widgets.HBox([ feature1_title, feature1 ]))

  feature2_title = widgets.HTML('<em>Select Feature2 </em>')  
  display(widgets.HBox([ feature2_title, feature2 ]))

  significance_title = widgets.HTML('<em>Significance level </em>')
  display(widgets.HBox([ significance_title, significance]))
    
  size_title = widgets.HTML('<em>Minimum number of samples</em>')
  display(widgets.HBox([size_title, size]))
    
  #cohort_title = widgets.HTML('<em>Cohort list</em>')
  #display(widgets.HBox([cohort_title, cohortlist]))
  
  
  return([study, feature1, feature2, gene_names, size,  significance])


def makeWidgetsPair(list1, list2) : 
  # updated this section to use drop down widget - JAW
  # gene_name1 = widgets.Text(
  #     value='',
  #     placeholder='label name',
  #     description='',
  #     disabled=False
  #     )

  # gene_name2 = widgets.Text(
  #     value='',
  #     placeholder='label name',
  #     description='',
  #     disabled=False
  #     )  
  
  gene_name1 = widgets.Dropdown(
    options = list1,
    value = list1[0],
    description = '',
    disabled = False
  )

  gene_name2 = widgest.Dropdown(
    options = list2,
    value = list2[0],
    description = '',
    disabled = False
  )

  gene1_title = widgets.HTML('<em>Select symbol 1 </em>')
  display(widgets.HBox([ gene1_title, gene_name1  ]))

  gene2_title = widgets.HTML('<em>Select symbol 2 </em>')
  display(widgets.HBox([ gene2_title, gene_name2  ]))

  

  return([gene_name1 , gene_name2  ])

 

def table_pair ( symbol, feature2_name, study, samplelist, table_label ) :

   ft = bqtable_data( feature2_name ) 

   if ( feature2_name == 'Clinical Numeric' or feature2_name == 'Clinical Categorical' ) :
       ft['data'] = symbol 
       ft['symbol'] = '\'' + symbol + '\'' 
   

   cohort = ft['study'] + ' = \'' + study + '\'' 
 
   if  ( (feature2_name == 'Clinical Numeric') or (feature2_name == 'Clinical Categorical') ) :
        
       if ( len( samplelist ) > 0  ) :
           cohort = ft['patientcode'] + " IN UNNEST(@PATIENTLIST) "
        
            
       query_table = table_label + """ AS (
SELECT
   symbol,
   {0} AS data,
   ParticipantBarcode
FROM (
   SELECT
      {1} AS symbol, 
      {2} AS avgdata,
      {3} AS ParticipantBarcode
   FROM `{4}`
   WHERE {5}        
   )
)""".format(ft['avgdat'],ft['symbol'],ft['data'],ft['patientcode'],ft['table'], cohort )
    
   else :
       if ( len( samplelist ) > 0  ) :
           cohort = ft['samplecode'] + " IN UNNEST(@SAMPLELIST) "

       query_table = table_label + """ AS (
SELECT
   symbol,
   {0} AS data,
   ParticipantBarcode
FROM (
   SELECT
      {1} AS symbol, 
      {2} AS avgdata,
      {3} AS ParticipantBarcode
   FROM `{4}`
   WHERE {5} AND {1} = '{6}'
         {7}  
   GROUP BY
      ParticipantBarcode, symbol
   )
)""".format(ft['avgdat'],ft['symbol'],ft['data'],ft['patientcode'],ft['table'], cohort, symbol ,ft['where'] )
    
    
   
   return( query_table )

def table_pair_cptac( symbol, feature2_name, study, samplelist, table_label ) :

   ft = bqtable_data_cptac( feature2_name, study ) 
   
   

   query_table = table_label + """ AS (
SELECT
   symbol,
   avgdata AS data,
   ParticipantBarcode
FROM (
   SELECT
      t1.{0} AS symbol, 
      {1} AS avgdata,
      t2.{2} AS ParticipantBarcode
   FROM `{3}` t1
   JOIN `isb-cgc-bq.PDC_metadata.aliquot_to_case_mapping_current` as t2
   ON  t1.{4} = t2.{5}   # cohort 
         AND t1.{0} = '{6}'
         {7}  
   GROUP BY
      ParticipantBarcode, symbol
   )
)
""".format(ft['symbol'],ft['data'],ft['patientcode'],ft['table'], ft['samplecode'],ft['metasampleid'], symbol, ft['where'] )
        
   return( query_table )


    
def get_query_pair (project, name1, name2, study, samplelist, feature1_name, feature2_name): 

   name1 = name1.strip()
   name2 = name2.strip()
   
   if ( project == 'TCGA') :  
       query_table1 =  table_pair(name1, feature1_name , study, samplelist, 'table1' )
       query_table2 =  table_pair(name2, feature2_name , study, samplelist, 'table2' )

   elif ( project == 'CPTAC' ) :
       query_table1 =  table_pair_cptac(name1, feature1_name , study, samplelist, 'table1' )
       query_table2 =  table_pair_cptac(name2, feature2_name , study, samplelist, 'table2' )
    
   if ( (feature2_name == 'Gene Expression') or (feature2_name == 'Somatic Copy Number')   ):
      data2_str = 'n2.data' 
   elif ( (feature2_name == 'Somatic Mutation t-test') or feature2_name == 'Somatic Mutation' ):
      data2_str = 'IF( n2.ParticipantBarcode is null, 0, 1)'
   else :
      data2_str = 'n2.data'
   
   combine_str = """
SELECT 
    n1.data as data1,  
    {0} as data2,  
    n1.ParticipantBarcode
FROM
    table1 n1  
LEFT JOIN  table2   n2 
ON  n1.ParticipantBarcode = n2.ParticipantBarcode""".format( data2_str)
    
   query_pair = 'WITH\n' +  query_table1 + ',\n' + query_table2 + combine_str              
   return( query_pair )


def plot_statistics_pair ( mydf, project, study, feature1_name, feature2_name, name1 , name2, nsamples ) :  
    
   
    if ( project == 'TCGA') :  
       ft1 = bqtable_data( feature1_name )    
       ft2 = bqtable_data( feature1_name  )

    elif ( project == 'CPTAC' ) :
       ft1 = bqtable_data_cptac( feature1_name, study )    
       ft2 = bqtable_data_cptac( feature1_name, study )
    
    

    if ( (ft1['dattype'] == 'numeric') and (ft2['dattype'] == 'numeric')  ): 
         
         label1 = name1.strip() + " (" +  feature1_name + ")"
         label2 = name2.strip() + " (" +  feature2_name + ")" 
         
         new_df = pd.DataFrame()
         new_df[label1] = pd.to_numeric( mydf['data1'] , errors='coerce') 
         new_df[label2] = pd.to_numeric( mydf['data2'] , errors='coerce') 
  
         new_df.dropna(axis = 0, how ='any', inplace = True)
         
         new_df.plot.scatter(x=label1, y=label2) 
         print(  stats.spearmanr(new_df[ label1],new_df[label2])  )

        
    elif (feature2_name == 'Somatic Mutation t-test' ): 
         label1 = name1.strip() + " (gene expression)"
         label2 = name2.strip() + " (Somatic Mutation)"
       
         mydf.rename(columns={ "data1": label1, "data2": label2 }, inplace=True)
        
         sns.violinplot( x=mydf[label2], y=mydf[label1], palette="Pastel1")
 
         print( mydf.groupby(label2).agg(['mean', 'count']) )
        
         Set1 = mydf[mydf[label2]==0]
         Set2 = mydf[mydf[label2]==1]
        
         print('\nT-test statistics : ')
         print( stats.ttest_ind(Set1[label1], Set2[label1], equal_var=False ) )
        
    elif (feature2_name == 'Somatic Mutation' ): 
         label1 = name1.strip() + " (gene expression)"
         label2 = name2.strip() + " (Somatic Mutation)"
       
         newdf = mydf.rename(columns={ "data1": label1, "data2": label2 })
        
         sns.violinplot( x=newdf[label2], y=newdf[label1], palette="Pastel1")
            
         # rank data 
          
         print( newdf.groupby(label2).agg(['mean', 'count']) )
        
         #Set1 = mydf[mydf[label2]==0]
         #Set2 = mydf[mydf[label2]==1]
        
         print('\nSpearman correlation : ')
         newdf['rnkdata']  = newdf[label1].rank(method='average') #average, min
         print( stats.pearsonr( newdf['rnkdata'] , newdf[label2] ) )  
        

    elif (feature2_name == 'Clinical Categorical' ) :
         new_data = mydf[ mydf.data2.str.contains('^\[.*\]$',na=True,regex=True) == False ]
         label1 = name1.strip() + " (gene expression)"
         label2 = name2.strip() + " (clinical)"
         new_data.rename(columns={ "data1": label1, "data2": label2 }, inplace=True)
        
         sns.violinplot( x=new_data[label2], y=new_data[label1], palette="Pastel1")
        
         print( new_data.groupby( label2 ).agg(['median', 'count']) )
        
         CategoryData = []
         CategoryNames = [] 
         for name, group in new_data.groupby( label2 ) :
             data =  group[ label1 ].values 
             if ( len( data ) > nsamples ) :
                  CategoryData.append( data )
                  CategoryNames.append( name )
                
         print('\nKruskal-Wallis test for groups with more than '+ str(nsamples) +' patients : ')        
         if len( CategoryData ) > 1 :
            print( mstats.kruskalwallis( *[ mydata for mydata in CategoryData   ] ) )
         else :
            print( 'Number of groups less than 2 \n')
        
        
            
    return 

