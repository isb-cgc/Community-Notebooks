# /*
# * Copyright 2019 Google LLC
# *
# * Licensed under the Apache License, Version 2.0 (the "License");
# * you may not use this file except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *     http://www.apache.org/licenses/LICENSE-2.0
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# */
CREATE OR REPLACE FUNCTION `__PROJECTID__.__DATASET__.kruskal_wallis__VERSIONTAG__`(data ARRAY<STRUCT<factor STRING, val FLOAT64>>)
OPTIONS (description="Computes the test statistics (H) and the p value of the Kruskal Wallis test(https://en.wikipedia.org/wiki/Kruskal-Wallis_one-way_analysis_of_variance) from the input data\nPARAMETERS: Data in from of an array of structures <factor STRING, val FLOAT64> where factors is the categorical or nominal data point and val is the numerical value(type array: struct <factor STRING, val FLOAT64>)\nOUTPUT: A structure of the type struct<H FLOAT64, p-value FLOAT64, DOF FLOAT64> where H is the statistic, p-value is the pe value, and DOF is the degrees of freedom\nVERSION: 1.0\nNOTE: This function was obtained from https://github.com/jrossthomson/bigquery-utils/tree/statslib/udfs/statslib\nEXAMPLE:https://github.com/isb-cgc/Community-Notebooks/blob/master/ACM-BCB-2020_Poster_GeneAndProteinExpression_vs_ClinicalFeatures.ipynb") AS (
(
    with H_raw as(
        with sums as 
        (
            with rank_data as 
            (
                #SELECT  r, d.factor as f, d.val as v from UNNEST(data) as d with offset as r
                select d.factor as f, d.val as v, rank() over(order by d.val) as r
                from unnest(data) as d 
            ) #rank_data
            select     
                SUM(r) * (SUM(r) / COUNT(*) ) AS sumranks, COUNT(*) AS n
            from rank_data
            GROUP BY f
        ) # sums
        SELECT 12.00 /(SUM(n) *(SUM(n) + 1)) * SUM(sumranks) -(3.00 *(SUM(n) + 1)) as H, 
                      count(n) -1 as DoF
        FROM sums
    ) # H_raw
    SELECT struct(H as H, `__PROJECTID__.__DATASET__.complement_chisquare_cdf_v1_0`(H, DoF) as p, DoF as DoF) from H_raw
)
)
