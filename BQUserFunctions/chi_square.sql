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
CREATE OR REPLACE FUNCTION `__PROJECTID__.__DATASET__.chi_square__VERSIONTAG__`(x ARRAY<STRING>, y ARRAY<STRING>)
OPTIONS (description="Computes the statistics and the p value of the Chi squared test(https://en.wikipedia.org/wiki/Chi-squared_test) from the input data\nPARAMETERS: x,y (arrays of labels from the first and secong group, respectively, both should be one-dimensional, type: ARRAY<STRING> ) \nOUTPUT: A structure of the type struct<Chi FLOAT64, DOF FLOAT64, p-value FLOAT64> where Chi2 is the Chi squared statistic, DOF is the degrees of freedom, and p-value is the pe value\nVERSION: 1.0") AS (
(
  WITH categorical AS (
    SELECT independent_var , y[OFFSET(id)] as dependent_var
    FROM UNNEST( x )  as independent_var  WITH OFFSET id  
  ),
  contingency_table AS (
    SELECT DISTINCT
      independent_var,
      dependent_var,
      COUNT(*) OVER(PARTITION BY independent_var, dependent_var) as count,
      COUNT(*) OVER(PARTITION BY independent_var) independent_total,
      COUNT(*) OVER(PARTITION BY dependent_var) dependent_total,
      COUNT(*) OVER() as total
      FROM categorical AS t0
  ),
  expected_table AS (
    SELECT
      independent_var,
      dependent_var,
      independent_total * dependent_total / total as count
    FROM contingency_table
  ),
  output AS (
    SELECT
      SUM(POW(contingency_table.count - expected_table.count, 2) / expected_table.count) as x,
      SUM(POW(ABS(contingency_table.count - expected_table.count)- 0.5, 2) / expected_table.count) as x_corr,
      (COUNT(DISTINCT contingency_table.independent_var) - 1)
        * (COUNT(DISTINCT contingency_table.dependent_var) - 1) AS dof
    FROM contingency_table
    INNER JOIN expected_table
    ON expected_table.independent_var = contingency_table.independent_var
      AND expected_table.dependent_var = contingency_table.dependent_var
  )
  SELECT 
    IF (  dof = 1 , 
      STRUCT (x_corr as x, dof, bqutil.fn.pvalue(x_corr, dof) AS p) ,
      STRUCT (x, dof, bqutil.fn.pvalue(x, dof) AS p) )
  FROM output
)
);
