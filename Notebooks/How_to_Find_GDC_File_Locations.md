R How to Find GDC File Locations
================

# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)\!

    Title:   How to Find GDC File Locations
    Author:  Lauren Hagen
    Created: 2019-08-13
    Purpose: Demonstrate how to find GDC file locations using manifests available in BigQuery
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_Find_GDC_File_Locations.md
    Notes: 

-----

# How to Find GDC File Locations

In this notebook, we will explore the data sets available in the
[Genomic Data Commons](https://gdc.cancer.gov/) using the GDC metadata
tables in BigQuery and find the file location within GDC. The metadata
tables are useful because several of the available data sets in GDC are
not yet available in the ISB-CGC WebApp or as BigQuery tables. This also
means that the data sets can’t be used with the ISB-CGC API’s. The
metadata tables can help you find which data sets are available in GDC
along with their locations and available file and sequencing types. The available metadata tables along with other data sets and tables from ISB-CGC can be explored without login with the [ISB-CGC BigQuery Table Searcher](https://isb-cgc.appspot.com/bq_meta_search/).

This notebook has been designed to keep itself up to date when new
metadata tables releases as new data sets are added to GDC or updated
every few months though we will be using the tables from release 14 in
the examples.

But first things first is to load libraries and create a client
variable.

``` r
library(bigrquery)
library(dplyr)
library(stringr)
```

``` r
billing <- 'isb-cgc-02-0001' # Insert your project ID in the ''
```

Let us first explore the available metadata tables in BigQuery that are
hosted by ISB-CGC. The data set in BigQuery is `isb-cgc.GDC_metadata`
and tables are listed with the release of data that they are from. For
example: `isb-cgc.GDC_metadata.rel14_fileData_current` is from release
14 of data in GDC. An explanation of what data is associated with each
release can be found on the [GDC Data
Release](https://docs.gdc.cancer.gov/Data/Release_Notes/Data_Release_Notes/)
and [ISB-CGC Data Releases and Future
Plans](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/updates_and_releases/Data_Releases.html)
pages. The manifests that are list with each release is what is used to
create the metadata within BigQuery that is hosted by ISB-CGC, so that
you do not need to download and tidy the release manifests thus saving
you time\!

Now let us view which releases are available currently in BigQuery:

``` r
tables <- list_tables("isb-cgc", "GDC_metadata")
tables
```

    ##  [1] "DLBC_affected_files"           "GDC_sync_active_20190104"     
    ##  [3] "GDC_sync_active_20190115"      "GDC_sync_legacy_20190104"     
    ##  [5] "GDC_sync_legacy_20190115"      "GDC_sync_obsolete_20190115"   
    ##  [7] "PanCanAtlas_manifest"          "rel12_GDCfileID_to_GCSurl"    
    ##  [9] "rel12_aliquot2caseIDmap"       "rel12_caseData"               
    ## [11] "rel12_fileData_current"        "rel12_fileData_legacy"        
    ## [13] "rel12_slide2caseIDmap"         "rel13_GDCfileID_to_GCSurl"    
    ## [15] "rel13_aliquot2caseIDmap"       "rel13_caseData"               
    ## [17] "rel13_fileData_current"        "rel13_fileData_legacy"        
    ## [19] "rel13_slide2caseIDmap"         "rel14_GDCfileID_to_GCSurl"    
    ## [21] "rel14_GDCfileID_to_GCSurl_NEW" "rel14_aliquot2caseIDmap"      
    ## [23] "rel14_caseData"                "rel14_fileData_current"       
    ## [25] "rel14_fileData_legacy"         "rel14_slide2caseIDmap"        
    ## [27] "rel15_aliquot2caseIDmap"       "rel15_caseData"               
    ## [29] "rel15_fileData_current"        "rel15_fileData_legacy"        
    ## [31] "rel15_slide2caseIDmap"         "rel16_aliquot2caseIDmap"      
    ## [33] "rel16_caseData"                "rel16_fileData_active"        
    ## [35] "rel16_fileData_legacy"         "rel16_slide2caseIDmap"        
    ## [37] "rel17_aliquot2caseIDmap"       "rel17_caseData"               
    ## [39] "rel17_fileData_active"         "rel17_fileData_legacy"        
    ## [41] "rel17_slide2caseIDmap"

Let us get the most recent data release available in the
`isb-cgc.GDC_metadata` data set.

``` r
releases <- c()
for (t in 1:length(tables)) {
  release <- str_match(tables[t], "(rel\\d*)_")[2]
  if (!is.na(release) && !(release %in% releases)) {
      releases <- c(releases, release)
  }
}
releases <- sort(releases)
releases
```

    ## [1] "rel12" "rel13" "rel14" "rel15" "rel16" "rel17"

``` r
curr_release <- releases[length(releases)]
curr_release
```

    ## [1] "rel17"

The next code block can be removed to use other release sets but the
examples in the rest of the notebook may need to updated for the
approapriate release and column
names.

``` r
# If this code block is removed, please check if the column names through the notebook are still correct
curr_release <- "rel14"
```

Each release is split up into several tables based on the data that they
help to faciltiate
finding.

| Table                                               | Description                                                                                                                                                                          |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| rel\#\_caseData                                     | List of all of the cases in GDC                                                                                                                                                      |
| rel\#\_fileData\_current or rel\#\_fileData\_active | List of the currently active cases in GDC along with information related to those cases                                                                                              |
| rel\#\_fileData\_legacy                             | Same as the previous table but with legacy data instead                                                                                                                              |
| rel\#\_aliquot2caseIDmap                            | “helper” table to help map between identifiers at different levels of aliquot data. The intrinsic hierarchy is program \> project \> case \> sample \> portion \> analyte \> aliquot |
| rel\#\_slide2caseIDmap                              | “helper” table to help map between identifiers at different levels of tissue slide data. The intrinsic hierarchy is program \> project \> case \> sample \> portion \> slide         |
| rel\#\_GDCfileID\_to\_GCSurl                        | Gives the Google Cloud Storage location for each file                                                                                                                                |

Let us see which data sets are available within the GDC.

``` r
datasets_query <- str_c("SELECT program_name, COUNT(program_name) AS Num
                        FROM `isb-cgc.GDC_metadata.", curr_release, "_fileData_current`
                        GROUP BY program_name
                        ORDER BY Num DESC", sep = "")
# Query table
# To see the R console output with query processing information, turn queit to FALSE
datasets_result <- bq_project_query(billing, datasets_query, quiet = TRUE) 
# Transform the query result into a tibble
datasets_result <- bq_table_download(datasets_result, quiet = TRUE)
datasets_result
```

    ## # A tibble: 6 x 2
    ##   program_name    Num
    ##   <chr>         <int>
    ## 1 TCGA         314354
    ## 2 FM            36134
    ## 3 TARGET         7138
    ## 4 NCICCR          957
    ## 5 CTSP             89
    ## 6 VAREPOP           7

We are going to explore the Foundation Medicine Adult Cancer Clinical
Data set (FM-AD), one of the newer data sets to the GDC. More
information can be found on the [‘FM-AD Data Set’
page](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/data/FM-AD_about.html)
in the ISB-CGC documentation.

Let us first take a look at the schema for the
`isb-cgc.GDC_metadata.rel14_fileData_current` table as it has the most
interesting data for figuring out which files are available in the GDC.

``` r
# Create the SQL query
fields_query <- str_c("SELECT column_name
                        FROM `isb-cgc.GDC_metadata.INFORMATION_SCHEMA.COLUMNS`
                        WHERE table_name = '", curr_release, "_fileData_current'", sep = "")
# Query table
# To see the R console output with query processing information, turn queit to FALSE
fields_result <- bq_project_query(billing, fields_query, quiet = TRUE) 
# Transform the query result into a tibble
fields_result <- bq_table_download(fields_result, quiet = TRUE)
fields_result
```

    ## # A tibble: 38 x 1
    ##    column_name                             
    ##    <chr>                                   
    ##  1 dbName                                  
    ##  2 file_gdc_id                             
    ##  3 access                                  
    ##  4 acl                                     
    ##  5 analysis_input_file_gdc_ids             
    ##  6 analysis_workflow_link                  
    ##  7 analysis_workflow_type                  
    ##  8 associated_entities__case_gdc_id        
    ##  9 associated_entities__entity_gdc_id      
    ## 10 associated_entities__entity_submitter_id
    ## # ... with 28 more rows

Then we will find out which files formats are available on GDC with a
SQL query. Since, we might want to look at different fields and their
counts, we will write a function that will take the field, table,
release, and program name that will then tell us the count of the field
in a dataframe.

``` r
variable_count <- function(field, table_type, release, program) {
  # Create a variable for the whole table path
  table_path <- str_c("isb-cgc.GDC_metadata.", release, table_type, sep = "")
  # Create a  variable with the SQL query
  count_query = str_c("SELECT ", field, ", COUNT(", field, ") AS Num 
                      FROM `", table_path, "` 
                      WHERE program_name = '", program, "' 
                      GROUP BY ", field, sep = "")
  result <- bq_project_query(billing, count_query, quiet = TRUE) 
  result <- bq_table_download(result, quiet = TRUE)
}
```

Let us now test the function to view the available data formats for the
FM-AD data set.

``` r
# Set the field that we are interested in
field <- "data_format"

# Set the program that we are interested in
program <- "FM"

# Set which table we are going to query
table_type <- "_fileData_current"

# run the function with the defined variables
query_result <- variable_count(field, table_type, curr_release, program)

# display the query results
query_result
```

    ## # A tibble: 3 x 2
    ##   data_format   Num
    ##   <chr>       <int>
    ## 1 MAF            42
    ## 2 TSV            84
    ## 3 VCF         36008

It seems that most of the files for FM-AD are VCF files. Next we are
going to see how many of the files available are controlled access vs
open access.

``` r
# Change the field to access type
field <- "access"

# run the function with the defined variables
query_result <- variable_count(field, table_type, curr_release, program)

# display the query results
query_result
```

    ## # A tibble: 2 x 2
    ##   access       Num
    ##   <chr>      <int>
    ## 1 controlled 36050
    ## 2 open          84

Wow, the majority of the files are controlled access files. You’ll want
to review that you have the correct permissions such as dbGaP
authorization to access controlled data with GDC before proceeding with
attempting to use the data. More information can be found in the ISB-CGC
documentation on the [‘Accessing Controlled Data’
page](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/Gaining-Access-To-Controlled-Access-Data.html).

A few other fields that we might be interested are `data_category`,
`data_type`, `experimental_strategy`, `file_size`, and `platform`. We
can modify the query by modifying the variables `field`, `dataset`,
`curr_release`, and `table_type` to view different tables and field
counts. Let’s update the query to look at the `data_type` field:

``` r
# Change the field to data type
field <- "data_type"

# run the function with the defined variables
query_result <- variable_count(field, table_type, curr_release, program)

# display the query results
query_result
```

    ## # A tibble: 5 x 2
    ##   data_type                     Num
    ##   <chr>                       <int>
    ## 1 Aggregated Somatic Mutation    42
    ## 2 Biospecimen Supplement         42
    ## 3 Clinical Supplement            42
    ## 4 Raw Simple Somatic Mutation 18004
    ## 5 Annotated Somatic Mutation  18004

Now that we have looked over different fields in the table, let us
create a set of files that we are interested in. For this example, we
are going to create a query that will find the GDC file id associated
with the FM-AD data set that are VCF files and have the file type of
‘simple\_somatic\_mutation’.

``` r
FM_gdc_file_query <- str_c("SELECT file_gdc_id
                     FROM `isb-cgc.GDC_metadata.", curr_release, "_fileData_current`
                     WHERE program_name = 'FM' AND data_format = 'VCF' AND file_type =  'simple_somatic_mutation'", sep = "")
# Query table
# To see the R console output with query processing information, turn queit to FALSE
gdc_file_id <- bq_project_query(billing, FM_gdc_file_query, quiet = TRUE) 
# Transform the query result into a tibble
gdc_file_id <- bq_table_download(gdc_file_id, quiet = TRUE)
gdc_file_id
```

    ## # A tibble: 18,004 x 1
    ##    file_gdc_id                         
    ##    <chr>                               
    ##  1 7c9a2c2b-4401-47c6-918f-c0032f9c72a7
    ##  2 2c9d1e76-1c74-41dd-aa38-43d2f2f55e4e
    ##  3 a7e3fd83-49be-4633-8e46-9fbdfe7ba741
    ##  4 ac26d85c-efa2-42a2-b63a-58b89f0c9c1c
    ##  5 a1f089d2-d5dc-496a-8ec2-faaac1225d86
    ##  6 e1f4ad4d-9096-4080-b276-db8936882f51
    ##  7 e23cdeae-be46-468c-9a3c-f7eade3413ec
    ##  8 24b429de-0f3b-4c81-8505-d65bbda9c757
    ##  9 b8ad6936-9e05-455b-9edc-cb6c0db03da5
    ## 10 811abd12-df1e-486d-824a-1e5a5b74b6e7
    ## # ... with 17,994 more rows

``` r
length(gdc_file_id$file_gdc_id)
```

    ## [1] 18004

Now that we have a list of the GDC file ids, we can join it with the GCP
urls from the `rel14_GDCfileID_to_GCSurl` table.

``` r
url_query = str_c("WITH id AS (SELECT file_gdc_id
                  FROM `isb-cgc.GDC_metadata.", curr_release, "_fileData_current`
                  WHERE program_name = '", program, "'
                  AND data_format = 'VCF' AND file_type =  'simple_somatic_mutation')
                  SELECT t2.file_gdc_url
                  FROM id AS t1
                  INNER JOIN `isb-cgc.GDC_metadata.", curr_release, "_GDCfileID_to_GCSurl_NEW` AS t2
                  ON t1.file_gdc_id = t2.file_gdc_id", sep = "")
# Query table
# To see the R console output with query processing information, turn queit to FALSE
gdc_file_url <- bq_project_query(billing, url_query, quiet = TRUE) 
# Transform the query result into a tibble
gdc_file_url <- bq_table_download(gdc_file_url, quiet = TRUE)
gdc_file_url
```

    ## # A tibble: 18,004 x 1
    ##    file_gdc_url                                                            
    ##    <chr>                                                                   
    ##  1 gs://gdc-fm-phs001179-controlled/a9130aed-b49d-4dd2-b611-b132b7ad7d28/a~
    ##  2 gs://gdc-fm-phs001179-controlled/b1c15a06-12d2-4a31-9dce-684e6b7c7133/b~
    ##  3 gs://gdc-fm-phs001179-controlled/01f4eddf-15df-4254-9a65-32501c704567/0~
    ##  4 gs://gdc-fm-phs001179-controlled/45bbf05a-3ad2-4923-bcc7-eaf625a79aa2/4~
    ##  5 gs://gdc-fm-phs001179-controlled/646fb13b-6471-4379-bd1f-0321b38f3694/6~
    ##  6 gs://gdc-fm-phs001179-controlled/fd3f7d0e-d38d-49e1-acb6-37fde1236f6b/f~
    ##  7 gs://gdc-fm-phs001179-controlled/ab3abe4c-6989-4328-acde-4a1208bb5dd7/a~
    ##  8 gs://gdc-fm-phs001179-controlled/acaf5498-3d82-44c0-a323-716e958407e0/a~
    ##  9 gs://gdc-fm-phs001179-controlled/3faea6ef-fc51-4f9e-8683-0d1efd86044d/3~
    ## 10 gs://gdc-fm-phs001179-controlled/ff3d1f20-d864-4725-ab38-b76b2ddbf47a/f~
    ## # ... with 17,994 more rows

``` r
length(gdc_file_url$file_gdc_url)
```

    ## [1] 18004

Now that we have some basics about the metadata tables, it would be good
to go over a more complicated SQL query to combine a set of cohort
case\_barcodes and then find the associated GDC urls by building and
joining many tables. The first portion of the query below is from the
[How to Create Cohorts
Notebook](https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_create_cohorts.ipynb)
in the [ISB-CGC Community Notebook
Repository](https://github.com/isb-cgc/Community-Notebooks/tree/master/Notebooks).

``` r
cohort_to_url_query = "-- SQL Query from the How to Create Cohorts Notebook
WITH
  select_on_annotations AS (
  SELECT
    case_barcode,
    category AS categoryName,
    classification AS classificationName
  FROM
    `isb-cgc.TCGA_bioclin_v0.Annotations`
  WHERE
    ( entity_type='Patient'
      AND (category='History of unacceptable prior treatment related to a prior/other malignancy'
        OR classification='Redaction' ) )
  GROUP BY
    case_barcode,
    categoryName,
    classificationName ),
  select_on_clinical AS (
  SELECT
    case_barcode,
    vital_status,
    days_to_last_known_alive,
    ethnicity,
    histological_type,
    menopause_status,
    race
  FROM
    `isb-cgc.TCGA_bioclin_v0.Clinical`
  WHERE
    ( disease_code = 'BRCA'
      AND age_at_diagnosis<=50
      AND gender='FEMALE' ) ),
-- Combine the cohort with the metadata tables to create a list of GDC urls
    cohort AS (
  SELECT
    case_barcode
  FROM (
    SELECT
      a.categoryName,
      a.classificationName,
      c.case_barcode
    FROM
      select_on_annotations AS a
    FULL JOIN
      select_on_clinical AS c
    ON
      a.case_barcode = c.case_barcode
    WHERE
      a.case_barcode IS NOT NULL
      OR c.case_barcode IS NOT NULL
    ORDER BY
      a.classificationName,
      a.categoryName,
      c.case_barcode )
  WHERE
    categoryName IS NULL
    AND classificationName IS NULL
    AND case_barcode IS NOT NULL
  ORDER BY
    case_barcode),
  gdc AS (SELECT a.case_barcode, b.case_gdc_id
  FROM cohort AS a
  INNER JOIN `isb-cgc.GDC_metadata.rel14_caseData` AS b
  ON a.case_barcode = b.case_barcode),
  curr AS (SELECT c.case_barcode, c.case_gdc_id, d.file_gdc_id
  FROM gdc as c
  INNER JOIN `isb-cgc.GDC_metadata.rel14_fileData_current` AS d
  ON c.case_gdc_id = d.case_gdc_id),
  url AS ( SELECT e.case_barcode, e.case_gdc_id, e.file_gdc_id, f.file_gdc_url
  FROM curr AS e
  INNER JOIN `isb-cgc.GDC_metadata.rel14_GDCfileID_to_GCSurl_NEW` AS f
  ON e.file_gdc_id = f.file_gdc_id)
SELECT case_barcode, file_gdc_url FROM url ORDER BY case_barcode"

# Query table
# To see the R console output with query processing information, turn queit to FALSE
cohort_to_url <- bq_project_query(billing, cohort_to_url_query, quiet = TRUE) 
# Transform the query result into a tibble
cohort_to_url <- bq_table_download(cohort_to_url, quiet = TRUE)
cohort_to_url
```

    ## # A tibble: 9,556 x 2
    ##    case_barcode file_gdc_url                                               
    ##    <chr>        <chr>                                                      
    ##  1 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/c993c79e-ac58-423e-ae89-352d1~
    ##  2 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/fe3ceb38-aecc-4efe-9d3d-2e802~
    ##  3 TCGA-3C-AALI gs://gdc-tcga-phs000178-controlled/a736c2d0-2c4b-433f-9eb3~
    ##  4 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/00737aa1-d1da-4386-b444-8abad~
    ##  5 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/ad8e6a02-4483-4049-ae7e-3a8a5~
    ##  6 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/3703a961-f8eb-4b2e-8fb3-ebeb8~
    ##  7 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/1bb15d67-0bcb-4d29-b186-2d57a~
    ##  8 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/af436ccb-b052-4cb6-892c-d4f2e~
    ##  9 TCGA-3C-AALI gs://gdc-tcga-phs000178-controlled/213e9b8f-3d2f-4dad-89a6~
    ## 10 TCGA-3C-AALI gs://gdc-tcga-phs000178-open/8b71d07c-b166-4260-993a-89ecf~
    ## # ... with 9,546 more rows
