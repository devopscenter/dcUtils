#!/bin/bash - 
#===============================================================================
#
#          FILE: run-restoredb.sh
# 
#         USAGE: ./run-restoredb.sh 
# 
#   DESCRIPTION: This script is run locally and will execute the restoredb.sh 
#                withing the web container.  This will allow the user to stay
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
set -o errexit
# be verbose
set -o verbose

# set debug mode 
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
    BACKUP=`basename $2`
fi

docker exec -it web-1 /bin/bash -c "export TERM=xterm; cd /utils/db; ./restoredb.sh ${DATABASE} ${BACKUP}"


