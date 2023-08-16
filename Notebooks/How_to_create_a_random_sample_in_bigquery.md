How to Create a Random Sample in BigQuery
================

# ISB-CGC Community Notebooks

    Title:   How to Create a Random Sample in BigQuery
    Author:  Lauren Hagen
    Created: 2019-10-17
    Purpose: Demonstrates how to split a data set into multiple groups randomly with BigQuery

# How to Create a Random Sample in BigQuery

In this notebook, we will be using BigQuery to create random samples for
predicting an outcome with test and training data sets such as in
machine learning. In this notebook, we assume that you have set up your
GCP and accessed the ISB-CGC WebApp. If not, please visit the [How To
Get Started on
ISB-CGC](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html)
or the [Community Notebook
Repository](https://github.com/isb-cgc/Community-Notebooks) for guides
on how to get started.

We will go over two methods to create the subset data: - `RAND()`
Function - `MOD()` and `FARM_FINGERPRINT` Functions

Before we can begin working with BigQuery, we will need to load the
BigQuery library and create a GCP variable.

``` r
library(bigrquery)
project <- 'your_project_number' # Insert your project ID in the ''
if (project == 'your_project_number') {
  print('Please update the project number with your Google Cloud Project')
}
```

## `RAND()` Function for Randomly Splitting data

A simple way to create a random sample with BigQuery is to use the
`RAND()` function. The `RAND()` function creates a seemingly random set
of numbers and then the query can select to create a random sample of
rows.

We will create two queries with the `RAND()` function. The first will
return a random sample of the data and the second will return all of a
cohort with the rows labeled for which subset they belong to.

We are going to start with a simple query to create a cohort. Cohorts
can be created previously in the WebApp or through other means instead
of within this query. For more information on creating cohorts, please
see the [ISB-CGC Web Interface (Web App)
documentation](https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/Web-UI.html)
and the [Community Notebook
Repository](https://github.com/isb-cgc/Community-Notebooks).

``` r
# Create a query with the cohort information
# This can be replaced with your own cohort
cohort_query <- "SELECT case_barcode, project_short_name, case_gdc_id
            FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
            WHERE project_short_name = 'TARGET-NBL'"
# Run the query
cohort <- bq_project_query(project, cohort_query, quiet = TRUE) 
# Create a dataframe with the results from the query
cohort <- bq_table_download(cohort, quiet = TRUE)
# Show the dataframe
str(cohort)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    1180 obs. of  3 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PATSRD" "TARGET-30-PATTEF" "TARGET-30-PARJAR" "TARGET-30-PAUAZA" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fef92ed0-242b-5564-ad92-6b35c21c3bd5" "fef13b6c-d5e9-5ffa-9f55-2404f2f99eeb" "feb97edc-ce83-5fd5-94e3-261ce244ac52" "fe831368-c7ce-5e2b-b0fd-c35216a7761d" ...

The next part of the query is creating the random sample. This line can
be adjusted to return any percent of the data table into a random
sample. For this example, it is set to create a random sample of \~25%
of the data.

``` r
# Create Query
sample_query <- "--- Create Cohort
            WITH table1 AS (
            SELECT case_barcode, project_short_name, case_gdc_id, 0 as table_num
            FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
            WHERE project_short_name = 'TARGET-NBL')

            --- Select a random sample that is ~25% of the data
            SELECT case_barcode, project_short_name, case_gdc_id, 1 as table_num
            FROM table1
            -- Count the number of rows in the cohort, then find how many of them will be 25%
            -- of the cohort. Divid that number by the total number of rows in the data 
            -- To change the %, change the 0.25 to what ever precentage you need
            WHERE RAND() < ((SELECT COUNT(*) FROM table1)*0.25)/(SELECT COUNT(*) FROM table1)"
# Run the query
sample <- bq_project_query(project, sample_query, quiet = TRUE) 
# Create a dataframe with the results from the query
sample <- bq_table_download(sample, quiet = TRUE)
# Show the dataframe
str(sample)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    318 obs. of  4 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PASWIJ" "TARGET-30-PANBMJ" "TARGET-30-PARABN" "TARGET-30-PAPRXW" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fe0b727f-3843-5b70-b9c1-8a207b837fc4" "fdfb389d-eb9a-5014-b391-9cd5f908720d" "fc9d0307-a5f5-51c4-ad9e-6e9ed60f0eba" "fc3288a3-ad98-5be3-ab70-e02bf4b8fc7c" ...
    ##  $ table_num         : int  1 1 1 1 1 1 1 1 1 1 ...

This query is nice if we just wanted to grab a smaller sample of the
cohort to do some initial analysis before moving to a larger data set
but it is not useful if you want to create two separate subsets of data
for training a model and then testing the model. The final query joins
the new random sample table back with the main table and preserving the
split of data with a column for which subset it belongs to.

``` r
dataset_query <- "--- Create Cohort
            WITH table1 AS (
            SELECT case_barcode, project_short_name, case_gdc_id, 0 as table_num
            FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
            WHERE project_short_name = 'TARGET-NBL'),

            --- Select a random sample that is ~25% of the data
            table2 AS (
            SELECT case_barcode, project_short_name, case_gdc_id, 1 as table_num
            FROM table1
            -- Count the number of rows in the cohort, then find how many of them will be 25%
            -- of the cohort. Divid that number by the total number of rows in the data
            -- To change the %, change the 0.25 to what ever precentage you need
            WHERE RAND() < ((SELECT COUNT(*) FROM table1)*0.25)/(SELECT COUNT(*) FROM table1)
            )

            --- Join the random sample table back to the main table
            SELECT a.case_barcode, a.project_short_name, a.case_gdc_id, IFNULL(b.table_num,2) AS table_num
            FROM table1 AS a
            FULL OUTER JOIN table2 AS b
            ON a.case_barcode = b.case_barcode"
# Run the query
dataset <- bq_project_query(project, dataset_query, quiet = TRUE) 
# Create a dataframe with the results from the query
dataset <- bq_table_download(dataset, quiet = TRUE)
# Show the dataframe
str(dataset)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    1180 obs. of  4 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PATHKB" "TARGET-30-PATCEM" "TARGET-30-PAISSH" "TARGET-30-PATFTN" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fba62f88-d514-5edb-a1fb-0e05fe967191" "d183c0ca-3de1-5522-9f25-427ef4f62998" "c72527a8-e976-5de2-a015-0f4af62e3041" "944b68d2-c55d-53f1-a940-fae1e59a224e" ...
    ##  $ table_num         : int  2 2 2 2 2 2 2 2 1 2 ...

Each query will have a different set of random samples because each time
`RAND()` is run, it generates a new set of random numbers. This could be
a problem if you want reproducible results each time you run the query.
Another way to solve this problem is to use `FARM_FINGERPRINT()` with
`MOD()` which we will cover next.

## `MOD()` and `FARM_FINGERPRINT` Functions

`FARM_FINGERPRINT()` will compute a string of BYTES or STRING and will
never change. The `MOD()` function will return the remainder of the farm
fingerprint number and a number. This method will always return the same
values for each subset.

For example, we want three approximately equal subsets of the data sets
of our cohort. We will create a `WHERE` statement that has the
`case_barcode` in the `FARM_FINGERPRINT` function, take the absolute
value, put that number into the `MOD()`, and set that equal to 0.

Note: You need to run `FARM_FINGERPRINT()` on a column that has unique
values for each row or combine two columns with `CONCAT` to create a
unique value row.

For more information visit the BigQuery documentation: -
[`FARM_FINGERPRINT()`](https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-and-operators#farm_fingerprint)
-
[`MOD()`](https://cloud.google.com/dataprep/docs/html/MOD-Function_57344691)

``` r
mod_query_1 <- "SELECT case_barcode, project_short_name, case_gdc_id
              FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
              WHERE project_short_name = 'TARGET-NBL' AND MOD(ABS(FARM_FINGERPRINT(case_barcode)),3) = 0"
# Run the query
mod_1 <- bq_project_query(project, mod_query_1, quiet = TRUE) 
# Create a dataframe with the results from the query
mod_1 <- bq_table_download(mod_1, quiet = TRUE)
# Show the dataframe
str(mod_1)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    372 obs. of  3 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PATTEF" "TARGET-30-PARJAR" "TARGET-30-PANUVK" "TARGET-30-PARZHA" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fef13b6c-d5e9-5ffa-9f55-2404f2f99eeb" "feb97edc-ce83-5fd5-94e3-261ce244ac52" "fd756a5f-0f9a-57ca-9879-2b18e5fa0b54" "fc9d5f9e-af43-5134-95e7-2d434831580b" ...

The three in the `MOD()` statement is what splits the cohort into three
subsets. If we wanted to do \~20% split of the data, we would change the
three to a ten and then take any row that less than or equal to 1.

``` r
mod_query_2 <- "SELECT case_barcode, project_short_name, case_gdc_id
                  FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
                  WHERE project_short_name = 'TARGET-NBL' AND MOD(ABS(FARM_FINGERPRINT(case_barcode)),10) <= 1"
# Run the query
mod_2 <- bq_project_query(project, mod_query_2, quiet = TRUE) 
# Create a dataframe with the results from the query
mod_2 <- bq_table_download(mod_2, quiet = TRUE)
# Show the dataframe
str(mod_2)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    221 obs. of  3 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PASWIJ" "TARGET-30-PARABN" "TARGET-30-PAPRXW" "TARGET-30-PAREAG" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fe0b727f-3843-5b70-b9c1-8a207b837fc4" "fc9d0307-a5f5-51c4-ad9e-6e9ed60f0eba" "fc3288a3-ad98-5be3-ab70-e02bf4b8fc7c" "fb071e74-40dc-5f67-b4c3-e61dd2c2ef88" ...

With this method, we can also create a query that will retrieve the
remaining subset of data. For the first example, we would change the `=`
to `!=` as shown below:

``` r
mod_query_3 <- "SELECT case_barcode, project_short_name, case_gdc_id
              FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
              WHERE project_short_name = 'TARGET-NBL' AND MOD(ABS(FARM_FINGERPRINT(case_barcode)),3) != 0"
# Run the query
mod_3 <- bq_project_query(project, mod_query_3, quiet = TRUE) 
# Create a dataframe with the results from the query
mod_3 <- bq_table_download(mod_3, quiet = TRUE)
# Show the dataframe
str(mod_3)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    808 obs. of  3 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PATSRD" "TARGET-30-PAUAZA" "TARGET-30-PAIJGC" "TARGET-30-PASWIJ" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fef92ed0-242b-5564-ad92-6b35c21c3bd5" "fe831368-c7ce-5e2b-b0fd-c35216a7761d" "fe58a8bf-8306-5aaf-99d1-b65c20fedc58" "fe0b727f-3843-5b70-b9c1-8a207b837fc4" ...

For the second example, we would change the `<=` to `>` as shown below:

``` r
mod_query_4 <- "SELECT case_barcode, project_short_name, case_gdc_id
                  FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
                  WHERE project_short_name = 'TARGET-NBL' AND MOD(ABS(FARM_FINGERPRINT(case_barcode)),10) > 1"
# Run the query
mod_4 <- bq_project_query(project, mod_query_4, quiet = TRUE) 
# Create a dataframe with the results from the query
mod_4 <- bq_table_download(mod_4, quiet = TRUE)
# Show the dataframe
str(mod_4)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    959 obs. of  3 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PATSRD" "TARGET-30-PATTEF" "TARGET-30-PARJAR" "TARGET-30-PAUAZA" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fef92ed0-242b-5564-ad92-6b35c21c3bd5" "fef13b6c-d5e9-5ffa-9f55-2404f2f99eeb" "feb97edc-ce83-5fd5-94e3-261ce244ac52" "fe831368-c7ce-5e2b-b0fd-c35216a7761d" ...

If you want to label the entire cohort and only create one query instead
of two, a column can be added to label each case with the subset
number.

``` r
mod_query_5 <- "SELECT case_barcode, project_short_name, case_gdc_id, MOD(ABS(FARM_FINGERPRINT(case_barcode)),3) as subset
                  FROM `isb-cgc.TARGET_bioclin_v0.Clinical`
                  WHERE project_short_name = 'TARGET-NBL'"
# Run the query
mod_5 <- bq_project_query(project, mod_query_5, quiet = TRUE) 
# Create a dataframe with the results from the query
mod_5 <- bq_table_download(mod_5, quiet = TRUE)
# Show the dataframe
str(mod_5)
```

    ## Classes 'tbl_df', 'tbl' and 'data.frame':    1180 obs. of  4 variables:
    ##  $ case_barcode      : chr  "TARGET-30-PATSRD" "TARGET-30-PATTEF" "TARGET-30-PARJAR" "TARGET-30-PAUAZA" ...
    ##  $ project_short_name: chr  "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" "TARGET-NBL" ...
    ##  $ case_gdc_id       : chr  "fef92ed0-242b-5564-ad92-6b35c21c3bd5" "fef13b6c-d5e9-5ffa-9f55-2404f2f99eeb" "feb97edc-ce83-5fd5-94e3-261ce244ac52" "fe831368-c7ce-5e2b-b0fd-c35216a7761d" ...
    ##  $ subset            : int  1 0 0 2 2 1 2 2 1 2 ...

The subsets can then be filtered out and manipulated in python. Have fun
random sampling the data\! Please let us know if you have questions by
emailing us at <feedback@isb-cgc.org>.
