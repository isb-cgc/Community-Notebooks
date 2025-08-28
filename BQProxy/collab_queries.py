from google.cloud import bigquery
from google.oauth2.credentials import Credentials
import os

api_endpoint = "https://bqproxy-dot-isb-cgc-dev-1.uc.r.appspot.com/bqproxy"
demo_mode = True

def demo_client_args():
    if demo_mode:
        ret = {"credentials": Credentials(token='dummy', expiry=None),
               "client_options": {"api_endpoint": api_endpoint}}
    else:
        ret = {}
    return ret

def demo_job_config_arg(query_id, job_config=None, demo_query_params=[]):
    if demo_mode:
        if job_config is None:
            job_config = bigquery.QueryJobConfig()
        new_params = list(job_config.query_parameters or [])
        new_params.append(bigquery.ScalarQueryParameter("queryid", "STRING", query_id))
        new_params.extend(*[demo_query_params])
        job_config.query_parameters = new_params
    ret = {"job_config": job_config}
    return ret



set_queries={}


set_queries["hm1"]= {"sql": '''SELECT project_short_name, sample_barcode, HGNC_gene_symbol, normalized_count
FROM `isb-cgc.TCGA_hg19_data_v0.RNAseq_Gene_Expression_UNC_RSEM`
WHERE project_short_name IN ('TCGA-KIRC', 'TCGA-GBM')
AND HGNC_gene_symbol IN UNNEST(@genelist) 
GROUP BY 1,2,3,4''', "params":["genelist"], "tests": [{"genelist":{"val":['APC'], "type":"strA"}}], "nb": "How_to_make_a_heatmap_using_BigQuery.ipynb"}


set_queries["qsg1"] = {"sql": '''SELECT
    proj__project_id,
    submitter_id,
    proj__name
  FROM
    `isb-cgc-bq.TCGA_versioned.clinical_gdc_r37`
  LIMIT
    5''', "nb":"Quick_Start_Guide_to_ISB_CGC", "tests":[{}] }

set_queries["tt"]={"sql" :'''SELECT * from `isb-cgc-bq.targetome_versioned.interactions_v1` where lower(targetName) = lower(@target_name)''', "nb":"test"
                   , "params":["target_name"], "tests": [{"target_name":{"val":"MS4A1", "type":"str"}}]}



