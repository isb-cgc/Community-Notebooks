from google.cloud import bigquery
import pandas as pd
from scipy import stats 
import statsmodels.stats.multitest as multi
import numpy as np

## The GeneSymbol_standardization function will convert all non-standarized gene list to approved gene symbols.###
def GeneSymbol_standardization(Gene_list,project_id):
    client = bigquery.Client(project_id)
    #query='''
    #    SELECT *
    #    FROM  `syntheticlethality.gene_information.gene_info_human`
    #    where Gene in UNNEST(@input_gene_list)
    #    '''
    query='''
        SELECT *
        FROM  `isb-cgc-bq.synthetic_lethality.gene_info_human_HGNC_NCBI_2020_07`
        where Gene in UNNEST(@input_gene_list)
        '''
    job_config = bigquery.QueryJobConfig(
    query_parameters=[
            bigquery.ArrayQueryParameter("input_gene_list", "STRING", Gene_list)
        ]
        )

    id_map = client.query(query,  job_config=job_config).result().to_dataframe()

    Gene_list_all = list(set(list(id_map['Alias'].values) + list(id_map['Gene'].values) ))


    #query1 = ''' 
    #            select Hugo_Symbol
    #            from `syntheticlethality.DepMap_public_20Q3.CCLE_mutation`
    #            where Hugo_Symbol in UNNEST(@input_gene_list_new)
    #            '''
    
    query1 = ''' 
                select Hugo_Symbol
                from `isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current`
                where Hugo_Symbol in UNNEST(@input_gene_list_new)
                '''
    job_config = bigquery.QueryJobConfig(
    query_parameters=[
            bigquery.ArrayQueryParameter("input_gene_list_new", "STRING", Gene_list_all)
        ]
        )

    Mut_mat = client.query(query1, job_config=job_config).result().to_dataframe()
    set_gene_CCLE = set(Mut_mat['Hugo_Symbol'])

    dic_gene_to_alias = {}
    output_gene_list = []
    for Gene in Gene_list:
        dic_gene_to_alias[Gene] = set(id_map.loc[id_map['Gene'] == Gene]['Alias']).intersection(set_gene_CCLE)
        if Gene in set(id_map['Gene']) and Gene in dic_gene_to_alias[Gene]:
            output_gene_list.append(Gene)
        else:
            print(Gene + ":" + ','.join(list(dic_gene_to_alias[Gene])))
            for value in dic_gene_to_alias[Gene]:
                if value in set(id_map['Alias']):
                    output_gene_list.append(value) 
            
    return(dic_gene_to_alias, output_gene_list)

## The GeneSymbol_standardization_output function will convert all non-standarized gene list to approved gene symbols in the output file.###
def GeneSymbol_standardization_output(Gene_list,project_id):
    Gene_list = list(set(Gene_list))
    client = bigquery.Client(project_id)
    #query='''
    #    SELECT *
    #    FROM  `syntheticlethality.gene_information.gene_info_human`
    #    where Gene in UNNEST(@input_gene_list)
    #    '''

    query='''
        SELECT *
        FROM  `isb-cgc-bq.synthetic_lethality.gene_info_human_HGNC_NCBI_2020_07`
        where Gene in UNNEST(@input_gene_list)
        '''
    job_config = bigquery.QueryJobConfig(
    query_parameters=[
            bigquery.ArrayQueryParameter("input_gene_list", "STRING", Gene_list)
        ]
        )

    id_map = client.query(query,  job_config=job_config).result().to_dataframe()
    alias_list = list(id_map['Alias'].values)
    gene_list = list(id_map['Gene'].values) 

    dic_alias_to_gene = {}
    
    for i in range(0,len(alias_list)):
        dic_alias_to_gene[alias_list[i]] = gene_list[i]
    
    return(dic_alias_to_gene)

## Get sample information from the CCLE dataset; version (Depmap 20Q3). 
def get_ccle_sample_info(project_id):
    client = bigquery.Client(project_id)
    #query = ''' 
    #        SELECT DepMap_ID, CCLE_Name,primary_disease,TCGA_subtype
    #        FROM `syntheticlethality.DepMap_public_20Q3.sample_info_Depmap_withTCGA_labels` 
    #        '''
    query = ''' 
            SELECT DepMap_ID, CCLE_Name,primary_disease,TCGA_subtype
            FROM `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` 
            '''
    sample_info = client.query(query).result().to_dataframe()
    return(sample_info)

