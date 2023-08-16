-- Adjust p values using the Benjamini-Hochberg multipletests method, additional details in doi:10.1098/rsta.2009.0127
-- PARAMETERS: pvalue_table_name (name of the table with p values, STRING), pvalue_column_name (name of the column with p values, STRING), Nrows (number of rows of the table, i.e number of tests, INT64)
-- OUTPUT: table with a column with name p_adj containing the adjusted p values
-- VERSION: 1.0
-- EXAMPLE: https://github.com/isb-cgc/Community-Notebooks/blob/master/RegulomeExplorer/Correlations_Protein_and_Gene_expression_CPTAC.ipynb")
CREATE OR REPLACE PROCEDURE `__PROJECTID__.__DATASET__.BHmultipletests__VERSIONTAG__`(pvalue_table_name STRING, pvalue_column_name STRING, Nrows INT64)
BEGIN
   EXECUTE IMMEDIATE format("""
   WITH padjusted_data AS (
      WITH ranked_data AS (
         SELECT *, ( DENSE_RANK() OVER( ORDER BY %s) ) AS jrank
         FROM %s
      )
      SELECT *, 
         MIN( %d * %s / jrank )
         OVER (
            ORDER BY jrank DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
         ) AS p_adj 
      FROM ranked_data 
   )
   SELECT * EXCEPT (p_adj, jrank), IF( p_adj > 1.0 , 1.0, p_adj) AS p_adj
   FROM padjusted_data
   ORDER BY jrank""", pvalue_column_name, pvalue_table_name, Nrows, pvalue_column_name );
END;
