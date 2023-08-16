import sys
import numpy as np
import pandas as pd
from statsmodels.sandbox.stats.multicomp import multipletests
from scipy import stats
from google.cloud import bigquery
import helper
from helper import *


def ProcessGeneAlias (client, input_gene_list, database):
    '''
    Description:Enables to use  all aliases of the given gene list.
    
    Inputs: 
        client:BigQueryClient, the BigQuery client that will run the function.
        input_gene_list:list of strings, the list of gene whose SL partners are seeked
       database:string, the data resource that will be used,  valid values: "PanCancerAtlas", "DepMap"

    Output:
         A dictionary that maps gene symbosl in the given database to the input gene list
    
    '''
    pancanceratlas_genes_query="""SELECT DISTINCT Gene_Symbol from `isb-cgc-bq.pancancer_atlas.Filtered_all_CNVR_data_by_gene`
    UNION DISTINCT  
    SELECT DISTINCT Symbol from  `isb-cgc-bq.pancancer_atlas.Filtered_EBpp_AdjustPANCAN_IlluminaHiSeq_RNASeqV2_genExp`
    UNION DISTINCT
    SELECT DISTINCT Hugo_Symbol from `isb-cgc-bq.pancancer_atlas.Filtered_MC3_MAF_V5_one_per_tumor_sample`  """
    depmap_genes_query= """ SELECT DISTINCT Hugo_Symbol from  `isb-cgc-bq.DEPMAP.CCLE_gene_cn_DepMapPublic_current`
    UNION DISTINCT
    SELECT DISTINCT Hugo_Symbol from `isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current`
    UNION DISTINCT
    SELECT DISTINCT Hugo_Symbol from `isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current`   """
    df=pd.DataFrame(columns=["Input_Gene", "DB_Gene"])

    if database=="PanCancerAtlas":
        pancancer_atlas_genes= list(client.query(pancanceratlas_genes_query).result().to_dataframe()['Gene_Symbol'])
        df["Input_Gene" ]= input_gene_list
        df.loc[df["Input_Gene" ].isin(pancancer_atlas_genes ),"DB_Gene"]=df.loc[df["Input_Gene" ].isin(pancancer_atlas_genes), "Input_Gene"]
        search_genes= list(df.loc[~df["Input_Gene" ].isin(pancancer_atlas_genes ),"Input_Gene"])
        if len(search_genes)>0:
            converted=ConvertGene(client, search_genes, 'Gene', ['Alias'])  
            add_lines= converted.loc[converted['Alias'].isin(pancancer_atlas_genes),]
            add_lines.columns=["Input_Gene", "DB_Gene"]
            df=pd.concat([df, add_lines])

    elif database=="DepMap":
        depmap_genes= list(client.query(depmap_genes_query).result().to_dataframe()['Hugo_Symbol'])
        df["Input_Gene" ]= input_gene_list
        df.loc[df["Input_Gene" ].isin(depmap_genes),"DB_Gene"]=df.loc[df["Input_Gene" ].isin(depmap_genes), "Input_Gene"]
        search_genes= list(df.loc[~df["Input_Gene" ].isin(depmap_genes),"Input_Gene"])
        if len(search_genes)>0:
            converted=ConvertGene(client, search_genes, 'Gene', ['Alias'])  
            add_lines= converted.loc[converted['Alias'].isin(depmap_genes),]
            add_lines.columns=["Input_Gene", "DB_Gene"]
            df=pd.concat([df, add_lines])
    else:
        print("DB name can be either PancancerAtlas or DepMap")
    df.columns=["Input_Gene", "DB_Gene"]
    return(dict(zip(df.DB_Gene, df.Input_Gene)))
        
        
def GetTCGASubtypes(client):
    '''
    Description: Returns the TCGA cancer types that have corresponding samples in CCLE data"
    Input:
        client:BigQuery client,the BigQuery client that will run the function.
    Output:
        List of TCGA cancer types
    '''
    query="""
    SELECT DISTINCT TCGA_subtype from `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3`
    WHERE  primary_disease not in ('Non-Cancerous','Unknown','Engineered','Immortalized')
    """
    all_tissues=client.query(query).result().to_dataframe()
    return(list(all_tissues['TCGA_subtype']))

