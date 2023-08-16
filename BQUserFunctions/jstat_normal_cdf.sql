CREATE OR REPLACE FUNCTION `__PROJECTID__.__DATASET__.jstat_normal_cdf__VERSIONTAG__`(x FLOAT64, mean FLOAT64, std FLOAT64)
RETURNS FLOAT64 
LANGUAGE js
OPTIONS (library=["gs://isb-cgc-bq-library/jstat/dist/jstat.min.js"], description="Returns the value of x in the cdf of the Normal distribution with parameters mean and std\nPARAMETERS: x (the value, FLOAT64), mean ( mean, FLOAT64), and std (standard deviation, FLOAT64)\nOUTPUT: the cdf of the normal distribution\nVERSION: 1.0\nEXAMPLE: This function is used by the udf isb-cgc-bq.functions.mannwhitneyu_v1_0") 
AS """
//return jStat.ztest(z, sides); //jStat.ztest(z, sides)
return jStat.normal.cdf( x, mean, std )
""";
