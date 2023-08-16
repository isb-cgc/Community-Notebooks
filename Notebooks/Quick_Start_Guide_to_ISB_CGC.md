Quick Start Guide for ISB-CGC
================

# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)!

    Title:   Quick Start Guide to ISB-CGC
    Author:  Lauren Hagen
    Created: 2019-06-20
    Updated: 2021-07-27
    Purpose: Painless intro to working in the cloud
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/Quick_Start_Guide_to_ISB_CGC.md
    Notes:

------------------------------------------------------------------------

Visit our WebApp at [ISB-CGC.org](https://isb-cgc.appspot.com/)!

# Quick Start Guide to ISB-CGC

[ISB-CGC](https://isb-cgc.appspot.com/)

This Quick Start Guide gives an overview of the data available, account
set-up overview, and getting started with a basic example in R. If
you have read the python version, you can skip to the Example section.

## Access Requirements

-   Google Account to access ISB-CGC
-   [Google Cloud Account](https://console.cloud.google.com)

## Access Suggestions

-   Favored Programming Language (R or Python)
-   Favored IDE (RStudio or Jupyter)
-   Some knowledge of SQL

## Outline for this Notebook

-   Libraries Needed for this Notebook
-   Overview of ISB-CGC
-   Overview How to Access Data
-   Example of Accessing Data with Python
-   Where to go next

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
see fit.

### About the ISB-CGC Data in the Cloud

ISB-CGC hosts carefully curated, high-level clinical, biospecimen, and
molecular datasets and tables in Google BigQuery, including data from
programs such as [The Cancer Genome Atlas
(TCGA)](https://www.cancer.gov/about-nci/organization/ccg/research/structural-genomics/tcga),
[Therapeutically Applicable Research to Generate Effective Treatments
(TARGET)](https://ocg.cancer.gov/programs/target), and [Clinical
Proteomic Tumor Analysis Consortium
(CPTAC)](https://proteomics.cancer.gov/programs/cptac). For more
information about hosted data, please visit: [Programs and
DataSets](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/Hosted-Data.html)

## Overview of How to Access Data

There are several ways to access and explore the data hosted by ISB-CGC.
Though in this notebook, we will cover using Python and SQL to access
the data.

-   [ISB-CGC WebApp](https://isb-cgc.appspot.com/)
    -   Provides a graphical interface to file and case data
    -   Easy cohort creation
    -   Doesn’t require knowledge of programming languages
-   [ISB-CGC BigQuery Table
    Search](https://isb-cgc.appspot.com/bq_meta_search/)
    -   Provides a table search for available ISB-CGC BigQuery Tables
-   [ISB-CGC APIs](https://api-dot-isb-cgc.appspot.com/v4/swagger/)
    -   Provides programmatic access to metadata
-   [Google Cloud Platform](https://cloud.google.com/)
    -   Access and store data in [Google Cloud
        Storage](https://cloud.google.com/storage) and
        [BigQuery](https://cloud.google.com/bigquery) via User
        Interfaces or programmatically
-   Suggested Programming Languages and Programs to use
-   SQL
    -   Can be used directly in [BigQuery
        Console](https://console.cloud.google.com/bigquery)
    -   Or via API in Python or R
-   [Python](https://www.python.org/)
    -   [gsutil tool](https://cloud.google.com/storage/docs/gsutil)
    -   [Jupyter Notebooks](https://jupyter.org/)
    -   [Google Colabratory](https://colab.research.google.com/)
    -   [Cloud Datalab](https://cloud.google.com/datalab/)
-   [R](https://www.r-project.org/)
    -   [RStudio](https://rstudio.com/)
    -   [RStudio.Cloud](https://rstudio.cloud/)
-   Command Line Interfaces
    -   Cloud Shell via Project Console
    -   [CLOUD SDK](https://cloud.google.com/sdk/)

### Account Set-up

To run this notebook, you will need to have your Google Cloud Account
set up. If you need to set up a Google Cloud Account, follow the “Obtain
a Google identity” and “Set up a Google Cloud Project” steps on our
[Quick-Start Guide
documentation](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html)
page.

### ISB-CGC Web Interface

The [ISB-CGC Web Interface](https://isb-cgc.appspot.com/) is an
interactive web-based application to access and explore the rich TCGA,
TARGET, and CCLE datasets with more datasets regularly added. Through
WebApp, you can create Cohorts, lists of Favorite Genes, miRNA, and
Variables. The Cohorts and Variables can be used in Workbooks to allow
you to quickly analyze and export datasets by mixing and matching the
selections.

### Google Cloud Platform and BigQuery Overview

The [Google Cloud Platform Console](https://console.cloud.google.com/)
is the web-based interface to your GCP Project. From the Console, you
can check the overall status of your project, create and delete Cloud
Storage buckets, upload and download files, spin up and shut down VMs,
add members to your project, access the [Cloud Shell command
line](https://cloud.google.com/shell/docs/), etc. You’ll want to
remember that any costs that you incur are charged under your *current*
project, so you will want to make sure you are on the correct one if you
are part of multiple projects.

ISB-CGC has uploaded multiple cancer genomic and proteomic datasets into
BigQuery tables that are open-source such as TCGA and TARGET Clinical,
Biospecimen, and Molecular Data, along with case and file data. This
data can be accessed from the Google Cloud Platform Console User
Interface (UI), programmatically with R and python, or explored with our
[BigQuery Table Search
tool](https://isb-cgc.appspot.com/bq_meta_search/).

## Example of Accessing Data with R

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

### View ISB-CGC Datasets and Tables in BigQuery

Let us look at the datasets available through ISB-CGC that are in
BigQuery.

``` r
# Let us view which datasets are available from ISB-CGC through BigQuery
bq_project_datasets("isb-cgc-bq")[1:5]
```

    ## [[1]]
    ## <bq_dataset> isb-cgc-bq.0_README
    ## 
    ## [[2]]
    ## <bq_dataset> isb-cgc-bq.BEATAML1_0
    ## 
    ## [[3]]
    ## <bq_dataset> isb-cgc-bq.BEATAML1_0_versioned
    ## 
    ## [[4]]
    ## <bq_dataset> isb-cgc-bq.CBTTC
    ## 
    ## [[5]]
    ## <bq_dataset> isb-cgc-bq.CBTTC_versioned

The ISB-CGC has two datasets for each Program. One dataset contains the
most current data, and the other contains versioned tables, which serve
as an archive for reproducibility. The current tables are labeled with
"\_current" and are updated when new data is released. For more
information, visit our [ISB-CGC BigQuery
Projects](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/BigQuery/ISBCGC-BQ-Projects.html)
page.

Now, let us see which tables are under the TCGA dataset.

``` r
# Let us look which tables are in the TCGA dataset
bq_dataset_tables("isb-cgc-bq.TCGA")[1:5]
```

    ## [[1]]
    ## <bq_table> isb-cgc-bq.TCGA.DNA_methylation_chr10_hg19_gdc_current
    ## 
    ## [[2]]
    ## <bq_table> isb-cgc-bq.TCGA.DNA_methylation_chr10_hg38_gdc_current
    ## 
    ## [[3]]
    ## <bq_table> isb-cgc-bq.TCGA.DNA_methylation_chr11_hg19_gdc_current
    ## 
    ## [[4]]
    ## <bq_table> isb-cgc-bq.TCGA.DNA_methylation_chr11_hg38_gdc_current
    ## 
    ## [[5]]
    ## <bq_table> isb-cgc-bq.TCGA.DNA_methylation_chr12_hg19_gdc_current

### Query ISB-CGC BigQuery Tables

First, use a magic command to call to BigQuery. Then we can use Standard
SQL to write your query. Click
[here](https://googleapis.github.io/google-cloud-python/latest/bigquery/magics.html)
for more on IPython Magic Commands for BigQuery. The result will be a
[Pandas Dataframe](https://pandas.pydata.org/).

> Note: you will need to update PROJECT\_ID in the next cell to your
> Google Cloud Project ID.

``` r
project <- 'your_project_number' # Insert your project ID in the ''
if (project == 'your_project_number') {
  print('Please update the project number with your Google Cloud Project')
}
# Create the SQL query
sql <- "
SELECT # Select a few columns to view
  proj__project_id, # GDC project
  submitter_id, # case barcode
  proj__name # GDC project name
FROM # From the GDC TCGA Clinical Dataset
  `isb-cgc-bq.TCGA.clinical_gdc_current`
LIMIT # Limit to 5 rows as the dataset is very large and we only want to see a few results
  5"
# Use BigQuery to run the SQL query on the Clinical table from the TCGA dataset
# which then may be downloaded into a tibble.
result <- bq_project_query(project, sql)
```

    ## Complete

    ## Billed: 0 B

``` r
# Create a data frame with results
result <- bq_table_download(result)
```

    ## Downloading 5 rows in 1 pages.

``` r
# print the results
print(result)
```

    ## # A tibble: 5 x 3
    ##   proj__project_id submitter_id proj__name                           
    ##   <chr>            <chr>        <chr>                                
    ## 1 TCGA-HNSC        TCGA-CN-5363 Head and Neck Squamous Cell Carcinoma
    ## 2 TCGA-HNSC        TCGA-CN-5365 Head and Neck Squamous Cell Carcinoma
    ## 3 TCGA-HNSC        TCGA-CN-A642 Head and Neck Squamous Cell Carcinoma
    ## 4 TCGA-HNSC        TCGA-CR-7380 Head and Neck Squamous Cell Carcinoma
    ## 5 TCGA-HNSC        TCGA-CV-5978 Head and Neck Squamous Cell Carcinoma

Now that wasn’t so difficult! Have fun exploring and analyzing the
ISB-CGC Data!

## Where to Go Next

Access, Explore and Analyze Large-Scale Cancer Data Through the Google
Cloud! :)

Getting Started for Free: \* [Free Cloud Credits from ISB-CGC for Cancer
Research](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowtoRequestCloudCredits.html)
\* [Google Free Tier with up to 1TB of free queries a
month](https://cloud.google.com/free)

ISB-CGC Links:

-   [ISB-CGC Landing Page](https://isb-cgc.appspot.com/)
-   [ISB-CGC
    Documentation](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/)
-   [How to Get Started on
    ISB-CGC](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html)
-   [How to access Google
    BigQuery](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/progapi/bigqueryGUI/HowToAccessBigQueryFromTheGoogleCloudPlatform.html)
-   [Community Notebook
    Repository](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowTos.html)
-   [Query of the
    Month](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/QueryOfTheMonthClub.html)

Google Tutorials:

-   [Google’s What is
    BigQuery?](https://cloud.google.com/bigquery/docs/introduction)
-   [Google Cloud Client Library for
    Python](https://googleapis.github.io/google-cloud-python/latest/index.html)
