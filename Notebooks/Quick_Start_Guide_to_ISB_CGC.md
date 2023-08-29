Quick Start Guide for ISB-CGC
================

# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)!

    Title:   Quick Start Guide to ISB-CGC
    Author:  Lauren Hagen
    Created: 2019-06-20
    Updated: 2023-08
    Purpose: Painless intro to working in the cloud
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/Quick_Start_Guide_to_ISB_CGC.Rmd
    Notes:

# Quick Start Guide to [ISB-CGC](https://isb-cgc.appspot.com/)

## Account Set-up

To run this notebook, you will need to have your Google Cloud Account
set up. If you need to set up a Google Cloud Account, follow the “Obtain
a Google identity” and “Set up a Google Cloud Project” steps on our
[Quick-Start Guide
documentation](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html)
page.

## Libraries needed for the Notebook

This notebook requires the bigrquery package to be loaded [(click here
for more
information)](https://cran.r-project.org/web/packages/bigrquery/index.html).
This library will allow you to access BigQuery programmatically.

``` r
library(bigrquery)
library(dplyr)
```

## Overview of ISB-CGC

The ISB-CGC provides interactive and programmatic access to data hosted
by institutes such as the [Genomic Data Commons
(GDC)](https://gdc.cancer.gov/) and [Proteomic Data Commons
(PDC)](https://proteomic.datacommons.cancer.gov/pdc/) from the [National
Cancer Institute (NCI)](https://www.cancer.gov/) while leveraging many
aspects of the Google Cloud Platform. You can also import your data,
analyze it side by side with the datasets, and share your data when you
see fit. The ISB-CGC hosts carefully curated high-level clinical,
biospecimen, and molecular datasets and tables in Google BigQuery,
including data from programs such as [The Cancer Genome Atlas
(TCGA)](https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga),
[Therapeutically Applicable Research to Generate Effective Treatments
(TARGET)](https://ocg.cancer.gov/programs/target), and [Clinical
Proteomic Tumor Analysis Consortium
(CPTAC)](https://proteomics.cancer.gov/programs/cptac). For more
information can be found at our [Programs and Data Sets
page](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/Hosted-Data.html).
This data can be explored via python, [Google Cloud
Console](https://console.cloud.google.com/) and/or our [BigQuery Table
Search tool](https://isb-cgc.appspot.com/bq_meta_search/).

## Example of Accessing BigQuery Data with R

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

### View ISB-CGC Datasets and Tables in BigQuery

Let us look at the datasets available through ISB-CGC that are in
BigQuery.

``` r
# Let us view which datasets are available from ISB-CGC through BigQuery
datasets <- bq_project_datasets("isb-cgc-bq")
for (dataset in datasets) {
  print(dataset[[2]])
}
```

The ISB-CGC has two datasets for each Program or source. One dataset
contains the most current data, and the other contains versioned tables,
which serve as an archive for reproducibility. The current tables are
labeled with “\_current” and are updated when new data is released. For
more information, visit our [ISB-CGC BigQuery
Projects](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/BigQuery/ISBCGC-BQ-Projects.html)
page. Let’s see which tables are under the TCGA dataset.

``` r
# Let us look which tables are in the TCGA dataset
tables <- bq_dataset_tables("isb-cgc-bq.TCGA_versioned")
for (table in tables){
  print(table[[3]])
}
```

### Query ISB-CGC BigQuery Tables

In this section, we will create a string variable with our SQL then call
to BigQuery and save the result to a dataframe.

#### Syntax for the query

    SELECT # Select a few columns to view
      proj__project_id, # GDC project
      submitter_id, # case barcode
      proj__name # GDC project name
    FROM # Which table in BigQuery in the format of `project.dataset.table`
      `project_name.dataset_name.table_name` # From the GDC TCGA Clinical Dataset
    LIMIT
      5 # Limit to 5 rows as the dataset is very large and we only want to see a few results

> Note: `LIMIT` only limits the number of rows returned and not the
> number of rows that the query looks at

``` r
# Create the SQL query
sql <- "
  SELECT
    proj__project_id,
    submitter_id,
    proj__name
  FROM
    `isb-cgc-bq.TCGA_versioned.clinical_gdc_r37`
  LIMIT
    5"
# Use BigQuery to run the SQL query on the Clinical table from the TCGA dataset
# which then may be downloaded into a tibble.
result <- bq_project_query(project_id, sql)
# Create a data frame with results
result <- bq_table_download(result)
# print the results
print(result)
```

## Resources

There are several ways to access and explore the data hosted by ISB-CGC.

- ISB-CGC
  - [ISB-CGC WebApp](https://isb-cgc.appspot.com/)
    - Provides a graphical interface to file and case data
    - Cohort creation
    - File exploration
  - [ISB-CGC BigQuery Table
    Search](https://isb-cgc.appspot.com/bq_meta_search/)
    - Provides a table search for available ISB-CGC BigQuery Tables
  - [ISB-CGC APIs](https://api-dot-isb-cgc.appspot.com/v4/swagger/)
    - Provides programmatic access to metadata
- Google Cloud
  - [Google Cloud Platform](https://cloud.google.com/)
    - Access and store data in [Google Cloud
      Storage](https://cloud.google.com/storage) and
      [BigQuery](https://cloud.google.com/bigquery) via User Interfaces
      or programmatically
- Suggested Programming Languages and Programs to use
- SQL
  - Can be used directly in [BigQuery
    Console](https://console.cloud.google.com/bigquery)
  - Or via API in Python or R
- [Python](https://www.python.org/)
  - [gsutil tool](https://cloud.google.com/storage/docs/gsutil)
  - [Jupyter Notebooks](https://jupyter.org/)
  - [Google Colabratory](https://colab.research.google.com/)
  - [Cloud Datalab](https://cloud.google.com/datalab/)
- [R](https://www.r-project.org/)
  - [RStudio](https://rstudio.com/)
  - [RStudio.Cloud](https://rstudio.cloud/)
- Command Line Interfaces
  - Cloud Shell via Project Console
  - [CLOUD SDK](https://cloud.google.com/sdk/)
- Getting Started for Free:
  - [Free Cloud Credits from ISB-CGC for Cancer
    Research](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowtoRequestCloudCredits.html)
  - [Google Free Tier with up to 1TB of free queries a
    month](https://cloud.google.com/free)

Useful ISB-CGC Links:

- [ISB-CGC Landing Page](https://isb-cgc.appspot.com/)
- [ISB-CGC
  Documentation](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/)
- [How to Get Started on
  ISB-CGC](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html)
- [How to access Google
  BigQuery](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/progapi/bigqueryGUI/HowToAccessBigQueryFromTheGoogleCloudPlatform.html)
- [Community Notebook
  Repository](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowTos.html)

Useful Google Tutorials:

- [Google’s What is
  BigQuery?](https://cloud.google.com/bigquery/docs/introduction)
- [Google Cloud Client Library for
  Python](https://googleapis.github.io/google-cloud-python/latest/index.html)
