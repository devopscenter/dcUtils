#!/bin/bash - 
#===============================================================================
#
#          FILE: run-restoredb.sh
# 
#         USAGE: ./run-restoredb.sh 
# 
#   DESCRIPTION: This script is run locally and will execute the restoredb.sh 
#                within the web container.  This will allow the user to stay
#                local and execute the restoredb.sh without having to log into
#                the container.  Someone with knowledge of Docker containers 
#                wouldn't have to run this script as they are probably comfortable
#                jumping onto the container and executing the script within the
#                container.  For others, this can do that same function for them
#                but doesn't required a lot of up front knowledge about containers.
# 
#       OPTIONS: DATABASE_NAME BACKUP_FILE_NAME
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/11/2016 14:35:31
#      REVISION:  ---
#===============================================================================


#-------------------------------------------------------------------------------
#set the options that you would have set as bash arguments
#-------------------------------------------------------------------------------
# exit immediately if command exits with a non-zero status
#set -o errexit
# be verbose
#set -o verbose

# set debug mode 
#set -x

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  provide the usage statement for improper use of this script
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: run-restoredb.sh [--customerAppName appName] [--env theEnv]"
    echo -e "           --database DATABASE_NAME --backup BACKUP_FILE_NAME"h
    echo
    echo -e "This script is run locally and will execute the restoredb.sh"
    echo -e "within the web container.  This will allow the user to stay"
    echo -e "local and execute the restoredb.sh without having to log into"
    echo -e "the container.  Someone with knowledge of Docker containers"
    echo -e "wouldn't have to run this script as they are probably comfortable"
    echo -e "jumping onto the container and executing the script within the"
    echo -e "container.  For others, this can do that same function for them"
    echo -e "but doesn't required a lot of up front knowledge about containers."
    echo 
    echo -e "--customerAppDir is the name of the application that you want to"
    echo -e "      run as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--env theEnv is one of local, dev, staging, prod. This is optional"
    echo -e "      unless you have defined an environment other than local."
    echo -e "--database (or -d) is the name of the database that needs to be "
    echo -e "      restored."
    echo -e "--backup (or -b) is the name of the backup file that will be used"
    echo -e "      to be restored."
    echo 
    echo -e "the customerAppName and the env arguments are required as they "
    echo -e "provide the basis for the name of the web container that will be"
    echo -e "used to run the restoredb.sh in"
    echo
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
NEW=${@}
dcUTILS=".."

envToSource=$(${dcUTILS}/scripts/process_dc_env.py ${NEW})

if [[ $? -ne 0 ]]; then
    echo $envToSource
else
    eval $envToSource
fi

DEBUG=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --database|-d ) shift
            DATABASE=$1
            ;;
        --backup|-b ) shift
            BACKUP=$(basename $1)
            ;;
    esac
    shift
done


CONTAINER_NAME="${dcDEFAULT_APP_NAME}_${CUSTOMER_APP_ENV}_web-1"

docker exec -it ${CONTAINER_NAME} /bin/bash -c "export TERM=xterm; cd /utils/db; ./restoredb.sh ${DATABASE} ${BACKUP}"


