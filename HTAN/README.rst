=====================================================
HTAN BigQuery Notebooks
=====================================================
`HTAN <https://humantumoratlas.org>`_ is a National Cancer Institute (NCI)-funded Cancer Moonshot<sup>SM</sup> initiative to
construct 3-dimensional atlases of the dynamic cellular, morphological, and molecular features of human cancers as they
evolve from precancerous lesions to advanced disease
`(Cell, April 2020) <https://www.sciencedirect.com/science/article/pii/S0092867420303469>`_.

In order to access the cloud-based data used in these notebooks, please see:
 `Getting started with the ISB-CGC <https://isb-cancer-genomics-cloud.readthedocs.io/en/latest/sections/HowToGetStartedonISB-CGC.html>`_


Clinical data, sample biospecimen data and assay files in HTAN have a rich set of annotations supplied by HTAN data
contributors.  These annotations are made according to the  `HTAN Data model <https://data.humantumoratlas.org/standards>`_ ,
a set of standards defined by the HTAN consortium. The supplied values of these attributes have been collected into
comprehensive data tables in the cloud, accessed using
`Google BigQuery standard SQL <https://cloud.google.com/bigquery/docs/query-overview>`_.

This folder contains example notebooks that illustrate how to query and process both file metadata and molecular data
that are available in Google BigQuery tables.

Notebooks are available in both the R programming language (R markdown) and in Python (Jupyter).
There is a also a folder with templates, if you would like to create and share your own notebooks.

Contents:

**R Notebooks/Explore_HTAN_Clinical_Biospecimen_Assay_Metadata.Rmd** - illustrates how to make use of HTAN Google
BigQuery metadata tables to tabulate and plot available HTAN clinical, biospecimen, and assay metadata in R

**R Notebooks/Explore_HTAN_Spatial_Cellular_Relationships.Rmd** - illustrates how to make use of HTAN Google 
BigQuery cell spatial tables, which contain information on cellular locations and the estimated expression of 
key marker proteins, based on multiplexed imaging and cell segmentation.

**Python Notebooks/Analyzing_HTAN_Data_in_SB_Data_Studio.ipynb** - illustrates how open-access HTAN data can be integrated 
with controlled-access data in CDS Data Studio. Utilizes the HTAN ID provenance BigQuery table in ISB-CGC to pull in 
relevant files

**Python Notebooks/HTAN_ID_Provenance_In_BQ.ipynb** - introduces the HTAN Google
BigQuery ID provenance table and provides example use cases for the table in Python

**Python Notebooks/Explore_HTAN_Clinical_Biospecimen_Assay_Metadata.ipynb** - illustrates how to make use of HTAN Google
BigQuery metadata tables to tabulate and plot available HTAN clinical, biospecimen, and assay metadata in Python

**Python Notebooks/Analyzing_HTAN_MIBI_Imaging_Data.ipynb** - demonstrates how higher level HTAN imaging data can be pulled 
from Synapse and Google BigQuery for analysis or visualization.

**Python Notebooks/Identifying_HTAN_Data_Files_by_Organ_in_ISB-CGC.ipynb** - demonstrates how users can identify and access 
assay data for a particular organ or cancer type using Google BigQuery metadata tables.

**Python Notebooks/Investigating_Single_Cell_HTAN_Data.ipynb** - illustrates how to query HTAN single-cell RNA
sequencing data for cell content and gene expression

**Python Notebooks/Building_AnnData_with_Subset_of_Cells_from_BQ.ipynb** - illustrates how to query HTAN single-cell RNA
sequencing data for specific cell types and construct an Scanpy Anndata object from the result

**HTAN_Notebook_Templates** - these templates serve as a guide for notebook construction. 

