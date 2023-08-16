How to make a heatmap using BigQuery
================

# ISB-CGC Community Notebooks

Check out more notebooks at our [Community Notebooks
Repository](https://github.com/isb-cgc/Community-Notebooks)\!

    Title:   How to make a heatmap using BigQuery 
    Author:  Lauren Hagen
    Created: 2020-02-21
    Purpose: Demonstrate how to make a correlation matrix and create a heatmap visualization.
    Notes:   Adapted from the How to make a heatmap using BigQuery python notebook by David L Gibbs
    Repo:    https://github.com/isb-cgc/Community-Notebooks/blob/master/Notebooks/How_to_make_a_heatmap_using_BigQuery.md

In this notebook, we will cover how to use BigQuery to pull some data,
make a correlation (or distance) matrix, and visualize that result in a
heatmap.

It is also possible to compute the correlations *inside* BigQuery, which
is a good use of the technology, but for simplicity’s sake, we will use
R.

The methods are used in cancer data analysis (see practically all TCGA
studies) but can apply to any data. Here we will be using TCGA gene
expression data from two studies, KIRC (kidney cancer) and GBM (brain
cancer).

In this work, we will see if the two tissue types separate into
clusters.

# Google Auth & Load packages

Before we can begin working with BigQuery, we will need to load the
BigQuery library and create a GCP variable.

``` r
library(bigrquery)
project <- 'your_project_number' # Insert your project ID in the ''
if (project == 'your_project_number') {
  print('Please update the project number with your Google Cloud Project')
}
```

We will also need to load the heatmap packages and dplyr.

``` r
library(tidyverse)
library(stringr)
library(pheatmap)
library(RColorBrewer)
```

# Query for data

OK, we’re going to query for some data using a preselected gene set from
MSigDB.

<http://software.broadinstitute.org/gsea/msigdb/cards/HALLMARK_TGF_BETA_SIGNALING.html>

``` r
genes <- read.delim('https://www.gsea-msigdb.org/gsea/msigdb/download_geneset.jsp?geneSetName=HALLMARK_TGF_BETA_SIGNALING&fileType=txt', skip = 1)
```

So, now that we have our list of genes, we will create a SQL string to
communicate to the Google mothership.

Here, the SQL is captured as a string. Using the Google BigQuery web
interface is a good place to prototype SQL.

``` r
sql = str_c("
SELECT project_short_name, sample_barcode, HGNC_gene_symbol, normalized_count 
FROM `isb-cgc.TCGA_hg19_data_v0.RNAseq_Gene_Expression_UNC_RSEM`
WHERE project_short_name IN ('TCGA-KIRC', 'TCGA-GBM')
AND HGNC_gene_symbol IN ('", str_c(genes[1:10,1], collapse = "', '"), "') 
GROUP BY 1,2,3,4")
```

Now we use the client, send off the SQL, and convert the results to a
dataframe.

``` r
result <- bq_project_query(project, sql, quiet = TRUE)
dat <- bq_table_download(result, quiet = TRUE)
head(dat)
```

    ## # A tibble: 6 x 4
    ##   project_short_name sample_barcode   HGNC_gene_symbol normalized_count
    ##   <chr>              <chr>            <chr>                       <dbl>
    ## 1 TCGA-GBM           TCGA-12-0616-01A ACVR1                       575. 
    ## 2 TCGA-KIRC          TCGA-BP-4343-01A ACVR1                      1229. 
    ## 3 TCGA-KIRC          TCGA-B0-5117-01A APC                         573. 
    ## 4 TCGA-KIRC          TCGA-AK-3453-01A CDKN1C                       42.5
    ## 5 TCGA-KIRC          TCGA-CJ-4644-01A BMPR1A                      497. 
    ## 6 TCGA-KIRC          TCGA-CW-5587-01A BMPR2                      4710.

# Converting tidy data to a matrix, and computing a correlation matrix

``` r
mat <- dat %>%
  select(-project_short_name) %>%
  group_by(sample_barcode, HGNC_gene_symbol) %>%
  summarise(genes = max(normalized_count)) %>%
  pivot_wider(names_from = HGNC_gene_symbol, values_from = genes)
head(mat)
```

    ## # A tibble: 6 x 11
    ## # Groups:   sample_barcode [6]
    ##   sample_barcode   ACVR1   APC ARID4B BCAR3  BMP2 BMPR1A BMPR2   CDH1  CDK9 CDKN1C
    ##   <chr>            <dbl> <dbl>  <dbl> <dbl> <dbl>  <dbl> <dbl>  <dbl> <dbl>  <dbl>
    ## 1 TCGA-02-0047-01A  989. 3389.   687.  122.  287.   903. 2020. 265.    954.   269.
    ## 2 TCGA-02-0055-01A 1309.  683.   630. 1501.  986.   423. 1219.   2.24 1166.   227.
    ## 3 TCGA-02-2483-01A  603. 1136.   885.  134.  287.   622. 1447.  19.0  1939.   274.
    ## 4 TCGA-02-2485-01A  801. 2499.   711.  624.  194.   394. 1628. 112.   1120    117.
    ## 5 TCGA-02-2486-01A  693. 1296.   509.  270.  199.   352. 1331.   9.15 1351.   313.
    ## 6 TCGA-06-0125-01A  629. 3077.   838.  171.  435.   727. 1984.  17.5   895.   229.

Let’s choose a smaller set of samples, to speed things up.

``` r
set.seed(10)
matSample <- sample_n(data.frame(mat), 60, replace = FALSE)
rownames(matSample) <- matSample[,1]
matSample <- matSample[-1]
head(matSample)
```

    ##                      ACVR1       APC    ARID4B    BCAR3     BMP2   BMPR1A    BMPR2      CDH1
    ## TCGA-BP-4770-01A 1995.5634  337.6180  844.0450 462.4515 326.9788 461.0330 3130.059   19.1506
    ## TCGA-CJ-5684-01A  862.2079  970.5882  780.0242 631.9380 602.7397 441.9823 3170.024 1786.8654
    ## TCGA-B0-5110-01A  910.8398 1968.5535 1325.2793 575.5901 980.7621 620.7917 4931.927  908.2501
    ## TCGA-B0-5707-01A 1009.6061  457.7329  536.9837 665.6388 811.7195 378.4822 1372.718 2036.0231
    ## TCGA-BP-4331-01A  650.9347  913.2700  860.1318 292.0625 334.0484 336.5002 2280.417 1412.8103
    ## TCGA-BP-4158-01A  720.0864  993.9525 1103.4212 520.5184 274.7300 420.3024 2824.190 2347.3002
    ##                       CDK9   CDKN1C
    ## TCGA-BP-4770-01A 1382.7442 167.0358
    ## TCGA-CJ-5684-01A 1051.5713 458.0983
    ## TCGA-B0-5110-01A 1015.5383 174.9908
    ## TCGA-B0-5707-01A 1078.7704 421.7099
    ## TCGA-BP-4331-01A 1051.1799 288.9979
    ## TCGA-BP-4158-01A  967.6026 490.7127

Now we’ll compute the correlations:

``` r
cormat <- cor(t(matSample), use = "pairwise.complete.obs")
```

and make a heatmap with the basic built-in stats package:

``` r
# Unsorted heatmap with basic built-in stats package
heatmap(cormat, Rowv = NA, Colv = NA)
```

![](How_to_make_a_heatmap_using_BigQuery_files/figure-gfm/unnamed-chunk-9-1.png)<!-- -->

We can also use `heatmap()` to create clustered heatmaps with colored
side labels.

``` r
# create a data frame to label each sample in the matrix
label <- unique.data.frame(dat[,1:2])
# Create a new data frame for the labeled data and add a column with the sample_barcodes
cormat_lab <- as.data.frame(cormat)
cormat_lab$sample_barcode <- as.character(rownames(cormat))
# Join the project names to label data
cormat_lab <- left_join(cormat_lab, label, key = "sample_barcode")
# Create a vector with the project names as numeric
my_group <- as.numeric(as.factor(cormat_lab$project_short_name))
# Set the color pallet for the project names
colSide <- brewer.pal(9, "Set1")[my_group]
# Create the heatmap
heatmap(cormat, ColSideColors = colSide)
```

![](How_to_make_a_heatmap_using_BigQuery_files/figure-gfm/unnamed-chunk-10-1.png)<!-- -->

Cool\! The tissue types separated out, and it looks like KIRC (blue bar)
clusters into two groups.

There are several packages to give more options for creating heatmaps.
We are going to explore `pheatmap` from the `pheatmap` package, but
there is also `heatmap.2` from the `gplots` package and `superheat` from
the `superheat` package.

First, we will make a basic heat map with
`pheatmap`:

``` r
pheatmap(cormat, fontsize_col = 5, fontsize_row = 4, cluster_row = FALSE, cluster_cols = FALSE)
```

![](How_to_make_a_heatmap_using_BigQuery_files/figure-gfm/unnamed-chunk-11-1.png)<!-- -->

Now, lets add some clustering to the
heatmap:

``` r
# Create a dataframe with the study as factors and the sample barcodes as the row names
annot <- data.frame(Study = factor(cormat_lab$project_short_name))
rownames(annot) <- cormat_lab$sample_barcode
# Define a list for the annotation labels
ann_colors <- list(
  Study = c("TCGA-KIRC" = "#377EB8", "TCGA-GBM" = "#E41A1C")
)
# Create heatmap
pheatmap(cormat, fontsize_col = 5, fontsize_row = 4, 
         annotation_row = annot, annotation_names_row = FALSE,
         annotation_colors = ann_colors,
         cutree_rows = 3, border_color = NA)
```

![](How_to_make_a_heatmap_using_BigQuery_files/figure-gfm/unnamed-chunk-12-1.png)<!-- -->

That’s it\! Please let us know if you have any questions at
<feedback@isb-cgc.org>.
