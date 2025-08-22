from google.cloud import bigquery
from google.oauth2.credentials import Credentials

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


query_fragments={}

query_fragments["difexp_caseq"]= """WITH rna as (
    SELECT
       case_barcode,
       sample_barcode,
       aliquot_barcode,
       Ensembl_gene_id_v,
       gene_name,
       unstranded,
       fpkm_uq_unstranded,
       sample_type_name,
    FROM `isb-cgc-bq.TCGA_versioned.RNAseq_hg38_gdc_r35`
    WHERE gene_type = 'protein_coding'
    AND project_short_name = '@proj_nm'
),
cases as (
  SELECT case_barcode, agg FROM
      (SELECT
        case_barcode,
        array_agg(distinct sample_type_name) agg
      FROM rna
      GROUP BY case_barcode)
  WHERE array_length(agg) > 1
  AND ("Solid Tissue Normal" in UNNEST(agg))
  )"""

query_fragments["difexp_scase"]="""SELECT * FROM cases"""

query_fragments["difexp_expq"]= """,
mean_expr as (
  SELECT * FROM (
    SELECT
      rna.Ensembl_gene_id_v,
      VARIANCE(rna.fpkm_uq_unstranded) var_fpkm
    FROM rna
    JOIN cases ON rna.case_barcode = cases.case_barcode
    WHERE rna.sample_type_name = 'Solid Tissue Normal'
    GROUP BY rna.Ensembl_gene_id_v)
  ORDER BY var_fpkm DESC
  LIMIT 2000)"""

query_fragments["difexp_selgenes"]="""
SELECT * FROM mean_expr
"""




set_queries={}


set_queries["hm1"]= {"sql": '''SELECT project_short_name, sample_barcode, HGNC_gene_symbol, normalized_count
FROM `isb-cgc.TCGA_hg19_data_v0.RNAseq_Gene_Expression_UNC_RSEM`
WHERE project_short_name IN ('TCGA-KIRC', 'TCGA-GBM')
AND HGNC_gene_symbol IN UNNEST(@genelist) 
GROUP BY 1,2,3,4''', "params":["genelist"] }

set_queries["hm2"] = {"sql": '''SELECT * FROM `isb-cgc.TCGA_hg19_data_v0.RNAseq_Gene_Expression_UNC_RSEM` WHERE project_short_name IN ('TCGA-KIRC', 'TCGA-GBM')
AND HGNC_gene_symbol IN ('ACVR1','APC')''' }

