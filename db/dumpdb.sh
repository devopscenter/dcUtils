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
    echo -e "Usage: dumpdb.sh [--customerAppDir clientName/appName]"
    echo
    echo -e "--customerAppName is the name of the application that you want to"
    echo -e "run as the default app for the current session.  This is optional"
    echo -e "as by default the appName will be set when deployenv.sh is run"
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
BACKUP=backup.sql
CUSTOMER_APP_DIR=""
CUSTOMER_APP_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --backupFileName|--backupfilename ) shift
            BACKUP=$1
            ;;
        --customerAppDir|--customerappdir )    shift
            CUSTOMER_APP_DIR=$1
            ;;
        * ) usage
            exit 1
    esac
    shift
done

echo "Checking environment..."
if [[ -d ${CUSTOMER_APP_DIR} ]]; then
    CUSTOMER_APP_NAME=$(basename ${CUSTOMER_APP_DIR})
fi

if [[ -z ${CUSTOMER_APP_NAME} ]]; then
    . ./scripts/process-dc-env.sh
else
    . ./scripts/process-dc-env.sh --customerAppName ${CUSTOMER_APP_NAME}
fi

#-------------------------------------------------------------------------------
# Draw attention to the appName that is being used by this session!!
#-------------------------------------------------------------------------------
echo "NOTICE: Using appName: ${dcDEFAULT_APP_NAME}"

pg_dump -Fc -U postgres ${CUSTOMER_APP_NAME} --file=/datadump/${BACKUP}