def RetrieveSamples(client, data_resource, method, tissues):
    '''
    Description:Retrieve the sample ids according to input parameters
    Inputs:
        client:BigQuery client, the BigQuery client that will run the function.
        data_source:string, valid values: "PanCancerAtlas", "CCLE" 
        method:one of DAISY inference procedures, valid values: "correlation", "sof", "func_ex"
        tissues: list of strings, the tissue type(s) that we are seeking SL pairs in.Could be one or more tissues. 
    Output:
        A dataframe of sample ids and tissue type
    
    '''
    min_sample_size=20;
    input_tissues= ["'"+ str(x) + "'" for x in tissues]
    input_tissues= ','.join(input_tissues)

    if data_resource=='PanCancerAtlas' and method=='correlation':
        tissue_query= " AND Study in (__TISSUE__)"
        sample_selection_sql='''SELECT distinct SampleBarcode FROM `isb-cgc-bq.pancancer_atlas.Filtered_EBpp_AdjustPANCAN_IlluminaHiSeq_RNASeqV2_genExp` 
    WHERE SampleType not like '%Normal%' and Study is not null '''
        if tissues.count('pancancer')==0:          
            sample_selection_sql=sample_selection_sql + tissue_query
            sample_selection_sql= sample_selection_sql.replace('__TISSUE__', input_tissues)
        selected_samples= list(client.query(sample_selection_sql).result().to_dataframe()['SampleBarcode'])

    elif data_resource=='PanCancerAtlas' and method=='sof':
        tissue_query= " WHERE  TS.Study  in (__TISSUE__)"
        sample_selection_sql= '''SELECT distinct SampleBarcode, Study FROM 
                (SELECT distinct SampleBarcode, Study FROM `isb-cgc-bq.pancancer_atlas.Filtered_EBpp_AdjustPANCAN_IlluminaHiSeq_RNASeqV2_genExp`
		WHERE SampleType not like '%Normal%'and Study is not null
		INTERSECT DISTINCT
		SELECT distinct SampleBarcode,  Study  FROM `isb-cgc-bq.pancancer_atlas.Filtered_all_CNVR_data_by_gene`
		WHERE SampleType not like '%Normal%' and Study is not null
		INTERSECT DISTINCT
		SELECT distinct Tumor_SampleBarcode as  SampleBarcode,  Study  FROM `isb-cgc-bq.pancancer_atlas.Filtered_MC3_MAF_V5_one_per_tumor_sample` WHERE Study is not null)
		TS '''

        if tissues.count('pancancer')==0:
            sample_selection_sql=sample_selection_sql + tissue_query
            sample_selection_sql= sample_selection_sql.replace('__TISSUE__', input_tissues)
        selected_samples= list(client.query(sample_selection_sql).result().to_dataframe()['SampleBarcode'])

 
    elif data_resource=='CCLE' and method=='correlation':
        tissue_query= " AND ST.TCGA_subtype in (__TISSUE__) "
        sample_selection_sql= ''' SELECT  distinct ST.DepMap_ID FROM  `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
        `isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current` E  
         WHERE ST.primary_disease 
        not in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND E.DepMap_ID=ST.DepMap_ID '''
        if tissues.count('pancancer')==0:
            sample_selection_sql=sample_selection_sql + tissue_query
            sample_selection_sql=sample_selection_sql.replace('__TISSUE__', input_tissues)
        selected_samples= list(client.query(sample_selection_sql).result().to_dataframe()['DepMap_ID'])

    elif data_resource=='CCLE' and method=='sof':
        tissue_query=  " WHERE TS.TCGA_subtype in (__TISSUE__) "
        sample_selection_sql= '''SELECT distinct DepMap_ID, TCGA_subtype FROM
                (SELECT  distinct ST.DepMap_ID  AS DepMap_ID, ST.TCGA_subtype as TCGA_subtype
                FROM  `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
   		 `isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current` E  WHERE  ST.primary_disease not
  		in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND E.DepMap_ID=ST.DepMap_ID 
  		INTERSECT DISTINCT
   		SELECT  distinct ST.DepMap_ID  AS DepMap_ID, ST.TCGA_subtype as TCGA_subtype FROM `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
   		`isb-cgc-bq.DEPMAP.CCLE_gene_cn_DepMapPublic_current`  C  WHERE  ST.primary_disease not
  		in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND C.DepMap_ID=ST.DepMap_ID 
  		INTERSECT DISTINCT
  		SELECT  distinct ST.DepMap_ID  AS DepMap_ID, ST.TCGA_subtype as TCGA_subtype
  		FROM  `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
  		`isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current` M  WHERE  ST.primary_disease not
  		in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND M.DepMap_ID=ST.DepMap_ID ) TS'''
        if tissues.count('pancancer')==0:
            sample_selection_sql=sample_selection_sql+ tissue_query
            sample_selection_sql=sample_selection_sql.replace('__TISSUE__', input_tissues)

        selected_samples= list(client.query(sample_selection_sql).result().to_dataframe()['DepMap_ID'])

        
    elif data_resource=='CRISPR' and method=='func_ex':
        tissue_query=  " WHERE TS.TCGA_subtype in (__TISSUE__) "
        sample_selection_sql= '''SELECT distinct DepMap_ID, TCGA_subtype FROM
        (SELECT  distinct ST.DepMap_ID AS DepMap_ID , ST.TCGA_subtype AS TCGA_subtype FROM `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,     `isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current` E  WHERE  ST.primary_disease not
      in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND E.DepMap_ID=ST.DepMap_ID 
      INTERSECT DISTINCT
      SELECT distinct ST.DepMap_ID AS DepMap_ID , ST.TCGA_subtype AS TCGA_subtype  FROM  `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
      `isb-cgc-bq.DEPMAP.CCLE_gene_cn_DepMapPublic_current`  C  WHERE  ST.primary_disease not
      in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND C.DepMap_ID=ST.DepMap_ID 
      INTERSECT DISTINCT
      SELECT distinct ST.DepMap_ID AS DepMap_ID , ST.TCGA_subtype AS TCGA_subtype  FROM `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
      `isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current` M  WHERE ST.primary_disease not
      in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND M.DepMap_ID=ST.DepMap_ID 
      INTERSECT DISTINCT
      SELECT distinct ST.DepMap_ID AS DepMap_ID , ST.TCGA_subtype AS TCGA_subtype  FROM  `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
      `isb-cgc-bq.DEPMAP.Achilles_gene_effect_DepMapPublic_current` A  WHERE  ST.primary_disease not
      in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND A.DepMap_ID=ST.DepMap_ID)  TS'''
        if tissues.count('pancancer')==0:
            sample_selection_sql=sample_selection_sql+ tissue_query
            sample_selection_sql=sample_selection_sql.replace('__TISSUE__', input_tissues)
        selected_samples= list(client.query(sample_selection_sql).result().to_dataframe()['DepMap_ID'])


    elif data_resource=='shRNA' and method=='func_ex':
        tissue_query="WHERE TS.TCGA_subtype in (__TISSUE__)"
        sample_selection_sql= '''SELECT CCLE_Name, DepMap_ID FROM
      (SELECT distinct ST.CCLE_Name AS CCLE_Name, ST.DepMap_ID  AS DepMap_ID, ST.TCGA_subtype AS TCGA_subtype  FROM
     `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
      `isb-cgc-bq.DEPMAP.Combined_gene_dep_score_DEMETER2_current`   DS  WHERE ST.primary_disease not
        in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND DS.CCLE_ID=ST.CCLE_Name

      INTERSECT DISTINCT

      SELECT distinct  ST.CCLE_Name AS CCLE_Name, ST.DepMap_ID  AS DepMap_ID, ST.TCGA_subtype AS TCGA_subtype
        FROM  `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
     `isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current`  E  WHERE   ST.primary_disease not
     in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND E.DepMap_ID=ST.DepMap_ID

      INTERSECT DISTINCT

       SELECT  distinct ST.CCLE_Name AS CCLE_Name, ST.DepMap_ID  AS DepMap_ID,   ST.TCGA_subtype AS TCGA_subtype FROM
     `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
       `isb-cgc-bq.DEPMAP.CCLE_gene_cn_DepMapPublic_current`  C  WHERE ST.primary_disease not
      in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND C.DepMap_ID=ST.DepMap_ID 

      INTERSECT DISTINCT
      SELECT  distinct ST.CCLE_Name AS CCLE_Name, ST.DepMap_ID  AS DepMap_ID, ST.TCGA_subtype AS TCGA_subtype FROM
     `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` ST,
       `isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current` M  WHERE  ST.primary_disease not
       in ('Non-Cancerous','Unknown','Engineered','Immortalized') AND M.DepMap_ID=ST.DepMap_ID) TS '''

        if tissues.count('pancancer')==0:
            sample_selection_sql=sample_selection_sql+ tissue_query
            sample_selection_sql=sample_selection_sql.replace('__TISSUE__', input_tissues)
        selected_samples= client.query(sample_selection_sql).result().to_dataframe()


    return selected_samples

