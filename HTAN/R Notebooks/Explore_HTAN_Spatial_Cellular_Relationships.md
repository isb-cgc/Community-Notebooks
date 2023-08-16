---
title: "Explore Spatial Cellular and Molecular Relationships in HTAN using Google BigQuery"
author: "Vesteinn Þórsson, Institute for Systems Biology"
date: "Created June 1, 2023"
output:
  html_document:
    keep_md: true
    highlight: tango
    toc: yes
    toc_float:
      collapsed: yes
      smooth_scroll: no
  pdf_document:
    toc: yes
---


# 1. Introduction & Overview 

[HTAN](https://humantumoratlas.org/) is a National Cancer Institute (NCI)-funded Cancer Moonshot<sup>SM</sup> initiative to construct 3-dimensional atlases of the dynamic cellular, morphological, and molecular features of human cancers as they evolve from precancerous lesions to advanced disease. [Cell April 2020](https://www.sciencedirect.com/science/article/pii/S0092867420303469) 

Many HTAN Research Centers employ highly-multiplexed imaging to gain understanding of molecular processes and interactions at work in the tumor microenvironment.  The study [Multiplexed 3D atlas of state transitions and immune interaction in colorectal cancer](https://www.cell.com/cell/fulltext/S0092-8674(22)01571-9), Lin et al, Cell, Vol. 186, p363, 2023, uses multiplexed whole-slide imaging analysis to characterize intermixed and graded morphological and molecular features in human colorectal cancer samples, highlighting large-scale cancer-characteristic structural features.

This notebook shows one example of how these data can be accessed and analyzed using R programming software.

### 1.1 Goal

This example notebook illustrates how to make use of HTAN Google BigQuery tables which contain information on cellular locations and the estimated expression of key marker proteins, based on multiplexed imaging and cell segmentation. 

### 1.2 Inputs, Outputs, & Data 

The originating data can be found on the [HTAN Data Portal](https://data.humantumoratlas.org/), and the data tables are on the [Cancer Gateway in the Cloud](https://isb-cgc.appspot.com/).

### 1.3 Notes

The tables correspond to HTAN Data Version 3.

# 2. Environment & Library Setup

```r
suppressMessages(library(tidyverse))
suppressMessages(library(bigrquery))
suppressMessages(library(knitr))
suppressMessages(library(rdist))
suppressMessages(library(dbscan))
```

# 3. Google Authentication

Running the BigQuery cells in this notebook requires a Google Cloud Project. Instructions for creating a project can be found in the [Google Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console). The instance needs to be authorized to bill the project for queries. For more information on getting started in the cloud see [Quick Start Guide to ISB-CGC](https://nbviewer.org/github/isb-cgc/Community-Notebooks/blob/master/Notebooks/Quick_Start_Guide_to_ISB_CGC.ipynb) and alternative authentication methods can be found in the [Google Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects#console).


```r
billing <- 'my-projectr' # Insert your project ID in the ''
if (billing == 'my-projectr') {
  print('Please update the project number with your Google Cloud Project')
}
```

# 4. Explore Spatial Cellular and Molecular Relationsips

We will focus on imaging of tissue section 97 of sample CRC1 described in [the manuscript](https://www.cell.com/cell/fulltext/S0092-8674(22)01571-9) in detail (see e.g. Figure 1C). This tissue section is HTAN biospecimen `HTA13_1_101`. An excellent [interactive guide](https://www.cycif.org/data/lin-wang-coy-2021/osd-crc-case-1-ffpe-cycif-stack.html#s=0#w=0#g=0#m=-1#a=-100_-100#v=0.5_0.5_0.5#o=-100_-100_1_1#p=Q) to the to multiplex imaging data for this biospecimen is available.  The data for this and the other CRC1 tissue sections is found in Google BigQuery table `isb-cgc-bq.HTAN.imaging_level4_HMS_crc_mask_current`. This table contains estimated marker intensity following cell segmentation using three kinds of masks. Here we will use the mask "cellRingMask". The tables also contain data on location of geometry of segmented cells. Here we will use the cell locations in terms of the centroids `X_centroid` and `Y_centroid`.

### 4.1 Investigate cell locations 

We begin by querying for the coordinates of the centroids for the relevant tissue slice `HTA13_1_101`.

```r
sql <- "SELECT X_centroid, Y_centroid
FROM `isb-cgc-bq.HTAN.imaging_level4_HMS_crc_mask_current`
WHERE HTAN_Biospecimen_ID='HTA13_1_101'"
tb <- bq_project_query(billing, sql)
df <- bq_table_download(tb)

df <- df %>% rename(X="X_centroid",Y="Y_centroid")
```
This gives a table as an R data frame. Each row corresponds to once cell, and columns are the corresponding X and Y coordinates.

How many cells are there? 

```r
nrow(df)
```

```
## [1] 1287131
```
Now let's do a scatter plot of the centroids. (With over a million cells (!), this will take a few seconds.)

```r
ggplot(df, aes(X,Y)) +
 geom_point(size=0.01) +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-5-1.png" style="display: block; margin: auto;" />

X and Y coordinates enumerate pixels in the originating image. To see how pixels relate to physical units, enter `HTA13_1_101` in file search on the [HTAN Data Portal](https://data.humantumoratlas.org/explore?tab=file#), "View Details" for the Image you will see that one pixel is 0.65 micrometers (wide and high) and that the originating image is 26,139 pixels x 27,120 pixels.

Pixels and physical dimensions

```r
micron_per_pixel=0.65
X_total_pixels=26139
Y_total_pixels=27120
total_megapixels=X_total_pixels*Y_total_pixels/10^6
X_total_physical_dimension_mm=X_total_pixels*micron_per_pixel/10^3
Y_total_physical_dimension_mm=Y_total_pixels*micron_per_pixel/10^3
whole_slide_dimension_mm_squared=X_total_physical_dimension_mm * Y_total_physical_dimension_mm
```
The whole slide is image is `total_megapixels`=708.88968 Megapixels, and is `X_total_physical_dimension_mm`=16.99035 mm wide and `Y_total_physical_dimension_mm`=17.628 mm high.

OK, so now we see all the cell locations, but the overall appearance is not visibly consistent with manuscript images (Figure 1C, e.g).

This can be improved with simply flipping the image top to bottom:

```r
df <- df %>% mutate(Y_flipped=-Y+Y_total_pixels)
```

Replot

```r
ggplot(df, aes(X,Y_flipped)) +
 geom_point(size=0.01) + ylab("Y") +
  ggtitle("Cellular locations for biospecimen \n HTA13_1_101,CRC1 slice 97") +
  theme(plot.title = element_text(hjust = 0.5)) +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-8-1.png" style="display: block; margin: auto;" />
This looks better. Let's use these transformed Y coordinates from now on.

Where is the greatest density of cells?

```r
d <- ggplot(df,aes(X,Y_flipped))
d + geom_hex() + ylab("Y") +
  ggtitle("Cellular density for biospecimen \n HTA13_1_101,CRC1 slice 97") +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-9-1.png" style="display: block; margin: auto;" />



### 4.2 Which regions are tumor rich?

Keratin is used as marker for tumor cells in this study. We augment the table query to include the marker for keratin: `Keratin_570_cellRingMask`.


```r
sql <- "SELECT X_centroid, Y_centroid, Keratin_570_cellRingMask 
FROM `isb-cgc-bq.HTAN.imaging_level4_HMS_crc_mask_current`
WHERE HTAN_Biospecimen_ID='HTA13_1_101'"
tb <- bq_project_query(billing, sql)
df <- bq_table_download(tb)
df <- df %>% rename(Keratin=Keratin_570_cellRingMask,X=X_centroid,Y=Y_centroid)
df <- df %>% mutate(Y_flipped=-Y+min(Y)+max(Y)) %>% select(-Y) %>% rename(Y=Y_flipped)
```

What is the distribution of Keratin values over all cells?

```r
ggplot(df,aes(Keratin)) + geom_histogram(binwidth = 1000) +
  ggtitle("Distribution of Keratin in Cells for HTA13_1_101") +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-11-1.png" style="display: block; margin: auto;" />
Let's threshold the Keratin as being positive above the 3rd quartile.

```r
third.quartile <- summary(df$Keratin)[["3rd Qu."]]
df <- df %>% mutate(Keratin_status = c("Neg","Pos")[(Keratin > third.quartile)+1])
```
This has generated a new categorical variable, `Keratin_status`, designated as Low or High for every cell. A more sophisticated thresholding scheme is employed in the [manuscript](https://www.cell.com/cell/fulltext/S0092-8674(22)01571-9) and described in the corresponding methods section.

Where are the Keratin-high cells on the image?

```r
ggplot(df, aes(X,Y)) +
 geom_point(aes(color=Keratin_status),size=0.01,show.legend = FALSE) +   
  scale_color_manual(values=c("gray90","darkblue")) +
  ggtitle("Keratin-high regions in biospecimen \n HTA13_1_101,CRC1 slice 97") +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-13-1.png" style="display: block; margin: auto;" />

This is consistent with keratin-rich regions described in the manuscript (see manuscript Figure 1C).

### 4.3 Spatial neighbhorhoods
Spatial neighborhoods are used in the analysis of tissue imaging to yield insight into how different tissue regions compare in cellular content, cellular function, and cellular interactions. A neighborhood is usually defined in terms of specified geometric extent, e.g cells within a specified radial distance from the center of a reference cell, or in terms of a set of nearest neighbors of a designated number ("100 nearest neighbhors" e.g.).

As an example we find a neighborhood defined in terms of the 10 nearest neighbors for each cell. Since the pairwise distance calculation is resource intensive we limit the illustration to square subregion of 2500 pixels each side, or 1625 micrometers per side. 

We now grab the data for a spatial subregion using BigQuery (which will be a faster query than for the whole slide.)


```r
sql <- "SELECT X_centroid, Y_centroid, Keratin_570_cellRingMask 
FROM `isb-cgc-bq.HTAN.imaging_level4_HMS_crc_mask_current`where HTAN_Biospecimen_ID='HTA13_1_101'
AND X_centroid > 5000 AND X_centroid < 7500
AND Y_centroid > 20000 AND Y_centroid < 22500"
tb <- bq_project_query(billing, sql)
df_small <- bq_table_download(tb)
df_small <- df_small %>% rename(Keratin=Keratin_570_cellRingMask,X=X_centroid,Y=Y_centroid)
```


Counting rows, there are 26229 cells within this region. 

Keratin values in the region
<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-15-1.png" style="display: block; margin: auto;" />

We now identify the 10 nearest neighbors of each cell. We first calculate all pairwise distances among cells. We then find the (row) indices of the nearest neighbors of each cell.

```r
k <- 10
point_distances <- rdist::pdist(df_small[,c("X","Y")])
point_distances_dist_object <- as.dist(point_distances)
nearest_neighbors <- dbscan::kNN(point_distances_dist_object,k)
```


```r
kable(head(nearest_neighbors$id))
```



|    1|    2|    3|    4|    5|    6|    7|    8|    9|   10|
|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|
| 1521|   50| 1963| 1827| 1952| 1725| 1305|  433|  564|   13|
|   75|  533| 1907| 1091|  148| 1934|  361| 1334| 1822|  975|
| 1066| 1205| 1988|  641| 1203| 1586|  937|  326|  726| 1432|
| 1501| 1952|  799| 1765|   13| 1955| 1360| 1610| 1535|   50|
|  272|  517| 1036| 1282|  154| 1100|  165| 1997|  104|  409|
|  625|  753| 1880| 1794|  310| 1081| 1082| 1727|  921|  758|

The top row shows the (row) indices of the nearest neighbors to the first cell in the data frame, and so on.

### 4.4 Spatial correlations among cells
The manuscript describes how spatial correlation functions are calculated for a pair of cell markers. Examining this correlation as a function of distance yields estimates of the spatial extent of cancer-associated cellular structures. As an example we calculate keratin-keratin correlation for 10 nearest neighbhors (in the manuscript methods this corresponds to C_AB(r), with A=Keratin,B=Keratin, and r=10)

For each cell, look up the neighboring cells, calculate the mean Keratin value of the neighbors, and append that value to our data frame.

```r
collect <- numeric()
for (index in 1:nrow(df_small) ){
  meanz <- df_small[nearest_neighbors$id[index,],"Keratin"] %>% pluck("Keratin") %>% mean()
  collect <- c(collect,meanz)
}
df_small <- df_small %>% add_column(Keratin_10NN_mean=collect)
```

This plot shows the relation between the cell values and the mean value of neighbors
<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-19-1.png" style="display: block; margin: auto;" />

We can now calculate the correlation.

```r
df_small %>% summarize(cor(Keratin,Keratin_10NN_mean)) %>% pluck(1)
```

```
## [1] 0.8469181
```
The correlation is fairly high and in line with results shown in the manuscript (Figure 2B). To calculate the correlation length, one needs to look at this for different k, correpsonding to varying distance, as described in the manuscript (see Figure 2B).

### 4.5 Immune cells in the neighbhorhood of tumor cells

Let's use BigQuery to retrieve information on leukocytes using cellular CD45 values.


```r
sql <- "SELECT X_centroid, Y_centroid, Keratin_570_cellRingMask,CD45_PE_cellRingMask  
FROM `isb-cgc-bq.HTAN.imaging_level4_HMS_crc_mask_current`
WHERE HTAN_Biospecimen_ID='HTA13_1_101'
AND X_centroid > 5000 AND X_centroid < 7500
AND Y_centroid > 20000 AND Y_centroid < 22500"
tb <- bq_project_query(billing, sql)
df_small <- bq_table_download(tb)

df_small <- df_small %>% rename(Keratin=Keratin_570_cellRingMask,X=X_centroid,Y=Y_centroid,CD45=CD45_PE_cellRingMask)
```

What is the distribution of CD45 values over all cells?

```r
ggplot(df_small,aes(CD45)) + geom_histogram(binwidth = 200) +
  ggtitle("CD45 values in cells in HTA13_1_101 subregion") +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-22-1.png" style="display: block; margin: auto;" />


We'll use the (overly) simple definition of marker-positive cells as exceeding the 3rd quartile of the cell value distribution for each marker.

```r
third.quartile.keratin <- summary(df_small$Keratin)[["3rd Qu."]]
df_small <- df_small %>% mutate(Keratin_status = c("Neg","Pos")[(Keratin > third.quartile.keratin)+1])
third.quartile.cd45 <- summary(df_small$CD45)[["3rd Qu."]]
df_small <- df_small %>% mutate(CD45_status = c("Neg","Pos")[(CD45 > third.quartile.cd45)+1])
```


The distribution of CD45 positive and Keratin positive cells is as follows by this definition.

```r
kable(df_small %>% group_by(CD45_status,Keratin_status) %>% do(data.frame(Count=nrow(.))))
```



|CD45_status |Keratin_status | Count|
|:-----------|:--------------|-----:|
|Neg         |Neg            | 13654|
|Neg         |Pos            |  6018|
|Pos         |Neg            |  6018|
|Pos         |Pos            |   539|


Even with this crude thresholding scheme, we see that count for double positives (DPs) is well below the random expectation of `1/4*1/4*nrow(df_small)`=1639.3125 

Let's phenotype the cells based on this scheme

```r
phenotype <- function(x,y){
  case_when(
  x >= third.quartile.keratin & y >= third.quartile.cd45 ~ "DP",
  x >= third.quartile.keratin & y < third.quartile.cd45 ~ "Tumor",
  x < third.quartile.keratin & y >= third.quartile.cd45 ~ "CD45",
  x < third.quartile.keratin & y < third.quartile.cd45 ~ "Other"
  )
}
df_small <- df_small %>% mutate(Phenotype=phenotype(Keratin,CD45))
```
 
Let's see how the cell phentoypes are distributed in the region.

```r
ggplot(df_small, aes(X,Y)) +
 geom_point(aes(color=Phenotype),size=0.3) +
  scale_color_manual(values=c("blue","magenta","gray90","yellow")) +
  ggtitle("Spatial distribution of tumor and immune cells \n in HTA13_1_101 region") +
  theme_classic()
```

<img src="Explore_HTAN_Spatial_Cellular_Relationships_files/figure-html/unnamed-chunk-26-1.png" style="display: block; margin: auto;" />

We can find tumor cells that have a predominance of immune cells in their neighborhood.

Suggested exercise: Use the nearest neighbor matrix above to find which tumor cells have the greatest number of immune cells nearby.  Display those on a plot like the one above. 

# 5. Citations and Links

[Cell April 2020](https://www.sciencedirect.com/science/article/pii/S0092867420303469)

[Multiplexed 3D atlas of state transitions and immune interaction in colorectal cancer](https://www.cell.com/cell/fulltext/S0092-8674(22)01571-9)
