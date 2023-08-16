# User defined functions
BigQuery now supports [User Defined Functions (UDFs)](https://cloud.google.com/bigquery/docs/reference/standard-sql/user-defined-functions) in SQL and JavaScript that can extend BigQuery on more specialized computations. To facilitate the analysis of cancer data, ISB-CGC offers a set of UDFs that implement commonly used statistical tests and methods in cancer research and bioinformatics, the source code of the ISB-CGC UDFs are hosted in this repo; and the following sections provide detailed descriptions and examples of how to use these functions in the [BigQuery console](https://console.cloud.google.com/bigquery).  

## kruskal_wallis 
Computes the test statistics (H) and the p value of the Kruskal Wallis test (https://en.wikipedia.org/wiki/Kruskal-Wallis_one-way_analysis_of_variance).

- **Input:** Data in form of an array of structures <factor STRING, val FLOAT64> where factors is the categorical or nominal data point and val is the numerical value (type array: struct <factor STRING, val FLOAT64>).
- **Output:** A structure of the type struct<H FLOAT64, p FLOAT64, DOF FLOAT64> where H is the statistic, p is the p value, and DOF is the degrees of freedom

Example
```
WITH mydata AS (
   SELECT [
    ('a',1.0), ('b',2.0), ('c',2.3), ('a',1.4),
    ('b',2.2), ('c',5.5), ('a',1.0), ('b',2.3),
    ('c',2.3), ('a',1.1), ('b',7.2), ('c',2.8)
   ] as data
) 
SELECT `isb-cgc-bq.functions.kruskal_wallis_current`(data) 
       AS results
FROM mydata
```

Output:
| results.H  | results.p  | results.DoF  |
|---|---|---|
| 3.423076923076927  | 0.1805877514841956  |  2 | 

## kmeans
Estimates cluster assigments using the K-means algorithm (https://en.wikipedia.org/wiki/K-means_clustering), implemented in JavaScript.

- **Input:** DataPoints: data points in the form of an array of structures where each element is an array that represents a data point
  (type ARRAY<STRUCT<point ARRAY<FLOAT64>>>), iterations: the number of iterations (type INT64), and k: the number of clusters (type INT64).
- **Output:** An array of labels (integer numbers) representing the cluster assigments for each data point.

Example
```
WITH mydata AS (
 SELECT
   [
    STRUCT( [  1.0, 0] ),
    STRUCT( [  0.0, 1] ),
    STRUCT( [  0.0, 0] ),
    STRUCT( [-10.0, 10] ),
    STRUCT( [ -9.0, 11] ),
    STRUCT( [ 10.0, 10] ),
    STRUCT( [ 11.0, 12] )
   ] AS PointSet)
SELECT `isb-cgc-bq.functions.kmeans_current`(PointSet, 100, 3) as labels
FROM mydata
```

Output:
| label |
|---|
| [2,2,2,1,1,0,0] | 

## p_fisherexact
Computes the p value of the Fisher exact test (https://en.wikipedia.org/wiki/Fisher%27s_exact_test), implemented in JavaScript.

- **Input:** a,b,c,d : values of 2x2 contingency table ([ [ a, b ] ;[ c , d ] ] (type FLOAT64).
- **Output:** The p value of the test (type: FLOAT64)

Example
```
WITH mydata as (
SELECT
    90.0        as a,
    27.0        as b,
    17.0        as c,
    50.0  as d
)
SELECT
    `isb-cgc-bq.functions.p_fisherexact_current`(a,b,c,d) as pvalue
FROM
   mydata
```

Output:
| pvalue |
|---|
| 8.046828829103659E-12 | 

## mannwhitneyu
Computes the U statistics and the p value of the Mann–Whitney U test (https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test). This test is also called the Mann–Whitney–Wilcoxon (MWW), Wilcoxon rank-sum test, or Wilcoxon–Mann–Whitney test

- **Input:** x,y :arrays of samples, both should be one-dimensional (type: ARRAY<FLOAT64> ), alt: defines the alternative hypothesis, the following options are available: 'two-sided', 'less', and 'greater'.
- **Output:** structure of the type struct<U FLOAT64, p FLOAT64> where U is the statistic and p is the p value of the test.

Example
```
WITH mydata AS (
  SELECT
    [2, 4, 6, 2, 3, 7, 5, 1.] AS x,
    [8, 10, 11, 14, 20, 18, 19, 9. ] AS y
)
SELECT `isb-cgc-bq.functions.mannwhitneyu_current`(y, x, 'two-sided') AS test
FROM mydata
```

Output:
| test.U | test.p |
|---|---|
| 0.0 | 9.391056991171487E-4 | 

## significance_level_ttest2
Determines if the p-value of a two-sided T test is smaller than  0.05, 0.01, 0.005, or 0.001 (common significance levels). It is used to filter out correlations that are not statistically significant (p-value > significance_level)

- **Input:** df: degrees of freedom (type INT64), and tscore: the t statistics (type FLOAT64).
- **Output:** One of the 6 possible upper bounds of the p-value : 1.0, 0.05,0.01,0.005,0.001,0.0.

Example:
```
SELECT `isb-cgc-bq.functions.significance_level_ttest2_current`(30, 3.65) as slevel
```
Output:
| slevel |
|---|
| 0.001 |

## complement_chisquare_cdf
Returns the complement of the value of H in the cdf of the Chi Square distribution with dof degrees of freedom.
This function is called by the kruskal_wallis function.

- **Input:** H: the statistics (type FLOAT64) and dof: degrees of freedom (type INT64).
- **Output:** complement of the the cdf of the Chi Square distribution.

Example:
```
SELECT `isb-cgc-bq.functions.complement_chisquare_cdf_current`(3.423076923076927 ,2 ) AS p
```
Output:
| p |
|---|
| 0.1805877514841956 |

## jstat_normal_cdf
Returns the value of x in the cdf of the Normal distribution with parameters mean and std. 

- **Input:** x: the value (type FLOAT64), mean (type FLOAT64), and std: standard deviation (type FLOAT64).
- **Output:** the cdf of the normal distribution

Example:
```
SELECT `isb-cgc-bq.functions.jstat_normal_cdf_current`(2.0, 0.0, 1.0 ) AS cdf
```
Output:
| cdf |
|---|
| 0.9772498680518208 |
