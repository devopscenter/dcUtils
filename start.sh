#!/bin/bash -
#===============================================================================
#
#          FILE: start.sh
#
#         USAGE: ./start.sh
#
#   DESCRIPTION: This script will start the docker containers for the default
#                application name (found in the personal.env or set when
#                deployenv.sh is run)
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/17/2016 11:07:36
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
set -o errexit      # exit immediately if command exits with a non-zero status
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
    echo -e "Usage: start.sh [--customerAppName appName] [--env theEnv] [-d]"
    echo
    echo -e "--customerAppDir is the name of the application that you want to"
    echo -e "run as the default app for the current session.  This is optional"
    echo -e "as by default the appName will be set when deployenv.sh is run"
    echo -e "--env theEnv is one of local, dev, staging, prod"
    echo -e "--debug will start the web-debug container rather than the web one"
    echo
    exit 1
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
CUSTOMER_APP_NAME=""
ENV=""
DEBUG=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --customerAppName|--customerappname )    shift
            CUSTOMER_APP_NAME=$1
            ;;
        --env )    shift
            ENV=$1
            ;;
        --debug|-d )
            DEBUG=1
            ;;
        * ) usage
            exit 1
    esac
    shift
done

echo "Checking environment..."
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

#-------------------------------------------------------------------------------
# Draw attention to the appName that is being used by this session!!
#-------------------------------------------------------------------------------
echo "NOTICE: Using appName: ${dcDEFAULT_APP_NAME}"

#-------------------------------------------------------------------------------
# We have all the information for this so lets run the docker-compose up with
# the appropriate appName
#-------------------------------------------------------------------------------

# TODO - determine if we want to run in the customers directory
cd $dcUTILS

DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose.yml"
# echo ${DOCKER_COMPOSE_FILE}

#-------------------------------------------------------------------------------
# check to see if the compose file exists
#-------------------------------------------------------------------------------
if [[ ! -f ${DOCKER_COMPOSE_FILE} ]]; then
    echo -e "ERROR: No compose file for the appName: ${dcDEFAULT_APP_NAME}"
    echo -e "so nothing can be started.  You may need to create one manually."
    exit 1
fi

CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} up -d"
#echo  ${CMDTORUN}
${CMDTORUN}

exit

new_tab() {
  sleep 1
  TAB_NAME=$1
  COMMAND=$2
  COMMANDINSIDE=$3
  osascript \
    -e "tell application \"Terminal\" to activate" > /dev/null
  sleep 1
  osascript \
    -e "tell application \"System Events\" to tell process \"Terminal\" to keystroke \"t\" using command down" \
    -e "tell application \"Terminal\" to do script \"$COMMAND\" in selected tab of the front window" > /dev/null
  sleep 2
  osascript \
    -e "tell application \"Terminal\" to do script \"printf '\\\e]1;$TAB_NAME\\\a'; $COMMANDINSIDE\" in selected tab of the front window" > /dev/null
}

new_tab "Web Container" "cd $dcUTILS && docker exec -it web-1 /bin/bash" " "
new_tab "Worker Container" "cd $dcUTILS && docker exec -it worker-1 /bin/bash" " "
