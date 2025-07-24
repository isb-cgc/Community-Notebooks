set_queries={}


set_queries["hm1"]= {"sql": '''SELECT project_short_name, sample_barcode, HGNC_gene_symbol, normalized_count
FROM `isb-cgc.TCGA_hg19_data_v0.RNAseq_Gene_Expression_UNC_RSEM`
WHERE project_short_name IN ('TCGA-KIRC', 'TCGA-GBM')
AND HGNC_gene_symbol IN UNNEST(@genelist) 
GROUP BY 1,2,3,4''', "params":["genelist"] }

