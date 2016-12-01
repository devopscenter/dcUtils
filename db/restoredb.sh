#!/usr/bin/env bash
#===============================================================================
#
#          FILE: restoredb.sh
# 
#         USAGE: ./restoredb.sh 
# 
#   DESCRIPTION: Take a database backup file and use pgrestore to restore/create a 
#                database
# 
#       OPTIONS: DATABASE = $1  the database name that you want to recreate
#                BACKUP = $2    the name of the backup file
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 10/04/2016 17:45:30
#      REVISION:  ---
#===============================================================================

#-------------------------------------------------------------------------------
#set the options that you would have set as bash arguments
#-------------------------------------------------------------------------------
# exit immediately if command exits with a non-zero status
set -o errexit
# be verbose
set -o verbose
set -x 

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  provide the usage statement for improper use of this script
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
function usage 
{
    echo 
    echo -e "$0: DATABASE_NAME BACKUP_FILE_NAME"
    echo 
    exit 1
}


#-------------------------------------------------------------------------------
# get the arguments from the command line
#-------------------------------------------------------------------------------
if [[ $# != 2 ]]; then
    usage
else
    DATABASE=$1
    BACKUP=$2
fi


#-------------------------------------------------------------------------------
# check for the existence of the backup file
#-------------------------------------------------------------------------------
flag=0
if [[ -f "${BACKUP}" ]]; then
    flag=1
elif [[ -f "/dataload/${BACKUP}" ]]; then
    flag=1
fi

if [[ flag -eq 0 ]]; then
    echo -e "File does not exist: ${BACKUP}"
    exit 2
fi


#-------------------------------------------------------------------------------
# Looks like we are good to go.  So, first drop the database and create it.
#-------------------------------------------------------------------------------
#dropdb ${DATABASE}_backup --if-exists -U postgres
#psql -U postgres postgres -c "alter database $DATABASE rename to ${DATABASE}_backup" || echo 0
dropdb ${DATABASE} --if-exists -U postgres
psql -U postgres postgres -c "create database $DATABASE"

psql -U postgres postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() and datname = '${DATABASE}'"

#-------------------------------------------------------------------------------
# and finally do the restore of the backup 
#-------------------------------------------------------------------------------
if [[ -f /dataload/${BACKUP} ]]; then
    pg_restore --exit-on-error -j 2 -e -U postgres -Fc --dbname=${DATABASE} /dataload/${BACKUP}
else
    pg_restore --exit-on-error -j 2 -e -U postgres -Fc --dbname=${DATABASE} ${BACKUP}
fi

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
