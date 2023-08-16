CREATE OR REPLACE FUNCTION `__PROJECTID__.__DATASET__.complement_chisquare_cdf__VERSIONTAG__`(H FLOAT64, dof INT64) RETURNS FLOAT64 LANGUAGE js
OPTIONS (library=["gs://isb-cgc-bq-library/jstat/dist/jstat.min.js"], description="Returns the complement of the value of H in the cdf of the Chi Square distribution with dof degrees of freedom\nPARAMETERS: H (The statistics, FLOAT64) and dof (degrees of freedom, INT64)\nOUTPUT: complement of the the cdf of the Chi Square distribution, FLOAT64\nVERSION: 1.0\nEXAMPLE: This function is used by the udf isb-cgc-bq.functions.kruskal_wallis_udf") AS """
return(1.0 - jStat.chisquare.cdf(H, dof));
"""
