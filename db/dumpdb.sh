#!/bin/bash - 
#===============================================================================
#
#          FILE: dumpdb.sh
# 
#         USAGE: ./dumpdb.sh 
# 
#   DESCRIPTION: script to dump the given database to a given
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/21/2016 15:50:04
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: dumpdb.sh [--customerAppName appName] [--env theEnv]"
    echo
    echo -e "--customerAppDir is the name of the application that you want to"
    echo -e "      run as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--env theEnv is one of local, dev, staging, prod. This is optional"
    echo -e "      unless you have defined an enviornment other than local."
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
BACKUP=backup.sql
CUSTOMER_APP_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --backupFileName|--backupfilename ) shift
            BACKUP=$1
            ;;
        --customerAppName|--customerappname )    shift
            CUSTOMER_APP_NAME=$1
            ;;
        --env )    shift
            ENV=$1
            ;;
        * ) usage
            exit 1
    esac
    shift
done


#-------------------------------------------------------------------------------
# Check the environment first
#-------------------------------------------------------------------------------
echo "Checking environment..."
# turn on error on exit incase the process-dc-env.sh exists this script
# needs to exit
set -e  
if [[ -z ${CUSTOMER_APP_NAME} ]]; then
    if [[ -z ${ENV} ]]; then
        . ./scripts/process-dc-env.sh
    else
        . ./scripts/process-dc-env.sh --env ${ENV}
    fi
else
    if [[ -z ${ENV} ]]; then
        . ./scripts/process-dc-env.sh --customerAppName ${CUSTOMER_APP_NAME}
    else
        . ./scripts/process-dc-env.sh --customerAppName ${CUSTOMER_APP_NAME} --env ${ENV}
    fi
fi
set +e  # turn off error on exit
#-------------------------------------------------------------------------------
# end checking environment
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Draw attention to the appName that is being used by this session!!
#-------------------------------------------------------------------------------
echo "NOTICE: Using appName: ${dcDEFAULT_APP_NAME}"

pg_dump -Fc -U postgres ${CUSTOMER_APP_NAME} --file=/datadump/${BACKUP}