## Get gene mutation matrix from the CCLE dataset; version (Depmap 20Q3). 
def get_ccle_mutation_data(project_id):
    client = bigquery.Client(project_id)    
    #Mutation matrix
    #query = ''' 
    #        select Hugo_Symbol,DepMap_ID,Variant_Classification 
    #        from `syntheticlethality.DepMap_public_20Q3.CCLE_mutation`
    #        '''
    #Mut_mat = client.query(query).result().to_dataframe()
    query = ''' 
            select Hugo_Symbol,DepMap_ID,Variant_Classification 
            from `isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current`
            '''
    Mut_mat = client.query(query).result().to_dataframe()
    return(Mut_mat)

## Get gene gene knockout effects from CRISPR dataset in Depmap data portal; version (Depmap 20Q3). 
def get_depmap_crispr_data(project_id):
    import requests
    from io import StringIO

    url = "https://ndownloader.figshare.com/files/24613292"
    req = requests.get(url)
    data = StringIO(req.text)

    Depmap_matrix = pd.read_csv(data )
    Depmap_matrix.index = Depmap_matrix['DepMap_ID']
    Depmap_matrix = Depmap_matrix.drop(['DepMap_ID'], axis=1)
    
    gene_names_old = list(Depmap_matrix.columns.values)
    gene_names_new = []
    for item in gene_names_old:
        name = item.split(' (')[0]
        gene_names_new.append(name)
    Depmap_matrix.columns = gene_names_new

    return(Depmap_matrix)

## Get gene gene down effects from shRNA dataset in Depmap data portal; version (Demeter). 
def get_demeter_shRNA_data(project_id):
    import requests
    from io import StringIO
    url = "https://ndownloader.figshare.com/files/13515395"
    req = requests.get(url)
    data = StringIO(req.text)
    
    Depmap_matrix = pd.read_csv(data )
    
    gene_names_new = []
    for item in list(Depmap_matrix['Unnamed: 0']):
        name = item.split(' (')[0]
        gene_names_new.append(name)
    Depmap_matrix.index = gene_names_new
    
    sample_info = get_ccle_sample_info(project_id)
    sample_map = {}
    for i in range(0, sample_info.shape[0]):
        Depmap_id = sample_info.iloc[i,0]
        CCLE_Name = sample_info.iloc[i,1]
        sample_map[CCLE_Name]  = Depmap_id

    Matched_cellLines = []
    for CCLE_Name in list(Depmap_matrix.columns):
        if CCLE_Name not in sample_map:
            print(CCLE_Name)
        else:
            Matched_cellLines.append(CCLE_Name)        
    Depmap_matrix_sele = Depmap_matrix.loc[:,Matched_cellLines]
    ACH_ID_list = []
    for CCLE_Name in list(Depmap_matrix_sele.columns):
        if CCLE_Name not in sample_map:
            print(CCLE_Name)
        else:
            ACH_ID_list.append(sample_map[CCLE_Name])
    Depmap_matrix_sele.columns = ACH_ID_list 
    Depmap_matrix_sele = Depmap_matrix_sele.transpose()
    return(Depmap_matrix_sele)

