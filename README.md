# DEBUT

Machine Learning with Health Claims Data

Contents:

* etl.py - script for preparing raw MS data for analysis


Details: probably only runs on IHME cluster, possibly requires `source
activate testenv`, which includes the dev version of sklearn.

To run ETL process on cluster, use the following loop:
```
# run full etl on cluster
import subprocess

for y in range(2007, 2015):
    log = '/ihme/scratch/users/abie/projects/2016/TICS/tics_etl_%d.txt'%y
    name_str = 'tics_etl_%d'%y
    call_str = 'qsub -pe multi_slot 64 -cwd -o %s -e %s ' % (log, log) \
                + '-N %s ' % name_str \
                + 'run_on_cluster.sh etl.py %d' % y
    print call_str
    subprocess.call(call_str, shell=True)
```

For example, see notebook `2016_02_16a_TICS_ETL_w_additional_year.ipynb`.

