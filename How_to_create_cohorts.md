How to Create Cohorts
================

# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)!

    Title:   How to create cohorts
    Author:  Lauren Hagen
    Created: 2019-06-20
    Updated: 2023-12
    Purpose: Basic overview of creating cohorts with IDB-CGC BigQuery
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_create_cohorts.Rmd
    Notes:   This notebook was adapted from work by Sheila Reynolds, 'How to Create TCGA Cohorts part 1' https://github.com/isb-cgc/examples-Python/blob/master/notebooks/Creating%20TCGA%20cohorts%20--%20part%201.ipynb.

------------------------------------------------------------------------

# How to Create Cohorts

This notebook demonstrates how to create a cohort (list) of patients
from the [Genomic Data Commons (GDC)](https://portal.gdc.cancer.gov/)
using ISB-CGC public BigQuery tables. We will use the clinical and file
tables to create a curated list of patients to discover associated files
and data. More information on the tables and data that this notebook
explores can be found in our Documentation at: - [ISB-CGC BigQuery
Tables](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/BigQuery.html) -
[Programs and Data
Sets](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/Hosted-Data.html) -
[Case and File
Metadata](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/data/FileMetadata.html) -
[Clinical, Biospecimen and Processed -Omics Data
Sets](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/Hosted-Data.html#clinical-biospecimen-and-processed-omics-data-sets)

## Initialize Notebook Environment

Before beginning, we first need to load dependencies and authenticate to
BigQuery. You will need to have access to a [Google Cloud Platform
(GCP)](https://cloud.google.com/?hl=en) project in order to use
BigQuery.

### Load Libraries

``` r
library(bigrquery)
library(tidyverse)
```

### Log into Google Cloud Storage and Authenticate ourselves

*Note: this will come up with your first call to BigQuery and will be
cached*

1.  Authenticate yourself with your Google Cloud Login
2.  A second tab will open or follow the link provided
3.  Follow prompts to Authorize your account to use Google Cloud SDK
4.  Copy code provided and paste into the box under the Command
5.  Press Enter

[Alternative authentication
methods](https://bigrquery.r-dbi.org/reference/bq_auth.html)

### Creating a client and using a billing project

To access BigQuery, you will need a Google Cloud Project for queries to
be billed to. If you need to create a Project, instructions on how to
create one can be found on our [Quick-Start Guide
page](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html).

A BigQuery Client object with the billing Project needs to be created to
interface with BigQuery.

> Note: Any costs that you incur are charged under your current project,
> so you will want to make sure you are on the correct one if you are
> part of multiple projects.

``` r
project_id <- 'YOUR_PROJECT_ID_CHANGE_ME' # Update with your Google Project Id
```

``` r
if (project_id == 'YOUR_PROJECT_ID_CHANGE_ME') {
  print('Please update the project id with your Google Cloud Project')
}
```

## Create a Simple Cohort

To create this cohort, we are going to explore TCGA data to find
projects with patients (cases) that have a history of smoking and the
number of years they smoked. We then will explore the data types
available in the top three projects.

### Determine which Projects to Use

We will use the TCGA clinical table to find projects with the most data
for the number of years smoked. This query can be used to look at any
feature in the clinical table. The query uses COUNT and GROUP BY to
calculate the number of patients with data.

``` r
# Create the SQL query
query_clinical <- "  SELECT
    proj__project_id,
    COUNT(proj__project_id) AS n
  FROM
    `isb-cgc-bq.TCGA_versioned.clinical_gdc_r37`
  WHERE
    exp__years_smoked is not Null
  GROUP BY
    proj__project_id
  ORDER BY
    n DESC"
# Query BigQuery and put the results in a data frame
result_clinical_projects <- bq_table_download(bq_project_query(project_id, query_clinical))
# Create a variable of the three most populated projects
project_ids = str_c(result_clinical_projects$proj__project_id[1:3], collapse="', '")
# print the results
print(result_clinical_projects)
```

### Create a List of Cases with Selected Projects

The [TCGA-LUSC (Lung Squamous Cell
Carcinoma)](https://portal.gdc.cancer.gov/projects/TCGA-LUSC),
[TCGA-LUAD (Lung
Adenocarcinoma)](https://portal.gdc.cancer.gov/projects/TCGA-LUAD), and
[TCGA-HNSC (Head and Neck Squamous Cell
Carcinoma)](https://portal.gdc.cancer.gov/projects/TCGA-HNSC) projects
are the top three projects with patients that have data for number of
years smoking. The patients in these projects will form the base of our
cohort. A cohort can be created by a number of different filters such as
patients that smoked more than 10 years or the primary disease type.

``` r
# Create the SQL query
query_case <- str_c("SELECT
    proj__project_id,
    case_id,
    exp__years_smoked
  FROM
    `isb-cgc-bq.TCGA_versioned.clinical_gdc_r37`
  WHERE
    proj__project_id IN ('", project_ids, "') AND exp__years_smoked is not Null")
# Query BigQuery with results to a data frame
clinical_case_ids <- bq_table_download(bq_project_query(project_id, query_case))
# Create a variable of the case ids
case_ids <- str_c(clinical_case_ids$case_id, collapse = "', '")
# print the results
print(clinical_case_ids)
```

### View the Data Types Available

Now that we have a cohort of case ids, we can use that list to discover
the available data types with the file table.

``` r
# Create the SQL query
query_file_types <- str_c("SELECT
    file.project_short_name,
    file.data_category,
    file.data_type,
    file.data_format,
    COUNT(file.file_gdc_id) as n
  FROM
    `isb-cgc-bq.GDC_case_file_metadata.fileData_active_current` AS file
  WHERE
    associated_entities__case_gdc_id IN ('", case_ids, "')
  GROUP BY
    file.project_short_name,
    file.data_category,
    file.data_type,
    file.data_format
  ORDER BY file.data_type, n DESC")
# Query BigQuery with results to a data frame
result_file_types <- bq_table_download(bq_project_query(project_id, query_file_types))
# print the results
print(result_file_types)
```

We can then use the cohort of case ids to create a table with RNA seq
data for the associated aliquots.

``` r
# Create the SQL query
query_rna <- str_c("SELECT
    aliquot_gdc_id,
    fpkm_unstranded
  FROM
    `isb-cgc-bq.TCGA_versioned.RNAseq_hg38_gdc_r35`
  WHERE
        case_gdc_id IN ('", case_ids, "')
  LIMIT 50")
# Query BigQuery with results to a data frame
results_rna_seq <- bq_table_download(bq_project_query(project_id, query_rna))
# print the results
print(results_rna_seq)
```

The final query to create the table of RNA seq data can also be created
with one query with a join between the clinical table and the RNA seq
table.

      SELECT
        c.case_id,
        c.exp__years_smoked,
        r.fpkm_unstranded
      FROM
        `isb-cgc-bq.TCGA_versioned.clinical_gdc_r37` AS c
      JOIN
        `isb-cgc-bq.TCGA_versioned.RNAseq_hg38_gdc_r35` AS r
      ON
        c.case_id = r.case_gdc_id
      WHERE
        proj__project_id IN ('TCGA-LUSC',
          'TCGA-LUAD',
          'TCGA-HNSC')
        AND exp__years_smoked IS NOT NULL

# Closing

Thank you for working through this notebook. We hope that you found this
exercise to be helpful in finding relevant cohorts for your studies.
Please explore the ISB-CGC ecosystem at [isb-cgc.org](isb-cgc.org).

For questions, comments, or troubleshooting, please contact us at
<feedback@isb-cgc.org>. We are especially keen on learning about your
particular use-cases, and how we can help you take advantage of the
latest in cloud-computing technologies to answer your research
questions. Also, check out our virtual [Office Hours on Tuesdays and
Thursdays](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/office_hours.html).
