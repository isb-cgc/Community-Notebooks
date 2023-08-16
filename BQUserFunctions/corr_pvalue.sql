CREATE OR REPLACE FUNCTION `__PROJECTID__.__DATASET__.corr_pvalue__VERSIONTAG__`(r FLOAT64, n INT64) RETURNS FLOAT64 LANGUAGE js
OPTIONS (library=["gs://isb-cgc-bq-library/jstat/dist/jstat.min.js"], description="Returns the p value of a correlation coefficient\nPARAMETERS: r (Correlation coefficient, FLOAT64) and n (number of samples, INT64)\nOUTPUT: p value, FLOAT64\nVERSION: 1.0") AS R"""
var abs_r = Math.abs(r)
if ( abs_r < 1.0 ) {
   var t =  abs_r * Math.sqrt( (n-2) / (1.0 - (r*r)) )
   return jStat.ttest(t,n-2,2); //jStat.ttest( tscore, n, sides)
} 
else if (abs_r == 1.0  ) {
   return 0.0
} else {  
   return NaN 
}
""";
