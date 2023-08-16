# Synthetic Lethality Cloud (SL-Cloud)

This project provides a cloud-based data access platform coupled with software and well documented computational notebooks that re-implement published synthetic lethality (SL) inference algorithms to facilitate novel investigation into synthetic lethality. In addition  we provide general purpose functions that support these prediction workflows e.g. saving data in bigquery tables. We anticipate that computationally savvy users can leverage the resources provided in this project to conduct highly customizable analysis based on their cancer type of interest and particular context. 

Open the framework in **MyBinder**: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/isb-cgc/Community-Notebooks/HEAD?labpath=SL-Cloud%2FMyBinder_Authentication.ipynb)

Citation: 
Bahar Tercan, Guangrong Qin, Taek-Kyun Kim, Boris Aguilar, Christopher J. Kemp, Nyasha Chambwe, Ilya Shmulevich. SL-Cloud: A Computational Resource to Support Synthetic Lethal Interaction Discovery. BioRxiv 2021.09.18.459450; doi: https://doi.org/10.1101/2021.09.18.459450

 If you have any questions, please reach out Bahar Tercan btercan@isbscience.org. 
## Getting Started

### Get a Google Identity

To be able to use our platform, researchers first need to have a Google identity, if you don't have one, please click [here](https://accounts.google.com/signup/v2/webcreateaccount?dsh=308321458437252901&continue=https%3A%2F%2Faccounts.google.com%2FManageAccount&flowName=GlifWebSignIn&flowEntry=SignUp#FirstName=&LastName=) to get, you can also link a non-Gmail account(like sluser<span>@isbscience.org</span>) as a Google identity by [this method](https://accounts.google.com/signup/v2/webcreateaccount?flowName=GlifWebSignIn&flowEntry=SignUp&nogm=true).

### Request Google Cloud Credits

Take advantage of a one-time [$300 Google Credit](https://cloud.google.com/free/).
If you have already used this one-time offer (or there is some other reason you cannot use it), see this information about how to [request ISB-CGC Cloud Credits](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowtoRequestCloudCredits.html).

### Set up a Google Cloud Project

See Google’s documentation about how to create a [Google Cloud Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

[Enable Required Google Cloud APIs](https://cloud.google.com/apis/docs/getting-started#enabling_apis)

### First Notebook

Please run the [first notebook](https://github.com/IlyaLab/SL-Cloud/blob/main/first_notebook.ipynb) to start using our bigquery tables from your computer.  

## What is There in the Project?
### Scripts
- [Scripts folder](https://github.com/IlyaLab/SL-Cloud/tree/main/Scripts/): includes the functions that are used by DAISY and Mutation Dependent  SL Inference workflows explained below. This folder also contains scripts for data wrangling procedures like BigQuery dataset and table creation, how to save DEPMAP data in BigQuery tables, helper functions like writing dataframes into excel files and gene conversion among gene symbol, EntrezID and alias.

### Sythetic Lethality Inference Workflows 
Example notebooks can be found in the Example_pipelines directory, which including the following notebooks:
- [DAISY Pipeline](https://github.com/IlyaLab/SL-Cloud/blob/main/Example_workflows/DAISY_example.ipynb) :We reimplemented the published workflow DAISY (Jerby-Arnon et al., 2014) using up-to-date large scale data resources. </br>
- [Mutation Dependent SL pipeline](https://github.com/IlyaLab/SL-Cloud/blob/main/Example_workflows/MDSLP_example.ipynb): We implemented a mutation-dependent synthetic lethality prediction (MDSLP) workflow based on the rationale that for tumors with mutations that have an impact on protein expression or protein structure (functional mutation), the knockout effects or inhibition of a partner target gene show conditional dependence for the mutated molecular entities.</br>
- [Conservation-based Inference from Yeast Genetic Interactions](https://github.com/IlyaLab/SL-Cloud/blob/main/Example_workflows/CGI_example.ipynb): We presented a workflow that leverages cross-species conservation to infer experimentally-derived synthetic lethal interactions in yeast to predict relevant SL pairs in humans. We implemented the Conserved Genetic Interaction (CGI) workflow based, in part, on methods described in (Srivas et al., 2016). </br>

### Synthetic-Lethality Inference Data Resources
This resource provides access to publicly available cancer genomics datasets relevant for SL inference. These data have been pre-processed, cleaned and stored in cloud-based query-able tables leveraging [Google BigQuery](https://cloud.google.com/bigquery)  technology. In addition we leverage relevant datasets available through the Institute for Systems Biology Cancer Genomics Cloud ([ISB-CGC](https://isb-cgc.appspot.com/)) to make inferences of potential synthetic lethal interactions. 
The following represent project-specific datasets with relevance for SL inference:

- **DEPMAP**: DEPMAP shRNA (DEMETER2 V6) and CRISPR (DepMap Public 20Q3) gene expression, sample information, mutation and copy number alterations  for CRISPR experiments and and gene dependency scores for shRNA and gene effect scores.

- **CellMap**: Yeast interaction dataset based on fitness scores after single and double knockouts from SGA experiments.

- **Gene Information**: Tables with relevant gene annotation information such as yeast and human ortholog information, gene-alias-Entrez ID mapping, gene Ensembl-id mapping, gene-Refseq mapping.


### Accessing ISB-CGC Resources
To be able to see the data in the ISB-CGC project, please click on https://console.cloud.google.com/bigquery and  add the syntheticlethality dataset, users need to pin the syntheticlethality project by first clicking "ADD DATA" and after selecting "Pin a project" and "Enter project name", you will see the window as in the Figure below. After writing isb-cgc-bq into Projectname box, please click on PIN. 