def CoexpressionAnalysis(client, SL_or_SDL, data_resource, input_genes, adj_method, fdr_level, tissues):

    '''
   Description: "The gene correlation information is used to detect SL pairs."

   Inputs:
    client:BigQueryClient, the BigQuery client that will run the function.
    SL_or_SDL:string, Synthetic lethal or Synthetic Dosage Lethal, valid values: 'SL', 'SDL'
    data_resource: string, The dataresource the analysis will be performed on, 	valid values: "CCLE", "PanCancerAtlas"
    input_genes:list of strings, the list of genes whose SL/SDL partners will be seeked	
    adj_method:	string,	optional, p value correction method,  valid_values:bonferroni,  sidak, holm-sidak , holm, simes-hochberg , hommel, fdr_bh,  fdr_by , fdr_tsbh, fdr_tsbky 
    fdr_level:string, the data that will be considered wile doing p value adjustment, valid values : "gene_level", "analysis_level"
    tissues: The tissues that the analysis will be performed on. 

    Output:
    A dataframe of SL/SDL pairs
        
    '''
  
    if data_resource=='PanCancerAtlas':
        table_name='isb-cgc-bq.pancancer_atlas.Filtered_EBpp_AdjustPANCAN_IlluminaHiSeq_RNASeqV2_genExp'
        gene_col_name='Symbol'
        entrez_col_name='Entrez'
        exp_name='normalized_count'
        sample_barcode='SampleBarcode'
        selected_samples=RetrieveSamples(client, 'PanCancerAtlas', 'correlation', tissues)
        gene_mapping=ProcessGeneAlias(client, input_genes, 'PanCancerAtlas')

        
    elif data_resource=='CCLE':
        table_name='isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current'
        gene_col_name='Hugo_Symbol'
        exp_name='TPM'
        sample_barcode='DepMap_ID'
        entrez_col_name='Entrez_ID'
        selected_samples=RetrieveSamples(client, 'CCLE','correlation', tissues)
        gene_mapping=ProcessGeneAlias(client, input_genes, 'DepMap')

    else :
        print("The database name can be either PanCancerAtlas or CCLE")
        return()

    min_sample_size=20
    if len(selected_samples)< (min_sample_size+1):
        print("Sample size needs to be greater than " +  str(min_sample_size) + ", it is " + str(len(selected_samples)))
        return()
    sql_correlation= """ CREATE TEMPORARY FUNCTION tscore_to_p(a FLOAT64, b FLOAT64, c FLOAT64)
     RETURNS FLOAT64
    LANGUAGE js AS
    \"\"\"
    return jStat.ttest(a,b,c); //jStat.ttest( tscore, n, sides)
    \"\"\"
    OPTIONS (
     library="gs://javascript-lib/jstat.min.js"
    );

    WITH
    table1 AS (
    SELECT
    symbol,
   (RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) -  1)/2.0 AS rnkdata,
   ParticipantBarcode
	FROM (
   SELECT
   __GENE_SYMBOL__  symbol,
      AVG( __EXP_NAME__)  AS data,
      __SAMPLE_ID__ AS ParticipantBarcode
   FROM `__TABLE_NAME__`
   WHERE  __GENE_SYMBOL__   IN (__GENE_LIST__) # labels
         AND __EXP_NAME__ IS NOT NULL  AND __SAMPLE_ID__ in (__SAMPLE_LIST__)
   GROUP BY
      ParticipantBarcode, symbol
       )
    )
    ,
    table2 AS (
    SELECT
    symbol,
   (RANK() OVER (PARTITION BY symbol ORDER BY data ASC)) + (COUNT(*) OVER ( PARTITION BY symbol, CAST(data as STRING)) - 1)/2.0 AS rnkdata,
   ParticipantBarcode
    FROM (
   SELECT
      __GENE_SYMBOL__    symbol,
      AVG(__EXP_NAME__)  AS data,
      __SAMPLE_ID__ AS ParticipantBarcode
   FROM `__TABLE_NAME__`
   WHERE  __GENE_SYMBOL__ IS NOT NULL  # labels
         AND __EXP_NAME__ IS NOT NULL AND __SAMPLE_ID__ in (__SAMPLE_LIST__)
   GROUP BY
      ParticipantBarcode, symbol
       )
    )
,
summ_table AS (
SELECT
   n1.symbol as symbol1,
   n2.symbol as symbol2,
   COUNT( n1.ParticipantBarcode ) as n,
   CORR(n1.rnkdata , n2.rnkdata) as correlation

FROM
   table1 AS n1
INNER JOIN
   table2 AS n2
ON
   n1.ParticipantBarcode = n2.ParticipantBarcode
   AND n2.symbol  NOT IN (__GENE_LIST__)

GROUP BY
   symbol1, symbol2
UNION ALL
SELECT
   n1.symbol as symbol1,
   n2.symbol as symbol2,
   COUNT( n1.ParticipantBarcode ) as n,
   CORR(n1.rnkdata , n2.rnkdata) as correlation

FROM
   table1 AS n1
INNER JOIN
   table1 AS n2
ON
   n1.ParticipantBarcode = n2.ParticipantBarcode
   AND n1.symbol <  n2.symbol
GROUP BY
   symbol1, symbol2
)
SELECT *,
   tscore_to_p( ABS(correlation)*SQRT( (n-2)/((1+correlation)*(1-correlation))) ,n-2, 2) as pvalue
   #`cgc-05-0042.Auxiliary.significance_level_ttest2`(n-2, ABS(correlation)*SQRT( (n-2)/((1+correlation)*(1-correlation)))) as alpha
FROM summ_table
WHERE n > 20
#AND correlation > __COR_THRESHOLD__
GROUP BY 1,2,3,4,5
#HAVING pvalue <= __P_THRESHOLD__
ORDER BY symbol1 ASC, correlation DESC """

    input_genes = ["'"+ str(x) + "'" for x in input_genes]
    input_genes_for_query= ','.join(input_genes)

    included_samples=["'"+ str(x) + "'" for x in selected_samples]
    included_samples= ','.join(included_samples)

    sql_correlation = sql_correlation.replace('__GENE_LIST__', input_genes_for_query)
    sql_correlation = sql_correlation.replace('__TABLE_NAME__', table_name)
    sql_correlation = sql_correlation.replace('__GENE_SYMBOL__', gene_col_name)
    sql_correlation = sql_correlation.replace('__EXP_NAME__', exp_name)
    sql_correlation = sql_correlation.replace('__SAMPLE_ID__', sample_barcode)
    sql_correlation = sql_correlation.replace('__SAMPLE_LIST__', included_samples)


    results= client.query(sql_correlation).result().to_dataframe()
    if results.shape[0]<1:
        print("Coexpression inference procedure applied on " + data_resource + " did not find candidate " + SL_or_SDL + " pairs.")
        return(results)
        
    report=results[['symbol1', 'symbol2', 'n', 'correlation', 'pvalue']]
    report=report.dropna()
    report.columns=['InactiveDB', 'SL_Candidate', '#Samples', 'Correlation', 'PValue']
    report['Inactive']= report['InactiveDB'].map(gene_mapping)
    if fdr_level=="gene_level":
        inactive_genes=list(report["Inactive"].unique())
        for i in range(len(inactive_genes)):
           report.loc[report["Inactive"]==inactive_genes[i],'FDR']=multipletests(report.loc[report["Inactive"]==inactive_genes[i], 'PValue'], method= adj_method, is_sorted=False)[1]

    elif fdr_level=="analysis_level":
       FDR=multipletests(report['PValue'],  method= adj_method, is_sorted=False)[1]
       report['FDR']=FDR
    else:
      print("FDR level can be either gene_level or analysis_level")
      return()
 
    report['Tissue']=str(tissues)
    cols=['Inactive', 'InactiveDB', 'SL_Candidate', '#Samples', 'Correlation', 'PValue', 'FDR', 'Tissue']
    report=report[cols]
    if SL_or_SDL=="SDL":
      report.columns= ['Overactive', 'OveractiveDB', 'SL_Candidate', '#Samples', 'Correlation', 'PValue', 'FDR', 'Tissue']
    return report

