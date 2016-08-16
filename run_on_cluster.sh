# Use the bash shell to interpret this job script
#$ -S /bin/bash
#

# submit this job to nodes that have
# at least 80 GB of RAM free.
#$ -l mem_free=80.0G


## Put the hostname, current directory, and start date
## into variables, then write them to standard output.
GSITSHOST=`/bin/hostname`
GSITSPWD=`/bin/pwd`
GSITSDATE=`/bin/date`
echo "**** JOB STARTED ON $GSITSHOST AT $GSITSDATE"
echo "**** JOB RUNNING IN $GSITSPWD"
##

# show the last git commit message to stdout, for posterity
#git log -1

# keep everything in a repo, even if the commit logs suffer for it...
# bad idea... leads to multiple concurrent writes to .git dir from different
# cluster nodes
#git commit -a -m 'keep code in repo'


# make sure that boost library is in the path
#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/boost-current/lib

#source /usr/local/anaconda-current/bin/activate  /usr/local/anaconda-current
#source deactivate
source activate /snfs2/HOME/abie/anaconda/envs/testenv
echo calling python -u "$@"
python -u "$@"


## Put the current date into a variable and report it before we exit.
GSITSENDDATE=`/bin/date`
echo "**** JOB DONE, EXITING 0 AT $GSITSENDDATE"
##

## Exit with return code 0
exit 0

