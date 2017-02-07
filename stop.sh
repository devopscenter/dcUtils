#!/bin/bash -
#===============================================================================
#
#          FILE: stop.sh
#
#         USAGE: ./stop.sh
#
#   DESCRIPTION:  Stops the containers that were started with docker-compose
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/17/2016 16:27:42
#      REVISION:  ---
#===============================================================================

#set -o nounset                              # Treat unset variables as an error
#set -o errexit      # exit immediately if command exits with a non-zero status
#set -x              # essentially debug mode

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: stop.sh [--appName appName] [--env theEnv]"
    echo
    echo -e "--appName is the name of the application that you want to"
    echo -e "      run as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--env theEnv is one of local, dev, staging, prod. This is optional"
    echo -e "      unless you have defined an environment other than local."
    echo -e "--debug will start the web-debug container rather than the web one"
    echo
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' || $# -eq 0 ]]; then
    usage
    exit 1
fi

NEW=${@}
dcUTILS=${dcUTILS:-"."}

envToSource=$(${dcUTILS}/scripts/process_dc_env.py ${NEW})

if [[ $? -ne 0 ]]; then
    echo $envToSource
else
    eval $envToSource
fi

DEBUG=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug|-d )
            DEBUG=1
            ;;
    esac
    shift
done

#-------------------------------------------------------------------------------
# Draw attention to the appName that is being used by this session!!
#-------------------------------------------------------------------------------
echo "NOTICE: Using appName: ${dcDEFAULT_APP_NAME}"

#-------------------------------------------------------------------------------
# We have all the information for this so lets run the docker-compose down with
# the appropriate appName
#-------------------------------------------------------------------------------

# TODO - determine if we want to run in the customers directory
cd $dcUTILS

if [[ ${DEBUG} -eq 1 ]]; then
    DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose-debug.yml"
else
    DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose.yml"
fi
#echo ${DOCKER_COMPOSE_FILE}

#-------------------------------------------------------------------------------
# check to see if the compose file exists
#-------------------------------------------------------------------------------
if [[ ! -f ${DOCKER_COMPOSE_FILE} ]]; then
    echo -e "ERROR: No compose file for the appName: ${dcDEFAULT_APP_NAME}"
    echo -e "so nothing can be started.  You may need to create one manually."
    exit 1
fi


#-------------------------------------------------------------------------------
# get the number of applications running by the name of the specialized network
# bridge created.
#-------------------------------------------------------------------------------
NUM_NETWORKS=$(docker network ls | grep -c "_dcnet" )
export NET_NUMBER=$((20+$NUM_NETWORKS-1))

CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} stop"
#echo  ${CMDTORUN}
${CMDTORUN}