def Mutational_based_SL_pipeline(tumor_type, mut_gene, Mut_mat, Depmap_matrix, datatype,project_id ):
    """
    Description: The mutation-dependent synthetic lethality prediction (MDSLP) workflow is based on the rationale that, 
    for tumors with mutations that have an impact on protein expression or structure (functional mutation), 
    the knockout effects or inhibition of a partner target gene show conditional dependence for the mutated molecular entities. 
    Leveraging the public cancer cell line datasets including gene mutation data from CCLE, and functional screening data generated 
    by either shRNA or CRISPR technology from DepMap (Dempster et al., 2019; Ghandi et al., 2019; McFarland et al., 2018; Meyers et al., 2017), 
    we integrated these data modalities to evaluate mutation-based conditional dependence. 

    The MDSLP is based on genetic variants, gene-dependency scores, or gene effects from the cancer cell line data in the DepMap Portal. 
    The genomic variants data from the CCLE project, gene-dependency scores estimated from CERES for CRISPR-Cas9 essentiality screening 
    from project Achilles [32] and gene-dependency scores estimated from DEMETER2 from three large RNAi screening datasets  were used. 
    We developed a pipeline that integrates the genetic information and the functional screening data to evaluate mutation-based conditional dependence, 
    using either the CRISPR or the shRNA dataset. For this pipeline, tumor types can be selected by the users. The variants selected for this pipeline 
    include those that alter the amino acid in the protein structures or protein expression which may further impact the function of the gene product. 
    These alterations include Splice_Site, Frame_Shift_Del, Frame_Shift_Ins, Nonstop_Mutation, In_Frame_Del,  In_Frame_Ins, Missense_Mutation, 
    Nonsense_Mutation, Nonstop_Mutation, Start_Codon_Del,  Start_Codon_Ins, Start_Codon_SNP, Stop_Codon_Del, Stop_Codon_Del, Stop_Codon_Ins, 
    and De_novo_Start_OutOfFrame. 

    For the CRISPR data-based pipeline, we used CCLE mutation, Achilles gene effect, and sample_info data from DepMap (version 20Q3).
    After selecting tumor types, or the pan-cancer analysis option, for each selected mutated gene, we grouped the cell lines into 
    either the mutated or the wild-type group, then tested whether the knockout effects or the gene dependency scores for the two groups
    show statistically significant differences using a t-test, followed by Benjamini-Hochberg (BH) adjustment. Effect size (Cohen_dist function) was used to 
    measure the  difference between the two groups. For each measurement, only the sample size for each group larger than five was considered. 

    For the shRNA data-based pipeline, cancer cell line gene dependency scores derived from DEMETER2 (version 6) from a combined dataset of 
    Achilles, DRIVE [45], and shRNA screen in breast cancer cell lines were used. The mutation data and sample annotation were for the DepMap 
    20Q3 dataset. Significant differences are defined for gene pairs with BH-adjusted P value smaller than 0.05. 
    Significant gene pairs with effect size (Cohen_dist function) smaller than 0 are predicted to be SLIs.

    Input:  
    tumor_type: A list of tumor types 
    mut_gene: The list of mutated genes
    Mut_mat: The mutation matrix from CCLE data set
    Depmap_matrix: The shRNA or CRISPR dataset 
    datatype: "shRNA" or "Crispr"

    Output: 
    A dataframe that describe the potential synthetic lethality interactions.

    """    
    def Cohen_dist(x,y):

        n1 = len(x)
        n2 = len(y)
        s = np.sqrt(((n1 - 1)*(np.std(x))*(np.std(x)) + (n2 - 1) * (np.std(y)) * (np.std(y))) / (n1 + n2 -2))
        d = (np.mean(x) - np.mean(y)) / s
        return(d)
    
    
    #selection of cancer cell lines in certain tumor types  
    client = bigquery.Client(project_id)
    #query = ''' 
    #        SELECT DepMap_ID, primary_disease,TCGA_subtype
    #        FROM `syntheticlethality.DepMap_public_20Q3.sample_info_Depmap_withTCGA_labels` 
    #        '''
    query = ''' 
            SELECT DepMap_ID, primary_disease,TCGA_subtype
            FROM `isb-cgc-bq.synthetic_lethality.sample_info_TCGAlabels_DepMapPublic_20Q3` 
            '''

    sample_info = client.query(query).result().to_dataframe()
    
    pancancer_cls = (sample_info.loc[~sample_info['primary_disease'].isin(['Non-Cancerous','Unknown','Engineered','Immortalized'])]) #'Non-Cancerous','Unknown','Engineered','Immortalized' cell lines are excluded.
    pancancer_cls = pancancer_cls.loc[~(pancancer_cls['primary_disease'].isna())] #cell lines without known primary disease is excluded. 
    
    #selection of cell lines in the tumor types selected
    if tumor_type == ['pancancer']:
        cl_sele = list(pancancer_cls['DepMap_ID'].values)

    else:
        tumor_selected = tumor_type
        cl_sele = sample_info.loc[sample_info['primary_disease'].isin((tumor_selected))]['DepMap_ID']  
        cl_sele = list(set(list(Depmap_matrix.index.values)).intersection(set(cl_sele)))

        
    #selection of cell lines with mutation data
    #query = ''' 
    #        select DepMap_ID from `syntheticlethality.DepMap_public_20Q3.CCLE_mutation`
    #        group by DepMap_ID
    #        '''
    query = ''' 
            select DepMap_ID from `isb-cgc-bq.DEPMAP.CCLE_mutation_DepMapPublic_current`
            group by DepMap_ID
            '''

    samples_with_mut = client.query(query).result().to_dataframe()
    samples_with_mut = set(samples_with_mut['DepMap_ID'])
    
    #The following mutation events are included in the analysis. 
    selected_variants = ['Splice_Site',
                     'Frame_Shift_Del',
                     'Frame_Shift_Ins',
                     'Nonstop_Mutation',
                     'In_Frame_Del',
                     'In_Frame_Ins',
                     'Missense_Mutation',
                     'Nonsense_Mutation',
                     'Nonstop_Mutation',
                     'Start_Codon_Del',
                     'Start_Codon_Ins',
                     'Start_Codon_SNP',
                     'Stop_Codon_Del',
                     'Stop_Codon_Del',
                     'Stop_Codon_Ins',
                     'De_novo_Start_OutOfFrame']
    
    #selection of cell lines with crispr or shRNA knockdown data
    samples_depmap_newname = []
    if datatype == "Crispr":
        #query = ''' 
        #        select DepMap_ID from `syntheticlethality.DepMap_public_20Q3.Achilles_gene_effect`
        #        group by DepMap_ID
        #        '''
        query = ''' 
                select DepMap_ID from `isb-cgc-bq.DEPMAP.Achilles_gene_effect_DepMapPublic_current`
                group by DepMap_ID
                '''
        samples_depmap = client.query(query).result().to_dataframe()
        samples_depmap = set(samples_depmap['DepMap_ID'])
        for sample in samples_depmap:
            samples_depmap_newname.append(sample)
        
    elif datatype == "shRNA":
        #query = ''' 
        #        select CCLE_ID from `syntheticlethality.DEMETER2_v6.D2_combined_gene_dep_score`
        #        group by CCLE_ID
        #        '''
        query = ''' 
                select CCLE_ID from `isb-cgc-bq.DEPMAP.Combined_gene_dep_score_DEMETER2_current`
                group by CCLE_ID
                '''
        samples_depmap = client.query(query).result().to_dataframe()
        samples_depmap = set(samples_depmap['CCLE_ID'])
        
        sample_info = get_ccle_sample_info(project_id)
        sample_map = {}
        for i in range(0, sample_info.shape[0]):
            Depmap_id = sample_info.iloc[i,0]
            CCLE_Name = sample_info.iloc[i,1]
            sample_map[CCLE_Name]  = Depmap_id
            
        for sample in samples_depmap:
            if sample in sample_map:
                samples_depmap_newname.append(sample_map[sample])
    else:
        print("Data type must be 'Crispr' or 'shRNA'!")
            
            
    #The intersection of cell lines with mutation and knockdown or knockout data
    Samples_with_mut_kd = samples_with_mut.intersection(cl_sele).intersection(samples_depmap_newname)
    
    Mut_mat_sele1 = Mut_mat.loc[Mut_mat['DepMap_ID'].isin(Samples_with_mut_kd)]
    Mut_mat_sele2 = Mut_mat_sele1.loc[Mut_mat_sele1['Variant_Classification'].isin(selected_variants)]
    
    Mut_mat_sele3 = Mut_mat_sele2.loc[Mut_mat_sele2['Hugo_Symbol'].isin(mut_gene),['Hugo_Symbol','DepMap_ID']]
    Depmap_matrix_sele = Depmap_matrix.loc[Samples_with_mut_kd,:].transpose()

    Gene_mut_list = []
    Gene_kd_list = []
    p_list = []
    es_list = []
    size_mut = []
    FDR_List = []
    result = pd.DataFrame()

    for Gene in mut_gene:
        print("Gene mutated: " + Gene)
        p_list_curr = []
        Mut_group = list(Mut_mat_sele3.loc[Mut_mat_sele3['Hugo_Symbol'] == Gene]['DepMap_ID'].values)
        WT_group = list(set(Samples_with_mut_kd) - set(Mut_group))
        print("Number of samples with mutation: " + str(len(Mut_group)))
        
        for Gene_kd in list(Depmap_matrix_sele.index.values):
            D_mut_new = Depmap_matrix_sele.loc[Gene_kd,Mut_group].values
            D_wt_new = Depmap_matrix_sele.loc[Gene_kd,WT_group].values

            nan_array = np.isnan(D_mut_new)
            not_nan_array = ~ nan_array
            D_mut_new = D_mut_new[not_nan_array]

            nan_array = np.isnan(D_wt_new)
            not_nan_array = ~ nan_array
            D_wt_new = D_wt_new[not_nan_array]
            

            # T-test is used to test the significance of difference of the gene knockout/knockdown effects between the mutated group and wt-group.
            # Cohen's distance was used to measure the different between the two groups. 
            # genes that with mutation in more than 5 cell lines are taken into consideration. 
        
            if len(D_mut_new) > 5:
                Sci_test = stats.ttest_ind(D_mut_new, D_wt_new, nan_policy = 'omit')
                pvalue = Sci_test[1]
                if np.isnan(pvalue) == False:
                    size_mut.append(len(D_mut_new))              #Number of cell lines with mutation of the gene being tested. 
                    p_list_curr.append(pvalue)                   # p_value from the t-test
                    Size_effect =Cohen_dist(D_mut_new, D_wt_new) # The difference of gene knockout/knockdown effects between the mutated group and the wild type group
                    es_list.append(Size_effect)
                    Gene_mut_list.append(Gene)                   # The gene being mutated
                    Gene_kd_list.append(Gene_kd)                 # The gene being knockout/knockdown

        if len(p_list_curr) > 0:

            FDR_List_table = multi.multipletests(p_list_curr, alpha=0.05, method='fdr_bh', is_sorted=False)[1]    #Multi-testing correlation based on each gene
            p_list = p_list + p_list_curr
            FDR_List = FDR_List + list(FDR_List_table)
            
    if len(p_list) > 0:
        FDR_List_table = multi.multipletests(p_list, alpha=0.05, method='fdr_bh', is_sorted=False)[1]
        FDR_List_allExp = list(FDR_List_table)  #Multi-testing correlation for the whole experiment
    
        # Standardize output
        Gene_mut_list_symbol = []
        Gene_mut_list_set = list(set(Gene_mut_list))

        dic_alias_gene = GeneSymbol_standardization_output(Gene_kd_list,project_id)
        Gene_mut_list_Symbol = []
        for gene in Gene_mut_list:
            if gene in dic_alias_gene:
                Gene_mut_list_Symbol.append(dic_alias_gene[gene])
            else:
                Gene_mut_list_Symbol.append(gene)

        Gene_kd_list_symbol = []
        for gene in Gene_kd_list:
            if gene in dic_alias_gene:
                Gene_kd_list_symbol.append(dic_alias_gene[gene])
            else:
                Gene_kd_list_symbol.append(gene)

        result = pd.DataFrame({"Gene_mut": Gene_mut_list, 
                               "Gene_mut_symbol": Gene_mut_list_Symbol,
                               "Gene_kd": Gene_kd_list, 
                               "Gene_kd_symbol":Gene_kd_list_symbol,
                               "Mutated_samples":size_mut,
                               "pvalue": p_list, 
                               "ES":es_list, 
                               "FDR_by_gene": FDR_List,
                               "FDR_all_exp":FDR_List_allExp,
                               "Tumor_type":[','.join(tumor_type)]*len(FDR_List_allExp)
                          })
    return(result)
    


