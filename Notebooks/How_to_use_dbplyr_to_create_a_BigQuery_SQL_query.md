# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)\!

    Title:   How to use dbplyr to build a query
    Author:  Lauren Hagen
    Created: 2020-02-26
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_use_dbplyr_to_create_a_BigQuery_SQL_query.Rmd
    Purpose: Demonnstrate query creation using dbplyr and use query with BigQuery
    Notes: 

-----

# Introduction

## Overview

In this notebook, we are going to use the dbplyr package to build SQL
for BigQuery. We are going to create a cohort by selecting on clinical
signs and then filter the RNA and miRNA gene expression tables from the
TARGET data set.

## What is dbplyr?

The [dbplyr package](https://dbplyr.tidyverse.org/articles/dbplyr.html)
allows the use of dplyr with databases like BigQuery. It is part of the
[tidyverse package](https://www.tidyverse.org/) set and uses the DBI
backend package to communicate with several different types of
databases.

Before we get started, we will need to load the BigQuery module,
authenticate ourselves, create a client variable, and load necessary
libraries.

``` r
# install.packages("dbplyr")
library(bigrquery)
library(dplyr)
library(dbplyr)
```

``` r
billing <- 'your_project_number' # Insert your project ID in the ''
if (billing == 'your_project_number') {
  print('Please update the project number with your Google Cloud Project')
}
```

``` r
# Connect to BigQuery
con <- dbConnect(
  bigrquery::bigquery(),
  project = billing,
)
```

# Query Building

In this notebook, we will query each table first and then join them for
a final query. The result will be a selection of clinical and molecular
data from the TARGET data set.

## Patient Clinical Data Query

We want a query that filters the TARGET data set for AML selecting only
columns for the case barcode and the remission status of the patient for
our
cohort.

``` r
# Pass the Clincal data table name to the Table class to create a variable
clin <- tbl(con, "isb-cgc.TARGET_bioclin_v0.Clinical")
```

``` r
# Create a query with dplyr pipes
clin_query <- clin %>% # Use the Clinical Table
  filter(disease_code=='AML') %>% # Filter for the AML disease type
  select(case_barcode, CR_status_at_end_of_course_1, CR_status_at_end_of_course_2) # Selected fields

# Display the SQL query without quering BigQuery to check the query
# We can also cpy the query into the BigQuery UI to check for errors
show_query(clin_query)
```

    ## <SQL>
    ## SELECT `case_barcode`, `CR_status_at_end_of_course_1`, `CR_status_at_end_of_course_2`
    ## FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
    ## WHERE (`disease_code` = 'AML')

We can now query BigQuery, then create a data frame with the results
though this isn’t necessary for creating the final query.

``` r
# Query BigQuery and return a data frame
clin_data <- collect(clin_query)
```

    ## Complete

    ## Billed: 0 B

    ## Downloading 993 rows in 1 pages.

``` 
## Parsing [===========================================================================================================] ETA:  0s                                                                                                                              
```

``` r
# View the first few lines of the data frame
head(clin_data)
```

    ## # A tibble: 6 x 3
    ##   case_barcode     CR_status_at_end_of_course_1 CR_status_at_end_of_course_2
    ##   <chr>            <chr>                        <chr>                       
    ## 1 TARGET-20-PATDMY CR                           CR                          
    ## 2 TARGET-20-PARHSA CR                           CR                          
    ## 3 TARGET-20-PARLSW CR                           CR                          
    ## 4 TARGET-20-PASLHH CR                           CR                          
    ## 5 TARGET-20-PATKUG CR                           CR                          
    ## 6 TARGET-20-PANSBH CR                           CR

## Molecular Data Query

Now that we have a list of cases with some clinical information, we can
join that table to one of the molecular data sets, such as the TARGET
gene expression data.

We’ll build the query using the molecular data set. While We’re not
going to query BigQuery, it is good to make sure the query looks correct
before joining it with another
table.

``` r
# Pass the Clincal data table name to the Table class to create a variable
expr <- tbl(con, "isb-cgc.TARGET_hg38_data_v0.RNAseq_Gene_Expression")
```

``` r
# Create a query with dplyr pipes and display the query
expr_query <- expr %>%
  select(case_barcode, HTSeq__FPKM_UQ, Ensembl_gene_id, gene_name) %>%
  arrange(HTSeq__FPKM_UQ) %>%
  show_query()
```

    ## <SQL>
    ## SELECT `case_barcode`, `HTSeq__FPKM_UQ`, `Ensembl_gene_id`, `gene_name`
    ## FROM `isb-cgc.TARGET_hg38_data_v0.RNAseq_Gene_Expression`
    ## ORDER BY `HTSeq__FPKM_UQ`

# Create the Final Query

Finally, we will create a query to join the two tables. BigQuery and
PyPika support all join types, though, for this query, we are using the
standard inner join. This query returns a large number of lines and can
be slow to bring into Collaboratory, so we will limit the number of
lines returned to 100.

``` r
final <- inner_join(clin_query, expr_query, by = "case_barcode") %>%
  head(100) %>%
  show_query()
```

    ## <SQL>
    ## SELECT *
    ## FROM (SELECT `LHS`.`case_barcode` AS `case_barcode`, `LHS`.`CR_status_at_end_of_course_1` AS `CR_status_at_end_of_course_1`, `LHS`.`CR_status_at_end_of_course_2` AS `CR_status_at_end_of_course_2`, `RHS`.`HTSeq__FPKM_UQ` AS `HTSeq__FPKM_UQ`, `RHS`.`Ensembl_gene_id` AS `Ensembl_gene_id`, `RHS`.`gene_name` AS `gene_name`
    ## FROM (SELECT `case_barcode`, `CR_status_at_end_of_course_1`, `CR_status_at_end_of_course_2`
    ## FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
    ## WHERE (`disease_code` = 'AML')) `LHS`
    ## INNER JOIN (SELECT `case_barcode`, `HTSeq__FPKM_UQ`, `Ensembl_gene_id`, `gene_name`
    ## FROM `isb-cgc.TARGET_hg38_data_v0.RNAseq_Gene_Expression`
    ## ORDER BY `HTSeq__FPKM_UQ`) `RHS`
    ## ON (`LHS`.`case_barcode` = `RHS`.`case_barcode`)
    ## ) `dbplyr_019`
    ## LIMIT 100

There\! We now have a query that joins the two tables. We can now query
BigQuery and view the
results.

``` r
final_data <- collect(final)
```

    ## Complete

    ## Billed: 1.56 GB

    ## Downloading 100 rows in 1 pages.

``` 
## Parsing [===========================================================================================================] ETA:  0s                                                                                                                              
```

``` r
head(final)
```

    ## Complete

    ## Billed: 1.56 GB

    ## Downloading 6 rows in 1 pages.

    ## Parsing [===========================================================================================================] ETA:  0s                                                                                                                              # Source:   lazy query [?? x 6]
    ## # Database: BigQueryConnection
    ##   case_barcode     CR_status_at_end_of_course_1 CR_status_at_end_of_course_2 HTSeq__FPKM_UQ Ensembl_gene_id gene_name
    ##   <chr>            <chr>                        <chr>                                 <dbl> <chr>           <chr>    
    ## 1 TARGET-20-PAPWHS CR                           CR                                     185. ENSG00000115194 SLC30A3  
    ## 2 TARGET-20-PAPWHS CR                           CR                                   54903. ENSG00000103489 XYLT1    
    ## 3 TARGET-20-PAPWHS CR                           CR                                   48156. ENSG00000104450 SPAG1    
    ## 4 TARGET-20-PAPWHS CR                           CR                                  144367. ENSG00000099864 PALM     
    ## 5 TARGET-20-PAPWHS CR                           CR                                   29986. ENSG00000215199 YWHAZP6  
    ## 6 TARGET-20-PAPWHS CR                           CR                                  105783. ENSG00000164941 INTS8

It’s that simple! Please let us know if you have any questions at
<feedback@isb-cgc.org>.