def SurvivalOfFittest(client, SL_or_SDL, data_source, input_genes, percentile_threshold, cn_threshold, adj_method, fdr_level, tissues, input_mutations='None'):

  '''
   Description: Gene expression, Copy Number Alteration (CNA), Somatic Mutations are used to decide whether gene is inactive.
   The SL pair detection according to difference in CNA given one gene is inactive vs not-inactive
   Inputs:
    client:BigQueryClient, the BigQuery client that will run the function.
    SL_or_SDL:string, Synthetic lethal or Synthetic Dosage Lethal, valid values: 'SL', 'SDL'
    data_resource: string, The dataresource the analysis will be performed on, 	valid values: "CCLE", "PanCancerAtlas"
    input_genes:list of strings, the list of genes whose SL/SDL partners will be seeked	
    percentile_threshold:double, the threshold for gene expression (for deciding whether a gene is inactive)
    cn_threshold:double, the threshold for copy number alteration (for deciding whether a gene is inactive)
    adj_method:	string,	optional, p value correction method,  valid_values:bonferroni,  sidak, holm-sidak , holm, simes-hochberg , hommel, fdr_bh,  fdr_by , fdr_tsbh, fdr_tsbky 
    fdr_level:string, the data that will be considered wile doing p value adjustment, valid values : "gene_level", "analysis_level"
    tissues: The tissues that the analysis will be performed on. 
    input_mutations:list of strings, optional, valid values: Missense_Mutation, Nonsense_Mutation,Translation_Start_Site, Frame_Shift_Ins, Splice_Site, In_Frame_DelFrame_Shift_Del, Nonstop_Mutation, In_Frame_Ins
        
   Output:
       A dataframe of SL/SDL  pairs

  '''
  if data_source=='PanCancerAtlas':
        gene_exp_table='isb-cgc-bq.pancancer_atlas.Filtered_EBpp_AdjustPANCAN_IlluminaHiSeq_RNASeqV2_genExp'
        mutation_table='isb-cgc-bq.pancancer_atlas.Filtered_MC3_MAF_V5_one_per_tumor_sample'
        cn_table='isb-cgc-bq.pancancer_atlas.Filtered_all_CNVR_data_by_gene'

        sample_id='SampleBarcode'
        gene_col_name='Symbol'
        gene_exp='normalized_count'
        cn_gene_name='Gene_Symbol'
        mutation_gene_name='Hugo_Symbol'
        mutation_sample_id='Tumor_SampleBarcode'
        cn_gistic='GISTIC_Calls'
        entrez_id='Entrez'
        selected_samples= RetrieveSamples(client, 'PanCancerAtlas', 'sof', tissues)
        gene_mapping=ProcessGeneAlias(client, input_genes, 'PanCancerAtlas')
  elif data_source=='CCLE':
        mutation_table='isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current'
        gene_exp_table='isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current'
        cn_table='isb-cgc-bq.DEPMAP.CCLE_gene_cn_DepMapPublic_current'
        sample_id='DepMap_ID'
        gene_col_name='Hugo_Symbol'
        gene_exp='TPM'
        cn_gene_name='Hugo_Symbol'
        mutation_gene_name='Hugo_Symbol'
        mutation_sample_id='Tumor_Sample_Barcode'
        cn_gistic='CNA'
        cn_threshold=np.log2(2**(cn_threshold)+1)
        entrez_id='Entrez_ID'
        selected_samples= RetrieveSamples(client, 'CCLE', 'sof', tissues)
        gene_mapping=ProcessGeneAlias(client, input_genes, 'DepMap')


  else :
        print("The data source name can be either PanCancerAtlas or CCLE")
        return()
  min_sample_size=20
  if len(selected_samples)< (min_sample_size+1):
        print("Sample size needs to be greater than " +  str(min_sample_size), " it is " + str(len(selected_samples)))
        return()

  sql_without_mutation= '''
    WITH
    table1 AS (
    (SELECT   symbol, Barcode FROM
    (SELECT GE.__EXP_GENE_NAME__ AS symbol, GE.__SAMPLE_ID__ AS Barcode ,
    PERCENT_RANK () over (partition by __EXP_GENE_NAME__ order by __GENE_EXPRESSION__ asc) AS Percentile
    FROM  __GENE_EXP_TABLE__ GE
    WHERE GE.__EXP_GENE_NAME__ in (__GENELIST__)  AND __SAMPLE_ID__ in (__SAMPLE_LIST__) AND GE.__GENE_EXPRESSION__ is not null
    )
    AS NGE
    WHERE NGE.Percentile  __GENE_CMP_STR__

    INTERSECT DISTINCT

    SELECT symbol ,  Barcode FROM
    (SELECT CN.__CN_GENE_NAME__ AS symbol, CN.__SAMPLE_ID__ AS Barcode,
    CN.__CN_GISTIC__ AS NORM_CN
    FROM  __CN_TABLE__ CN
    WHERE CN.__CN_GENE_NAME__ in (__GENELIST__)  AND __SAMPLE_ID__ in (__SAMPLE_LIST__)  and CN.__CN_GISTIC__ is not null
    ) AS NC
    WHERE NC.NORM_CN __CN_CMP_STR__
    )'''

  if data_source=='CCLE':
        sql_mutation_part='''

        UNION DISTINCT
        SELECT M.__MUTATION_GENE_NAME__  AS symbol , M.__MUTATION_SAMPLE_ID__ AS Barcode
        FROM __MUTATION_TABLE__ M
        WHERE __MUTATION_GENE_NAME__ IN (__GENELIST__) AND
        M.Variant_Classification IN (__MUTATIONLIST__) AND __MUT_SAMPLE_ID__ in (__SAMPLE_LIST__)
        )'''

  elif data_source=='PanCancerAtlas':
        sql_mutation_part='''
         UNION DISTINCT
        SELECT M.__MUTATION_GENE_NAME__  AS symbol , M.__MUTATION_SAMPLE_ID__ AS Barcode
        FROM __MUTATION_TABLE__ M
        WHERE __MUTATION_GENE_NAME__ IN (__GENELIST__) AND
        M.Variant_Classification IN (__MUTATIONLIST__) AND __MUT_SAMPLE_ID__ in (__SAMPLE_LIST__) AND Filter="PASS"
        )'''

  rest_of_the_query= '''
     , table2 AS (
    SELECT
        __SAMPLE_ID__ Barcode,  __CN_GENE_NAME__ symbol,
        (RANK() OVER (PARTITION BY __CN_GENE_NAME__ ORDER BY __CN_GISTIC__ ASC)) + (COUNT(*) OVER ( PARTITION BY __CN_GENE_NAME__, CAST(__CN_GISTIC__ as STRING)) - 1)/2.0  AS rnkdata
    FROM
       __CN_TABLE__
       where __CN_GENE_NAME__ IS NOT NULL  AND  __SAMPLE_ID__ in (__SAMPLE_LIST__) AND __CN_GISTIC__ is not null 
       ),
summ_table AS (
SELECT
   n1.symbol as symbol1,
   n2.symbol as symbol2,
   COUNT( n1.Barcode) as n_1,
   SUM( n2.rnkdata )  as sumx_1,
FROM
   table1 AS n1
INNER JOIN
   table2 AS n2
ON
   n1.Barcode = n2.Barcode
GROUP BY
    symbol1, symbol2 ),

statistics AS (
SELECT symbol1, symbol2, n1, n, U1,
      (n1n2/2.0 - U1)/den as zscore

FROM (
   SELECT  symbol1, symbol2, n_t as n,
       n_1 as n1,
       sumx_1 - n_1 *(n_1 + 1) / 2.0 as U1,
       n_1 * (n_t - n_1 ) as n1n2,
       SQRT( n_1 * (n_t - n_1 )*(n_t + 1) / 12.0 ) as den
   FROM  summ_table as t1
   LEFT JOIN ( SELECT symbol, COUNT( Barcode ) as n_t
            FROM table2
            GROUP BY symbol)  t2
   ON symbol2 = symbol
   WHERE n_t > 20 and n_1>5
)
WHERE den > 0
)
SELECT symbol1, symbol2, n1, n, U1,
    `cgc-05-0042.functions.jstat_normal_cdf`(zscore, 0.0, 1.0 ) as pvalue
FROM statistics
GROUP BY 1,2,3,4,5,6
#HAVING pvalue <= 0.01
ORDER BY pvalue ASC '''

  input_genes = ["'"+ str(x) + "'" for x in input_genes]
  input_genes_query= ','.join(input_genes)

  included_samples=["'"+ str(x) + "'" for x in selected_samples]
  included_samples= ','.join(included_samples)


  if SL_or_SDL=='SDL' or input_mutations is None:
      sql_sof=sql_without_mutation +  ')' +' ' +  rest_of_the_query
  else:
      mutations_intermediate_representation = ["'"+x+"'" for x in input_mutations]
      input_mutations_for_query = ','.join(mutations_intermediate_representation)
      sql_sof=sql_without_mutation + ' '+ sql_mutation_part + ' ' +  rest_of_the_query
      sql_sof = sql_sof.replace('__MUTATION_TABLE__', mutation_table)
      sql_sof = sql_sof.replace('__MUTATION_SAMPLE_ID__', mutation_sample_id)
      sql_sof = sql_sof.replace('__MUTATIONLIST__', input_mutations_for_query)

  sql_sof = sql_sof.replace('__GENELIST__', input_genes_query)
 # sql_sof = sql_sof.replace('__CUTOFFPRC__', str(percentile_threshold/100))
 # sql_sof = sql_sof.replace('__CUTOFFSCNA__', str(cn_threshold))
  sql_sof = sql_sof.replace('__CN_TABLE__', cn_table)
  sql_sof = sql_sof.replace('__GENE_EXP_TABLE__', gene_exp_table)
  sql_sof = sql_sof.replace('__SAMPLE_ID__', sample_id)
  sql_sof = sql_sof.replace('__MUT_SAMPLE_ID__', mutation_sample_id)
  sql_sof = sql_sof.replace('__ENTREZ_ID__', entrez_id)
  sql_sof = sql_sof.replace('__CN_TABLE__', cn_table)
  sql_sof = sql_sof.replace('__GENE_EXPRESSION__', gene_exp)
  sql_sof = sql_sof.replace('__CN_GISTIC__', cn_gistic)
  sql_sof = sql_sof.replace('__EXP_GENE_NAME__', gene_col_name)
  sql_sof = sql_sof.replace('__CN_GENE_NAME__', cn_gene_name)
  sql_sof = sql_sof.replace('__MUTATION_GENE_NAME__', mutation_gene_name)
  sql_sof= sql_sof.replace('__SAMPLE_LIST__', included_samples)

  if SL_or_SDL=="SL":
      comp_str="<"+str(cn_threshold)
      com_gene_th="<"+str(percentile_threshold/100)

  elif SL_or_SDL=="SDL":
      comp_str=">"+str(cn_threshold)
      sql_sof= sql_sof.replace('__CN_CMP_STR__', comp_str)
      com_gene_th=">"+str(percentile_threshold/100)
      sql_sof= sql_sof.replace('__GENE_CMP_STR__', com_gene_th)

  sql_sof= sql_sof.replace('__CN_CMP_STR__', comp_str)
  sql_sof= sql_sof.replace('__GENE_CMP_STR__', com_gene_th)


  results= client.query(sql_sof).result().to_dataframe()

  if results.shape[0]<1:
      print("SOF inference procedure applied on " + data_resource + " did not find candidate " + SL_or_SDL + " pairs.")
      return(results)
  report=results [['symbol1', 'symbol2', 'n1', 'n', 'U1', 'pvalue']]
  report=report.dropna()
  report.columns=['InactiveDB', 'SL_Candidate', '#InactiveSamples', '#Samples', 'U1','PValue']
  report['Inactive']= report['InactiveDB'].map(gene_mapping)

  if fdr_level=="gene_level":
      inactive_genes=list(report["Inactive"].unique())
      for i in range(len(inactive_genes)):
         report.loc[report["Inactive"]==inactive_genes[i],'FDR']=multipletests(report.loc[report["Inactive"]==inactive_genes[i], 'PValue'], method= adj_method, is_sorted=False)[1]

  elif fdr_level=="analysis_level":
     FDR=multipletests(report['PValue'],  method= adj_method, is_sorted=False)[1]
     report['FDR']=FDR
  else:
    print("FDR level can be either gene_level or analysis_level")
    return()
 
  report['Tissue']=str(tissues)
  
  cols=['Inactive', 'InactiveDB', 'SL_Candidate','#InactiveSamples', '#Samples',  'PValue', 'FDR', 'Tissue']
  report=report[cols]
  if SL_or_SDL=="SDL":
      report.columns= ['Overactive', 'OveractiveDB', 'SL_Candidate','#Overactive', '#Samples', 'PValue', 'FDR', 'Tissue']
  return report

  
