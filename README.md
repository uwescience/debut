# DEBUT

Machine Learning with Health Claims Data

Contents:

* README.md - this file
* LICENSE - some legal stuff
* etl.py - script for preparing raw MS data for analysis
* data.py - methods for tangling with the prepped data
* test_data.py - tests for data methods, execute with `py.test`
* auc.py - script for calculating auc of multiple ML methods
* 2016_08_15a_debut_etl_on_prod_cluster.ipynb - notebook to launch etl process on cluster
* 2016_07_18b_debut_table_data_calcs_and_checks.ipynb - script to do some analysis of the complex sequence data
* 2016_08_16a_debut_tics_refactored_additional_data_prep.ipynb - script to do some additional data prep
* 2016_08_16b_debut_model_sweep_on_prod_cluster.ipynb

Details: probably only runs on IHME cluster, possibly requires `source
activate debut_env`, which includes the dev version of sklearn.

To recreate this environment, use the command `conda env create -f environment.yml`


