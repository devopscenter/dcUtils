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
    echo -e "Usage: start.sh [--appName appName] [--env theEnv] [-d]"
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
if [[ $1 == '-h' ]]; then
    usage
    exit 1
fi

NEW=${@}
dcUTILS="."

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
# first we need to see if postgresql is running locally, and if so stop and
# let the user know that we can't run the db containers and the local postgresql
# at the same time.  The ports will collide and the db container will not start.
#-------------------------------------------------------------------------------
postgres=$(ps -ef|grep postgres | grep -v grep)
set -e
if [ -n "$postgres" ]; then
    echo "*** courtesy warning ***"
    echo "postgres running on os/x, please exit and try starting again."
    return 1 2> /dev/null || exit 1
fi
set +e

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

if [[ ${DEBUG} -eq 1 ]]; then
    DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose-debug.yml"
else
    DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose.yml"
fi
# echo ${DOCKER_COMPOSE_FILE}

#-------------------------------------------------------------------------------
# check to see if the compose file exists
#-------------------------------------------------------------------------------
if [[ ! -f ${DOCKER_COMPOSE_FILE} ]]; then
    echo -e "ERROR: No compose file for the appName: ${dcDEFAULT_APP_NAME}"
    echo -e "so nothing can be started.  You may need to create one manually."
    exit 1
fi

NUM_NETWORKS=$(docker network ls | grep -sc "_dcnet")
export NET_NUMBER=$((20+$NUM_NETWORKS))
#echo "Network subnet used: 172.${NET_NUMBER}.0"


CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} up -d"
echo  ${CMDTORUN}
${CMDTORUN}

exit

#-------------------------------------------------------------------------------
#  TODO: figure out a cross platform way to open terminals for the containers
#        In the meantime have the user use the script ${dcUtils}/enter-container.py
#        in different terminals.   Or if they want to see the debug logs for any
#        of the containers use the show-docker-logs.py and select a running container
#-------------------------------------------------------------------------------
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