set_queries["tr1"] = {"sql": '''SELECT
    inter.targetName,
    inter.drugName,
    src.PubMedID

  FROM
    `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter

  INNER JOIN `isb-cgc-bq.targetome_versioned.sources_v1` AS src
    -- link interactions to literature sources
    ON inter.sourceID = src.sourceID

  INNER JOIN `isb-cgc-bq.targetome_versioned.target_synonyms_v1` AS targsyn
    -- filter for interactions that match target
    ON inter.targetID = targsyn.targetID

  WHERE
    LOWER(targsyn.synonym) = LOWER(@target_name)

  ORDER BY drugName ASC''', "params":["target_name"], "tests": [{"target_name":{"val":"MS4A1", "type":"str"}}],
                      "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}



set_queries["tr2"] = {"sql": '''SELECT
    DISTINCT
      inter.interactionID,
      inter.drugName,
      inter.targetName

  FROM
    `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter

  INNER JOIN `isb-cgc-bq.targetome_versioned.experiments_v1` AS exp
    -- filter for interactions with experiments
    ON inter.expID = exp.expID

  WHERE
    -- filter for exact binding evidence
    exp.exp_assayType IS NOT NULL
    AND exp.exp_assayRelation = '='

    -- filter for only human targets
    AND inter.targetSpecies = 'Homo sapiens'

  ORDER BY
    targetName ASC,
    drugName ASC''', "tests":[{}], "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}


set_queries["tr3"] = {"sql": '''SELECT
    DISTINCT
      inter.* EXCEPT (sourceID),
      exp.exp_assayType,
      exp.exp_assayValueMedian

  FROM
    `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter

  INNER JOIN `isb-cgc-bq.targetome_versioned.experiments_v1` AS exp
    -- filter for interactions with experimental evidence
    ON inter.expID = exp.expID

  INNER JOIN `isb-cgc-bq.targetome_versioned.drug_synonyms_v1` AS drugsyn
    -- filter for interactions matching drug id
    ON inter.drugID = drugsyn.drugID

  WHERE
    -- filter by drug name
    LOWER(drugsyn.synonym) = LOWER(@drug_name)

    -- make sure that all assay ranges are at or below 100nM
    AND exp.exp_assayValueMedian <= 100
    AND (exp.exp_assayValueLow <= 100 OR exp.exp_assayValueLow is null)
    AND (exp.exp_assayValueHigh <= 100 OR exp.exp_assayValueHigh is null)

    -- make sure the assay type is known (KD, Ki, IC50, or EC50)
    AND exp.exp_assayType IS NOT NULL
    AND exp.exp_assayRelation = '='

    -- limit to just experiments in humans
    AND inter.targetSpecies = 'Homo sapiens'

  ORDER BY inter.targetName ASC''', "params":["drug_name"], "tests": [{"drug_name":{"val":"imatinib", "type":"str"}}],
                      "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}


set_queries["tr4"] = {"sql": '''SELECT
    DISTINCT pathway.*

  FROM
    `isb-cgc-bq.reactome_versioned.pathway_v77` as pathway

  INNER JOIN `isb-cgc-bq.reactome_versioned.pe_to_pathway_v77` as pe2pathway
    -- link pathways to physical entities via intermediate table
    ON pathway.stable_id = pe2pathway.pathway_stable_id

  INNER JOIN `isb-cgc-bq.reactome_versioned.physical_entity_v77` AS pe
    -- link pathways to physical entities
    ON pe2pathway.pe_stable_id = pe.stable_id

  INNER JOIN `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter
    -- link physical entities to interactions
    ON pe.uniprot_id = inter.target_uniprotID

  INNER JOIN `isb-cgc-bq.targetome_versioned.experiments_v1` AS exp
    -- link interactions to experiments
    ON inter.expID = exp.expID

  INNER JOIN `isb-cgc-bq.targetome_versioned.drug_synonyms_v1` AS drugsyn
    -- filter for interactions matching drug id
    ON inter.drugID = drugsyn.drugID

  WHERE
    -- filter by drug name
    LOWER(drugsyn.synonym) = LOWER(@drug_name)

    -- make sure that all assay ranges are at or below 100nM
    AND exp.exp_assayValueMedian <= 100
    AND (exp.exp_assayValueLow <= 100 OR exp.exp_assayValueLow is null)
    AND (exp.exp_assayValueHigh <= 100 OR exp.exp_assayValueHigh is null)

    -- make sure the assay type is known (KD, Ki, IC50, or EC50)
    AND exp.exp_assayType IS NOT NULL
    AND exp.exp_assayRelation = '='

    -- limit to just experiments in humans
    AND inter.targetSpecies = 'Homo sapiens'

    -- filter by stronger evidence: "Traceable Author Statement"
    AND pe2pathway.evidence_code = 'TAS'
  ORDER BY pathway.name ASC''', "params":["drug_name"], "tests": [{"drug_name":{"val":"imatinib", "type":"str"}}],
                      "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}


set_queries["tr5"] = {"sql": '''SELECT
    DISTINCT pathway.*

  FROM
    `isb-cgc-bq.reactome_versioned.pathway_v77` as pathway

  INNER JOIN `isb-cgc-bq.reactome_versioned.pe_to_pathway_v77` as pe2pathway
    -- link pathways to physical entities via intermediate table
    ON pathway.stable_id = pe2pathway.pathway_stable_id

  INNER JOIN `isb-cgc-bq.reactome_versioned.physical_entity_v77` AS pe
    -- link pathways to physical entities
    ON pe2pathway.pe_stable_id = pe.stable_id

  INNER JOIN `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter
    -- link physical entities to interactions
    ON pe.uniprot_id = inter.target_uniprotID

  INNER JOIN `isb-cgc-bq.targetome_versioned.experiments_v1` AS exp
    -- link interactions to experiments
    ON inter.expID = exp.expID

  INNER JOIN `isb-cgc-bq.targetome_versioned.drug_synonyms_v1` AS drugsyn
    -- filter for interactions matching drug id
    ON inter.drugID = drugsyn.drugID

  WHERE
    -- filter by drug name
    LOWER(drugsyn.synonym) = LOWER(@drug_name)

    -- make sure that all assay ranges are at or below 100nM
    AND exp.exp_assayValueMedian <= 100
    AND (exp.exp_assayValueLow <= 100 OR exp.exp_assayValueLow is null)
    AND (exp.exp_assayValueHigh <= 100 OR exp.exp_assayValueHigh is null)

    -- make sure the assay type is known (KD, Ki, IC50, or EC50)
    AND exp.exp_assayType IS NOT NULL
    AND exp.exp_assayRelation = '='

    -- limit to just experiments in humans
    AND inter.targetSpecies = 'Homo sapiens'

    -- filter by stronger evidence: "Traceable Author Statement"
    AND pe2pathway.evidence_code = 'TAS'

    -- filter to include just lowest level pathways
    AND pathway.lowest_level in UNNEST(@lowest_level)
  ORDER BY pathway.name ASC''', "params":["drug_name", "lowest_level"],
                      "tests": [{"drug_name":{"val":"imatinib", "type":"str"}, "lowest_level":{"val":[True, False, None], "type":"boolA"}},
                                {"drug_name":{"val":"imatinib", "type":"str"}, "lowest_level":{"val":[True], "type":"boolA"}}],
                      "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}

set_queries["tr6"]={"sql":'''

WITH
    target_list_query AS (
      -- Table that contains a list of all distinct targets of the drug
      SELECT
        DISTINCT inter.target_uniprotID
    
      FROM
        `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter
    
      INNER JOIN `isb-cgc-bq.targetome_versioned.drug_synonyms_v1` AS drugsyn
        -- filter for interactions matching drug id
        ON inter.drugID = drugsyn.drugID 
    
      INNER JOIN `isb-cgc-bq.targetome_versioned.experiments_v1` AS exp
        -- filter for interactions with experimental evidence
        ON inter.expID = exp.expID 
    
      INNER JOIN `isb-cgc-bq.reactome_versioned.physical_entity_v77` AS pe
        -- filter for interactions with targets that match a reactome
        -- physical entity
        ON inter.target_uniprotID = pe.uniprot_id
    
      WHERE
        -- filter by drug name
        LOWER(drugsyn.synonym) = LOWER(@drug_name)
    
        -- make sure that all assay ranges are at or below 100nM
        AND exp.exp_assayValueMedian <= 100
        AND (exp.exp_assayValueLow <= 100 OR exp.exp_assayValueLow is null)
        AND (exp.exp_assayValueHigh <= 100 OR exp.exp_assayValueHigh is null)
    
        -- make sure the assay type is known (KD, Ki, IC50, or EC50)
        AND exp.exp_assayType IS NOT NULL
        AND exp.exp_assayRelation = '='
    
        -- limit to just experiments in humans
        AND inter.targetSpecies = 'Homo sapiens'
    ),

    target_pp_query AS (
      -- Table that maps pathways to the total number of drug targets within that pathway
      SELECT
        COUNT(DISTINCT target_list_query.target_uniprotID) as num_targets,
        pathway.stable_id,
        pathway.name
    
      FROM
        target_list_query
    
      INNER JOIN `isb-cgc-bq.reactome_versioned.physical_entity_v77` AS pe
        -- filter for interactions with targets that match a reactome
        -- physical entity
        ON target_list_query.target_uniprotID = pe.uniprot_id
    
      INNER JOIN `isb-cgc-bq.reactome_versioned.pe_to_pathway_v77` AS pe2pathway
        -- link physical entities to pathways via intermediate table
        ON pe.stable_id = pe2pathway.pe_stable_id
    
      INNER JOIN `isb-cgc-bq.reactome_versioned.pathway_v77` AS pathway
        -- link physical entities to pathways
        ON pe2pathway.pathway_stable_id = pathway.stable_id
    
      WHERE
        -- filter by stronger evidence: "Traceable Author Statement" 
        pe2pathway.evidence_code = 'TAS'
    
      GROUP BY pathway.stable_id, pathway.name
      ORDER BY num_targets DESC
    ),

    not_target_list_query AS (
      -- Table that contains a list of all proteins that are NOT targets of the drug
      -- This query depends on "target_list_query", which is created by a previous
      -- query.
      SELECT
        DISTINCT inter.target_uniprotID AS target_uniprotID
    
      FROM `isb-cgc-bq.targetome_versioned.interactions_v1` AS inter
    
      WHERE
        inter.targetSpecies = 'Homo sapiens'
        
        AND inter.target_uniprotID NOT IN (
          SELECT target_uniprotID FROM target_list_query
        )
    ),

    not_target_pp_query AS (
      -- Table that maps pathways to the number of proteins that are NOT drug
      -- targets in that pathway.
      SELECT
        COUNT(DISTINCT not_target_list_query.target_uniprotID) AS num_not_targets,
        pathway.stable_id,
        pathway.name
    
      FROM not_target_list_query
    
      INNER JOIN `isb-cgc-bq.reactome_versioned.physical_entity_v77` AS pe
        ON not_target_list_query.target_uniprotID = pe.uniprot_id
    
      INNER JOIN `isb-cgc-bq.reactome_versioned.pe_to_pathway_v77` AS pe2pathway
        ON pe.stable_id = pe2pathway.pe_stable_id
      
      INNER JOIN `isb-cgc-bq.reactome_versioned.pathway_v77` AS pathway
        ON pe2pathway.pathway_stable_id = pathway.stable_id
    
      WHERE
        -- filter by stronger evidence: "Traceable Author Statement" 
        pe2pathway.evidence_code = 'TAS'
    
      GROUP BY pathway.stable_id, pathway.name
      ORDER BY num_not_targets DESC
    ),

    target_count_query AS (
      -- Table that contains the counts of # of proteins that are/are not targets
      SELECT
        target_count,
        not_target_count,
        target_count + not_target_count AS total_count
    
      FROM 
        (SELECT COUNT(*) AS target_count FROM target_list_query),
        (SELECT COUNT(*) AS not_target_count FROM not_target_list_query)
    ),

    observed_query AS (
      -- Table with observed values per pathway in the contingency matrix
      SELECT
        target_pp_query.num_targets AS in_target_in_pathway,
        not_target_pp_query.num_not_targets AS not_target_in_pathway,
        target_count_query.target_count - target_pp_query.num_targets AS in_target_not_pathway,
        target_count_query.not_target_count - not_target_pp_query.num_not_targets AS not_target_not_pathway,
        target_pp_query.stable_id,
        target_pp_query.name
    
      FROM 
        target_pp_query,
        target_count_query
    
      INNER JOIN not_target_pp_query
        ON target_pp_query.stable_id = not_target_pp_query.stable_id
    ),

    sum_query AS (
      -- Table with summed observed values per pathway in the contingency matrix
      SELECT
        observed_query.in_target_in_pathway + observed_query.not_target_in_pathway AS pathway_total,
        observed_query.in_target_not_pathway + observed_query.not_target_not_pathway AS not_pathway_total,
        observed_query.in_target_in_pathway + observed_query.in_target_not_pathway AS target_total,
        observed_query.not_target_in_pathway + observed_query.not_target_not_pathway AS not_target_total,
        observed_query.stable_id,
        observed_query.name
    
      FROM
        observed_query
    ),

    expected_query AS (
      -- Table with the expected values per pathway in the contingency matrix
      SELECT 
        sum_query.target_total * sum_query.pathway_total / target_count_query.total_count AS exp_in_target_in_pathway,
        sum_query.not_target_total * sum_query.pathway_total / target_count_query.total_count AS exp_not_target_in_pathway,
        sum_query.target_total * sum_query.not_pathway_total / target_count_query.total_count AS exp_in_target_not_pathway,
        sum_query.not_target_total * sum_query.not_pathway_total / target_count_query.total_count AS exp_not_target_not_pathway,
        sum_query.stable_id,
        sum_query.name
    
      FROM 
        sum_query, target_count_query
    ),
    
    chi_squared_query AS (
      -- Table with the chi-squared statistic for each pathway
      SELECT
        -- Chi squared statistic with Yates' correction
        POW(ABS(observed_query.in_target_in_pathway - expected_query.exp_in_target_in_pathway) - 0.5, 2) / expected_query.exp_in_target_in_pathway 
        + POW(ABS(observed_query.not_target_in_pathway - expected_query.exp_not_target_in_pathway) - 0.5, 2) / expected_query.exp_not_target_in_pathway
        + POW(ABS(observed_query.in_target_not_pathway - expected_query.exp_in_target_not_pathway) - 0.5, 2) / expected_query.exp_in_target_not_pathway
        + POW(ABS(observed_query.not_target_not_pathway - expected_query.exp_not_target_not_pathway) - 0.5, 2) / expected_query.exp_not_target_not_pathway
        AS chi_squared_stat,
        observed_query.stable_id,
        observed_query.name
    
      FROM observed_query
    
      INNER JOIN expected_query
        ON observed_query.stable_id = expected_query.stable_id
    )

  SELECT
    observed_query.in_target_in_pathway,
    observed_query.in_target_not_pathway,
    observed_query.not_target_in_pathway,
    observed_query.not_target_not_pathway,
    chi_squared_query.chi_squared_stat,
    chi_squared_query.stable_id,
    chi_squared_query.name

  FROM chi_squared_query

  INNER JOIN observed_query
    ON chi_squared_query.stable_id = observed_query.stable_id
  
  INNER JOIN `isb-cgc-bq.reactome_versioned.pathway_v77` AS pathway
    ON chi_squared_query.stable_id = pathway.stable_id

  WHERE pathway.lowest_level in UNNEST(@lowest_level)

  ORDER BY chi_squared_stat DESC

''', "params":["drug_name", "lowest_level"],
                    "tests": [{"drug_name":{"val":"sorafenib", "type":"str"}, "lowest_level":{"val":[True, False, None], "type":"boolA"}},
{"drug_name":{"val":"sorafenib", "type":"str"}, "lowest_level":{"val":[True], "type":"boolA"}}],
                      "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}


set_queries["tr7"]={"sql":'''SELECT
             COUNT (*) AS num_pathways
          FROM
             `isb-cgc-bq.reactome_versioned.pathway_v77` as pathway 
             WHERE lowest_level in UNNEST(@lowest_level)
             ''', "params":["lowest_level"], "tests":[{"lowest_level":{"val":[True, False, None], "type":"boolA"}},
                                                                       {"lowest_level":{"val":[True], "type":"boolA"}}],
                     "nb":"How_to_use_the_Targetome_and_Reactome_BQ_datasets"}



if __name__== '__main__':
    project_id = os.environ["PROJECT_ID"]
    credentials_file_needed = ((os.environ["CREDENTIALS_FILE_NEEDED"]).lower() == "true")
    if credentials_file_needed:
        credentials_file = os.environ['CREDENTIALS_FILE']
        client = bigquery.Client.from_service_account_json(credentials_file)

    else:
        client = bigquery.Client(project=project_id)

    for queryid in set_queries:
        sql = set_queries[queryid]['sql']
        nb = set_queries[queryid]['nb']
        for testnum in range(len(set_queries[queryid]["tests"])):
            job_config = None
            if "params" in set_queries[queryid]:
                query_params=[]
                for param in set_queries[queryid]["params"]:
                    if param in set_queries[queryid]["tests"][testnum]:
                        param_val = set_queries[queryid]["tests"][testnum][param]["val"]
                        ptype = set_queries[queryid]["tests"][testnum][param]["type"]
                        if ptype=="str":
                            query_param = bigquery.ScalarQueryParameter(param, "STRING",param_val)
                        elif ptype=="strA":
                            query_param = bigquery.ArrayQueryParameter(param, "STRING", param_val)
                        elif ptype =="int":
                            query_param = bigquery.ScalarQueryParameter(param, "INT64", param_val)
                        elif ptype =="intA":
                            query_param = bigquery.ArrayQueryParameter(param, "INT64", param_val)
                        elif ptype == "bool":
                            query_param = bigquery.ScalarQueryParameter(param, "BOOL", param_val)
                        elif ptype == "boolA":
                            query_param = bigquery.ArrayQueryParameter(param, "BOOL", param_val)

                        query_params.append(query_param)
                if (len(query_params)>0):

                    job_config = bigquery.QueryJobConfig(query_parameters = query_params)
            if queryid =="tr7":
                try:
                    res=client.query(sql, job_config).result()
                    sz = len(list(res))
                    print(f"query id successful {queryid} with testnum {testnum}. Num rows is {sz}")
                except Exception as e:
                    print(f"error with query {queryid}: {e} ")