def FunctionalExamination(client, SL_or_SDL, database, input_genes, percentile_threshold, cn_threshold, adj_method, fdr_level, tissues,  input_mutations=None):

    '''
      Description: Gene expression, Copy Number Alteration (CNA), Somatic Mutations (optional) are used to decide whether gene is inactive.
      The SL/SDL pair detection according to difference in gene effect/dependency score given one gene is inactive vs not-inactive

   Inputs:
    client:BigQueryClient, the BigQuery client that will run the function.
    SL_or_SDL:string, Synthetic lethal or Synthetic Dosage Lethal, valid values: 'SL', 'SDL'
    database: string, The dataresource the analysis will be performed on, 	valid values: "CRISPR", "shRNA"
    input_genes:list of strings, the list of genes whose SL/SDL partners will be seeked	
    percentile_threshold:double, the threshold for gene expression (for deciding whether a gene is inactive)
    cn_threshold:double, the threshold for copy number alteration (for deciding whether a gene is inactive)
    adj_method:	string,	optional, p value correction method,  valid_values:bonferroni,  sidak, holm-sidak , holm, simes-hochberg , hommel, fdr_bh,  fdr_by , fdr_tsbh, fdr_tsbky 
    fdr_level:string, the data that will be considered wile doing p value adjustment, valid values : "gene_level", "analysis_level"
    tissues: list of strings, the tissues that the analysis will be performed on. 
    input_mutations:list of strings, optional, valid values: "Missense_Mutation", "Nonsense_Mutation","Translation_Start_Site", "Frame_Shift_Ins", "Splice_Site",
    "In_Frame_Del","Frame_Shift_Del", "Nonstop_Mutation", "In_Frame_Ins"
        
   Output:
       A dataframe of SL/SDL pairs
    '''

       

    if database=='CRISPR':
 
        dep_score_table='isb-cgc-bq.DEPMAP.Achilles_gene_effect_DepMapPublic_current'
        sample_id='DepMap_ID'
        gene_exp='TPM'
        effect='Gene_Effect'
        symbol='Hugo_Symbol'
        selected_samples= RetrieveSamples(client, 'CRISPR', 'func_ex', tissues)
        ccle_samples=selected_samples
        ccle_sample_id='DepMap_ID'
        cid="DepMap_ID"

    elif database=='shRNA':
        dep_score_table='isb-cgc-bq.DEPMAP.Combined_gene_dep_score_DEMETER2_current'
        sample_id='CCLE_ID'
        gene_exp='TPM'
        effect='Combined_Gene_Dep_Score'
        symbol='Hugo_Symbol'
        selected_samples= RetrieveSamples(client, 'shRNA', 'func_ex', tissues)
        ccle_samples=selected_samples['DepMap_ID']
        shRNA_samples=selected_samples['CCLE_Name']
        ccle_sample_id='DepMap_ID'
        cid="CCLE_Name"
     

    else :
        print("The database name can be either CRISPR or shRNA")
        return()
    
    mutation_table='isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current'
    gene_exp_table='isb-cgc-bq.DEPMAP.CCLE_gene_expression_DepMapPublic_current'
    cn_table='isb-cgc-bq.DEPMAP.CCLE_gene_cn_DepMapPublic_current'
    sample_info_table='isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3'
    cn_threshold=np.log2(2**(cn_threshold)+1)
    gene_mapping=ProcessGeneAlias(client, input_genes, 'DepMap')

    min_sample_size=20
    if len(selected_samples)< (min_sample_size+1):
        print("Sample size needs to be greater than " +  str(min_sample_size) + ", it is " + str(len(selected_samples)))
        return()
    sql_without_mutation= """
    WITH
    table1 AS (
    (SELECT   symbol, Barcode FROM
    (SELECT GE.__SYMBOL__ AS symbol, GE.__CCLE_SAMPLE_ID__ AS Barcode ,
    PERCENT_RANK () over (partition by __SYMBOL__ order by __GENE_EXPRESSION__ asc) AS Percentile
    FROM  __GENE_EXP_TABLE__ GE
    WHERE GE.__SYMBOL__ in (__GENELIST__) AND __CCLE_SAMPLE_ID__ in (__SAMPLE_LIST_CCLE__) AND __GENE_EXPRESSION__ is not null ) AS NGE
    WHERE NGE.Percentile __GENE_CMP_STR__

    INTERSECT DISTINCT

    SELECT symbol,  Barcode FROM
    (SELECT CN.__SYMBOL__ AS symbol, CN.__CCLE_SAMPLE_ID__ AS Barcode,
    CN.CNA AS NORM_CN
    FROM  __CN_TABLE__ CN
    WHERE CN.__SYMBOL__ in (__GENELIST__) AND __CCLE_SAMPLE_ID__ in (__SAMPLE_LIST_CCLE__) and    CN.CNA is not null) AS NC
    WHERE NC.NORM_CN __CN_CMP_STR__  )"""


    sql_mutation_part="""  

    UNION DISTINCT
    SELECT M.__SYMBOL__  AS symbol , M.__CCLE_SAMPLE_ID__ AS Barcode
    FROM __MUTATION_TABLE__ M
    WHERE __SYMBOL__ IN (__GENELIST__) AND
    M.Variant_Classification IN (__MUTATIONLIST__) AND __CCLE_SAMPLE_ID__ in (__SAMPLE_LIST_CCLE__))"""


    rest_of_the_query= """
     , table2 AS (
    SELECT
        S.DepMap_ID Barcode,   __SYMBOL__ symbol,
        (RANK() OVER (PARTITION BY __SYMBOL__ ORDER BY __EFFECT__ ASC)) + (COUNT(*) OVER ( PARTITION BY __SYMBOL__, CAST(__EFFECT__ as STRING)) - 1)/2.0  AS rnkdata
    FROM
       __ACHILLES_TABLE__ A, __SAMPLE_INFO_TABLE__ S  
       where __SYMBOL__ IS NOT NULL AND __EFFECT__ IS NOT NULL AND  S.__REL_SAMPLE_ID__=A.__SAMPLE_ID__ AND S.DepMap_ID in (__SAMPLE_LIST_CCLE__)
       ),
summ_table AS (
SELECT
   n1.symbol as symbol1,
   n2.symbol as symbol2,
   COUNT( n1.Barcode) as n_1,
   SUM( n2.rnkdata )  as sumx_1,
FROM
   table1 AS n1
INNER JOIN
   table2 AS n2
ON
   n1.Barcode = n2.Barcode
GROUP BY
    symbol1, symbol2 ),

statistics AS (
SELECT symbol1, symbol2, n1, n, U1,
       (U1 - n1n2/2.0)/den as zscore
FROM (
   SELECT  symbol1, symbol2, n_t as n,
       n_1 as n1,
       sumx_1 - n_1 *(n_1 + 1) / 2.0 as U1,
       n_1 * (n_t - n_1 ) as n1n2,
       SQRT( n_1 * (n_t - n_1 )*(n_t + 1) / 12.0 ) as den
   FROM  summ_table as t1
   LEFT JOIN ( SELECT symbol, COUNT( Barcode ) as n_t
            FROM table2
            GROUP BY symbol)  t2
   ON symbol2 = symbol
   WHERE n_t > 20 and n_1>5
)
WHERE den > 0
)
SELECT symbol1, symbol2, n1, n, U1,
    `cgc-05-0042.functions.jstat_normal_cdf`(zscore, 0.0, 1.0 ) as pvalue
FROM statistics
GROUP BY 1,2,3,4,5,6
#HAVING pvalue <= 0.01
ORDER BY pvalue ASC """

    genes_intermediate_representation = ["'" +str(x)+"'"  for x in input_genes]
    input_genes_query= ','.join(genes_intermediate_representation)
    included_samples=["'"+ str(x) + "'" for x in selected_samples]
    included_samples= ','.join(included_samples)
    included_samples_ccle=["'"+ str(x) + "'" for x in ccle_samples]
    included_samples_ccle= ','.join(included_samples_ccle)


    if SL_or_SDL=='SDL' or input_mutations is None:
        sql_func_ex=sql_without_mutation +  ')' +' ' +  rest_of_the_query
    else:
        mutations_intermediate_representation = ["'"+x+"'" for x in input_mutations]
        input_mutations_for_query = ','.join(mutations_intermediate_representation)
        sql_func_ex=sql_without_mutation + ' '+ sql_mutation_part + ' ' +  rest_of_the_query
        sql_func_ex = sql_func_ex.replace('__MUTATION_TABLE__', mutation_table)
        sql_func_ex = sql_func_ex.replace('__MUTATIONLIST__', input_mutations_for_query)

    sql_func_ex = sql_func_ex.replace('__GENELIST__', input_genes_query)
    sql_func_ex = sql_func_ex.replace('__CUTOFFPRC__', str(percentile_threshold/100))
    sql_func_ex = sql_func_ex.replace('__CUTOFFSCNA__', str(cn_threshold))
    sql_func_ex = sql_func_ex.replace('__CN_TABLE__', cn_table)
    sql_func_ex = sql_func_ex.replace('__GENE_EXP_TABLE__', gene_exp_table)
    sql_func_ex = sql_func_ex.replace('__SAMPLE_ID__', sample_id)
    sql_func_ex = sql_func_ex.replace('__SYMBOL__', symbol)
    sql_func_ex = sql_func_ex.replace('__ACHILLES_TABLE__', dep_score_table)
    sql_func_ex = sql_func_ex.replace('__GENE_EXPRESSION__', gene_exp)
    sql_func_ex = sql_func_ex.replace('__EFFECT__', effect)
    sql_func_ex= sql_func_ex.replace('__SAMPLE_LIST__', included_samples)
    sql_func_ex= sql_func_ex.replace('__SAMPLE_LIST_CCLE__', included_samples_ccle)
    sql_func_ex= sql_func_ex.replace('__SAMPLE_INFO_TABLE__', sample_info_table)
    sql_func_ex = sql_func_ex.replace('__CCLE_SAMPLE_ID__', ccle_sample_id)
    sql_func_ex = sql_func_ex.replace('__REL_SAMPLE_ID__', cid)

    if SL_or_SDL=="SL":
      comp_str="<"+str(cn_threshold)
      com_gene_th="<"+str(percentile_threshold/100)

    elif SL_or_SDL=="SDL":
      comp_str=">"+str(cn_threshold)
      com_gene_th=">"+str(percentile_threshold/100)

    sql_func_ex= sql_func_ex.replace('__CN_CMP_STR__', comp_str)
    sql_func_ex= sql_func_ex.replace('__GENE_CMP_STR__', com_gene_th)

    results= client.query(sql_func_ex).result().to_dataframe()
    if results.shape[0]<1:
      print("Functional examimation inference procedure applied on " + database + " did not find candidate " + SL_or_SDL + " pairs.")
      return(results)
    
    report=results[['symbol1', 'symbol2', 'n1', 'n' ,'pvalue']]
    report=report.dropna()
    report.columns=['InactiveDB', 'SL_Candidate', '#InactiveSamples', '#Samples', 'PValue']
    report['Inactive']= report['InactiveDB'].map(gene_mapping)
    
    if fdr_level=="gene_level":
       inactive_genes=list(report["Inactive"].unique())
       for i in range(len(inactive_genes)):
          report.loc[report["Inactive"]==inactive_genes[i],'FDR']=multipletests(report.loc[report["Inactive"]==inactive_genes[i], 'PValue'], method= adj_method, is_sorted=False)[1]

    elif fdr_level=="analysis_level":
      FDR=multipletests(report['PValue'],  method= adj_method, is_sorted=False)[1]
      report['FDR']=FDR
    else:
      print("FDR level can be either gene_level or analysis_level")
      return()
 
    report['Tissue']=str(tissues)
    cols=['Inactive', 'InactiveDB', 'SL_Candidate','#InactiveSamples', '#Samples', 'PValue', 'FDR', 'Tissue']
    report=report[cols]
    if SL_or_SDL=="SDL":
      report.columns= ['Overactive', 'OveractiveDB', 'SL_Candidate','#Overactive', '#Samples', 'PValue', 'FDR', 'Tissue']
    return report

