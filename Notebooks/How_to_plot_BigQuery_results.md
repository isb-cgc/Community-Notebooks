How to plot BigQuery results
================

    # ISB-CGC Community Notebooks
    # Check out more notebooks at our [Community Notebooks Repository](https://github.com/isb-cgc/Community-Notebooks)!
    Title:   How to visualize results from BigQuery
    Author:  David L Gibbs
    Created: 2019-07-17
    Purpose: Demonstrate how visualize the results from a query.
    URL:     https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_plot_BigQuery_results.Rmd
    Notes:   
    ***

\#How to visualize results from BigQuery

In this example, we’ll perform a few easy queries, and use the ggplot
library to visualize the results.

We will use theh bigrquery package to execute our SQL:
<https://github.com/r-dbi/bigrquery>

It is expected that you’re running the notebook in an interactive mode,
where you have access to a web browser for authorization with Google.

Library documentation: <https://ggplot2.tidyverse.org/>

There’s many tidyverse tutorials. For example,
<http://www.storybench.org/getting-started-with-tidyverse-in-r/>

``` r
#Function to check whether package is installed
#https://stackoverflow.com/questions/9341635/check-for-installed-packages-before-running-install-packages
is.installed <- function(mypkg){
    is.element(mypkg, installed.packages()[,1])
} 
  
if (!is.installed("bigrquery")){
    install.packages("bigrquery")
}

if (!is.installed("ggplot2")){
    install.packages("ggplot2")
}


if (!is.installed("dbplyr")){
  install.packages("dbplyr")
}

if (!is.installed("dplyr")){
  install.packages(dplyr)
}

if (!is.installed("dbplyr")){
  install.packages(DBI)
}
```

Getting setup

``` r
library(bigrquery)
library(ggplot2)
billing <- 'your_project_number' ### Replace with your project ID!! ### 
if (billing == 'your_project_number') {
  print('Please update the project number with your Google Cloud Project')
}
```

## Making barplots

The first time you run bq\_project\_query, you will be asked if you want
to authorize locally in the R session. By selecting ‘yes’, a browser tab
will open allowing google auth.

``` r
# We define queries as strings #
sql = "
SELECT
   icd_10,
   COUNT(*) as Count
FROM
   `isb-cgc.TCGA_bioclin_v0.Clinical`
GROUP BY
   1  -- this is the same as 'group by icd_10'
ORDER BY
   Count
"

tb <- bq_project_query(billing, sql)
```

    ## Complete

    ## Billed: 0 B

``` r
df <- bq_table_download(tb, max_results = 200)
```

    ## Downloading 168 rows in 1 pages.

``` r
df[1:5,]
```

    ## # A tibble: 5 x 2
    ##   icd_10 Count
    ##   <chr>  <int>
    ## 1 C71.8      1
    ## 2 C34.10     1
    ## 3 C34.90     1
    ## 4 C16.5      1
    ## 5 C80.1      1

Now we can make a bar plot with ggplot2.

``` r
df2 <- df[df$Count > 200,]
g <- ggplot(data=df2, aes(x=icd_10, y=Count))
g + geom_bar(stat="identity")
```

![](How_to_plot_BigQuery_results_files/figure-gfm/unnamed-chunk-4-1.png)<!-- -->

## Making scatter plots

``` r
sql = "
SELECT
   avg_percent_neutrophil_infiltration,
   avg_percent_lymphocyte_infiltration
FROM
   `isb-cgc.TCGA_bioclin_v0.Biospecimen`
GROUP BY
   1,2
"

tb3 <- bq_project_query(billing, sql)
```

    ## Complete

    ## Billed: 0 B

``` r
df3 <- bq_table_download(tb3, max_results = 200)
```

    ## Downloading 200 rows in 1 pages.

``` r
df3[1:5,]
```

    ## # A tibble: 5 x 2
    ##   avg_percent_neutrophil_infiltration avg_percent_lymphocyte_infiltration
    ##                                 <dbl>                               <dbl>
    ## 1                                  NA                                  NA
    ## 2                                   2                                   5
    ## 3                                   3                                   2
    ## 4                                   0                                   2
    ## 5                                   0                                   1

And now we make plot those results.

Note: It is always best practice to summarize within BigQuery, and plot
*summarized*
results.

``` r
g <- ggplot(data=df3, aes(x=avg_percent_lymphocyte_infiltration, y=avg_percent_neutrophil_infiltration))
g + geom_point()
```

    ## Warning: Removed 22 rows containing missing values (geom_point).

![](How_to_plot_BigQuery_results_files/figure-gfm/unnamed-chunk-5-1.png)<!-- -->

## Using dplyr

You can use dplyr to create SQL\! We’ll recreate the first query.

``` r
sql = "
SELECT
   icd_10,
   COUNT(*) as Count
FROM
   `isb-cgc.TCGA_bioclin_v0.Clinical`
GROUP BY
   1  -- this is the same as 'group by icd_10'
ORDER BY
   Count
"

library(dplyr)
library(DBI)

con <- dbConnect(
  bigrquery::bigquery(),
  project = "isb-cgc",
  dataset = "TCGA_bioclin_v0",
  billing = billing
)
con
```

    ## <BigQueryConnection>
    ##   Dataset: isb-cgc.TCGA_bioclin_v0
    ##   Billing: isb-cgc-02-0001

``` r
tcga_clinical <- tbl(con, "Clinical")

res4 <- tcga_clinical %>% select(icd_10) %>% group_by(icd_10) %>% tally()

head(res4)
```

    ## Complete

    ## Billed: 10.49 MB

    ## Downloading 6 rows in 1 pages.

    ## # Source:   lazy query [?? x 2]
    ## # Database: BigQueryConnection
    ##   icd_10     n
    ##   <chr>  <int>
    ## 1 <NA>     355
    ## 2 C71.9    652
    ## 3 C56.9    582
    ## 4 C34.3    347
    ## 5 C34.1    577
    ## 6 C34.2     37

And now we can plot the results\!

``` r
df3 <- res4 %>% filter(n > 200)
g <- ggplot(data=df3, aes(x=icd_10, y=n))
```

    ## Complete

    ## Billed: 10.49 MB

    ## Downloading 15 rows in 1 pages.

``` r
g + geom_bar(stat="identity")
```

![](How_to_plot_BigQuery_results_files/figure-gfm/unnamed-chunk-7-1.png)<!-- -->
