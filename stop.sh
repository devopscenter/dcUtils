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
    echo -e "Usage: stop.sh [--customerAppName appName] [--env theEnv]"
    echo
    echo -e "--customerAppName is the name of the application that you want to"
    echo -e "      run as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--env theEnv is one of local, dev, staging, prod. This is optional"
    echo -e "      unless you have defined an enviornment other than local."
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
CUSTOMER_APP_NAME=""
ENV=""
while [[ $# -gt 0 ]]; do
    case $1 in
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