def UnionResults(results, SL_or_SDL, labels, tissues):
    '''
    Description: This functions merges results from the same inference procedure applied on different datasets.
    Inputs:
        results: list of dataframes, the output of inference procedure applied on different datasets,
        SL_or_SDL:string, Synthetic lethal or Synthetic Dosage Lethal, valid values: 'SL', 'SDL'
        labels:string, the column names to be used,valid values: 'PValue', 'FDR'
        tissues: list of strings, the tissues that the analysis will be performed on.

    Output:
         A dataframe o merged results
    '''
    inds=[]
    for i in range(len(results)):
        if results[i].shape[0]<1:
            inds.append(i)
            
    indices = sorted(inds, reverse=True)
    for idx in indices:
        if idx < len(results):
            results.pop(idx)
    for i in range(len(results)):
        results[i].reset_index(inplace=True, drop=True)
        results[i].rename(columns = {labels[i]:labels[i]+ str(i)}, inplace = True)
    
    combined_results=results[0]
    for i in range(1,len(results)):
        if SL_or_SDL=="SL":
            combined_results =pd.merge(combined_results, results[i], on = ['Inactive',  'SL_Candidate'], how = 'outer')
        elif SL_or_SDL=="SDL":
            combined_results =pd.merge(combined_results, results[i], on = ['Overactive',  'SL_Candidate'], how = 'outer')

    rel_cols=combined_results.columns[np.array([x.startswith(labels[i]) for x in combined_results.columns])]
    p_matrix=combined_results[rel_cols]

    combined_results["Tissue"]=str(tissues)
    if SL_or_SDL=="SL":
        inc_cols= ['Inactive', 'SL_Candidate'] +  list(rel_cols) +['Tissue']
    elif SL_or_SDL=="SDL":
       inc_cols= ['Overactive', 'SL_Candidate'] +  list(rel_cols) + ['Tissue']

    return(combined_results[inc_cols])

