How to quickly compare cohorts
================

# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)\!

    Title:   How to quickly compare cohorts
    Author:  Lauren Hagen
    Created: 2020-04-09
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_quickly_compare_cohorts.md
    Purpose: Comparing cohorts with survival curves and histograms with data from BigQuery or the WebApp.
    Notes: 

# Overview

In this notebook, we will compare two cohorts with survival curves and
feature comparisons. We will be using data from the [Lung
Adenocarcinoma](https://portal.gdc.cancer.gov/projects/TCGA-LUAD) (LUAD)
and [Lung Squamous Cell
Carcinoma](https://portal.gdc.cancer.gov/projects/TCGA-LUSC) (LUSC)
projects from the TCGA program.

This notebook can handle multiple or different cohorts from the TCGA
program. The ‘Load Cohort’ code block can be updated to add or change
the cohorts.

# Authorization, install or load packages, and create client

Before we get started, we will need to load the BigQuery module,
authenticate ourselves, create a client variable, and import and load
necessary libraries. The package `tidyverse` has dplyr, stringr,
ggplot2, among other useful packages as part of it’s package, so we are
going to save time and just install and load the `tidyverse` package.
For more information, see the `tidyverse`
[site](https://www.tidyverse.org/).

``` r
library(bigrquery)
library(dplyr)
library(ggplot2)
library(stringr)
library(survival)
library(ggfortify)
project <- 'your_project_number' # Insert your project ID in the ''
if (project == 'your_project_number') {
  print('Please update the project number with your Google Cloud Project')
}
```

# Load Cohort

First we will need to load our cohort into a data frame. The cohort can
either be made using the WebApp or a SQL query to the TCGA clinical
tables. A cohort is a list of case barcodes from the TCGA program. The
first code block can be updated to include 2 or more cohorts. We are
going to use the sample queries filled in below as an example.

``` r
# Fill in how the cohort will be created
# SQL or File
cohort_type <- "SQL"

# Load a list of case_barcodes from our WebApp

file1 = 'your_first_file_location_here' # update with your file location, if using one
# Or insert a SQL query
query1 = "
  SELECT
    case_barcode
  FROM
   `isb-cgc.TCGA_bioclin_v0.Clinical`
  WHERE
    disease_code = 'LUAD'
  "
file2 = 'your_second_file_location_here' # update with your file location, if using one
# Or insert a SQL query
query2 = "
  SELECT
    case_barcode
  FROM
   `isb-cgc.TCGA_bioclin_v0.Clinical`
  WHERE
    disease_code = 'LUSC'
  "

# Update with files or queries used
cohorts <- data.frame(Cohort_1=query1, Cohort_2=query2)
```

``` r
# Function to create a combined labeled list of cohorts for comparison
load_cohort <- function(cohorts, cohort_type){
  final_list <- data.frame("case_barcodes" = NULL, "Cohort" = NULL)
  for (cohort in 1:ncol(cohorts)){
    if (cohort_type == "SQL") {
      cohort_request <- bq_project_query(project, cohorts[,cohort])
      cohort_table <- bq_table_download(cohort_request, quiet=TRUE)
    }
    else {
      cohort_table <- read.csv(cohorts[,cohort], skip = 1)
      cohort_table <- cohort_table$Case.Barcode
    }
    cohort_name <- names(cohorts[cohort])
    cohort_df <- data.frame("case_barcodes" = cohort_table, "cohort" = cohort_name)
    final_list <- rbind(final_list, cohort_df)
  }
  return(final_list)
}
```

``` r
combined_list <- load_cohort(cohorts, cohort_type)
```

    ## Complete

    ## Billed: 0 B

    ## Complete

    ## Billed: 0 B

# Survival Curve

First, we will compare groups with a survival curve. We will be using a
Kaplan Meier Curve from the [`survival`
package](https://cran.r-project.org/web/packages/survival/index.html)
and [`ggfortify`
package](https://cran.r-project.org/web/packages/ggfortify/index.html).

``` r
# Pull the vital status, days to death, and grouping column
# into a data frame
sc_query = str_c("
  SELECT
    case_barcode,
    vital_status,
    days_to_death
  FROM
    `isb-cgc.TCGA_bioclin_v0.Clinical`
  WHERE
    case_barcode IN ('", str_c(combined_list$case_barcode, collapse = "', '"),"') AND
    vital_status IS NOT NULL")
sc_query_request <- bq_project_query(project, sc_query)
```

    ## Complete

    ## Billed: 0 B

``` r
survival_curve <- bq_table_download(sc_query_request)
```

    ## Downloading 1,026 rows in 1 pages.

``` r
survival_curve <- left_join(survival_curve, combined_list, key = "case_barcode")
```

    ## Joining, by = "case_barcode"

``` r
# Fill in NAs in days_to_death with the max from the days to death
survival_curve$days_to_death[is.na(survival_curve$days_to_death)] <- max(survival_curve$days_to_death, na.rm = TRUE)
# Convert the vital status to numbers
survival_curve$vital_status <- ifelse(survival_curve$vital_status=='Alive', 0, 1)
```

``` r
fit <- survfit(Surv(days_to_death, vital_status) ~ cohort, data = survival_curve)
autoplot(fit) +
  labs(title = "Survival Curve",
       y = "Percent Survival", 
       x = "Days") +
  theme(legend.title=element_blank())
```

![](Cohort_Comparison_files/figure-gfm/unnamed-chunk-7-1.png)<!-- -->
\#\# Survival Curve Summary

We now have our two cohorts plotted with a survival curve. We can see
that the percent survival falls faster for Cohort 2 (LUSC) than Cohort 1
(LUAD). Below is a section on compare the case counts for different
features within the data.

Listed below are some useful resources on Survival Curves:
- [Kaplan-Meier Estimator Wikipedia](https://en.wikipedia.org/wiki/Kaplan%E2%80%93Meier_estimator)
- [Kaplan Meier curves: an introduction](https://towardsdatascience.com/kaplan-meier-curves-c5768e349479)
- [Nature: A practical guide to understanding Kaplan-Meier curves by Rich J, Neely J, Paniello R, Voelker C, Nussenbaum B, Wang E](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3932959/)

# Feature Comparisons

We may also like to view the distribution of the patient’s ages, gender,
and vital status between the two data sets. We can do this by creating
bar charts for each feature.

First, we will get the data from BigQuery for the desired features.

``` r
# Create a query to retrieve the cohort features
hist_query = str_c("
  SELECT
    case_barcode,
    gender,
    vital_status,
    age_at_diagnosis,
    ethnicity,
    pathologic_stage
  FROM
    `isb-cgc.TCGA_bioclin_v0.Clinical`
  WHERE
    case_barcode IN ('", str_c(combined_list$case_barcode, collapse = "', '"),"')
  ")

hist_query_request <- bq_project_query(project, hist_query)
```

    ## Complete

    ## Billed: 0 B

``` r
compare_download <- bq_table_download(hist_query_request)
```

    ## Downloading 1,089 rows in 1 pages.

``` r
compare <- left_join(compare_download, combined_list, key = "case_barcode")
```

    ## Joining, by = "case_barcode"

Next we will want to view if there are any missing values in our
cohorts.

``` r
# View the number of missing records in the data set
colSums(is.na(compare))
```

    ##     case_barcode           gender     vital_status age_at_diagnosis        ethnicity pathologic_stage           cohort 
    ##                0               63               63               91              366               75                0

Then, we will plot the feature on bar charts.

``` r
# Create Age at Diagnosis Comparison
age_graph <- ggplot(data = compare, mapping = aes(age_at_diagnosis, fill = cohort)) +
  geom_histogram(bins = 10) +
  labs(title = "Age at Diagnosis Comparison",
       x = "Age at Diagnosis",
       y = "Count of Cases")
age_graph
```

    ## Warning: Removed 91 rows containing non-finite values (stat_bin).

![](Cohort_Comparison_files/figure-gfm/unnamed-chunk-10-1.png)<!-- -->

``` r
# Create Gender Comparison graph
gender_graph <- ggplot(data = compare, mapping = aes(ethnicity, fill=cohort)) +
  geom_bar(position = "dodge") +
  labs(title = "Ethnicity Comparison",
    x = "Ethnicity",
    y = "Count of Cases")
gender_graph
```

![](Cohort_Comparison_files/figure-gfm/unnamed-chunk-11-1.png)<!-- -->

``` r
# Create Gender Comparison graph
gender_graph <- ggplot(data = compare, mapping = aes(gender, fill=cohort)) +
  geom_bar(position = "dodge") +
  labs(title = "Gender Comparison",
    x = "Gender",
    y = "Count of Cases")
gender_graph
```

![](Cohort_Comparison_files/figure-gfm/unnamed-chunk-12-1.png)<!-- -->

``` r
# Create Vital Status Comparison graph
vital_status_graph <- ggplot(data = compare, mapping = aes(vital_status, fill=cohort)) +
  geom_bar(position = "dodge") +
  labs(title = "Vital Status Comparison",
    x = "Vital Status",
    y = "Count of Cases")
vital_status_graph
```

![](Cohort_Comparison_files/figure-gfm/unnamed-chunk-13-1.png)<!-- -->

``` r
# Create Pathology Status Comparison graph
pathology_status_graph <- ggplot(data = compare, mapping = aes(pathology_status, fill=cohort)) +
  geom_bar(position = "dodge") +
  labs(title = "Pathology Status Comparison",
    x = "Pathology Status",
    y = "Count of Cases")
vital_status_graph
```

![](Cohort_Comparison_files/figure-gfm/unnamed-chunk-14-1.png)<!-- -->

# That’s all folks\!

So, that’s it for a quick cohort comparison. If you need help or have a
comment, reach out to us at <feedback@isb-cgc.org>

This notebook was inspired by the [ICGC Cohort Comparison Analysis
tool](https://dcc.icgc.org/analysis)
