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
    echo -e "      unless you have defined an environment other than local."
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------

NEW=${@}
dcUTILS=".."

envToSource="$(${dcUTILS}/scripts/process_dc_env.py ${NEW})"

if [[ $? -ne 0 ]]; then
    echo $envToSource
    exit 1
else
    eval "$envToSource"
fi

BACKUP=backup.sql

while [[ $# -gt 0 ]]; do
    case $1 in
        --backupFileName|--backupfilename ) shift
            BACKUP=$1
            ;;
    esac
    shift
done

#-------------------------------------------------------------------------------
# Draw attention to the appName that is being used by this session!!
#-------------------------------------------------------------------------------
echo "NOTICE: Using appName: ${dcDEFAULT_APP_NAME}"

pg_dump -Fc -U postgres ${CUSTOMER_APP_NAME} --file=/datadump/${BACKUP}