def MergeResults(results, SL_or_SDL, tissues):
    '''
  Description: This function merges results from SoF, Coexpression and Functional Examination procedures
  Inputs:
    results: list of dataframes, the output of inference procedure applied on different datasets,
    SL_or_SDL:string, Synthetic lethal or Synthetic Dosage Lethal, valid values: 'SL', 'SDL'
    tissues: list of strings, the tissues that the analysis will be performed on.
 Output:
    A dataframe o merged results
    '''
      
    inds=[]
    for i in range(len(results)):
        if results[i].shape[0]<1:
            inds.append(i)
    if len(inds)>0 :
        print("At least one of the inference procedure did not return results")
        print("No SL pairs found by every pipeline")
        return()
    indices = sorted(inds, reverse=True)
    for idx in indices:
        if idx < len(results):
            results.pop(idx)
    for i in range(len(results)):
        results[i].reset_index(inplace=True, drop=True)

    combined_results=results[0]
    for i in range(1,len(results)):
        if SL_or_SDL=="SL":
            combined_results =pd.merge(combined_results, results[i], on = ['Inactive',  'SL_Candidate'], how = 'inner')
        elif SL_or_SDL=="SDL":
            combined_results =pd.merge(combined_results, results[i], on = ['Overactive',  'SL_Candidate'], how = 'inner')

    combined_results["Tissue"]=str(tissues)

    if SL_or_SDL=="SL":
        inc_cols= ['Inactive', 'SL_Candidate'] 
    elif SL_or_SDL=="SDL":
        inc_cols= ['Overactive', 'SL_Candidate']
    return(combined_results[inc_cols])

