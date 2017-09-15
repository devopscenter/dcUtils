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
    echo -e "This script will stop the docker containers found running that are"
    echo -e "specific to the application and no others.  The containers will be "
    echo -e "stopped so the state will not be lost when they are started again"
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

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  setupNetwork
#   DESCRIPTION:  ensures the user defined network for this container is set up
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
setupNetwork()
{
    # get the subnet definition from the customers utils/config/local directory
    DOCKER_SUBNET_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-subnet.conf"


    if [[ -f ${DOCKER_SUBNET_FILE} ]]; then
        # need to get the docker-subnet.conf from the app-utils/config/local
        aLine=$(grep DOCKER_SUBNET_TO_USE ${DOCKER_SUBNET_FILE})
        export DOCKER_SUBNET_TO_USE=${aLine/*=}
        SUBNET_TO_USE=${DOCKER_SUBNET_TO_USE%\.*}
    else
        # choose a default subnet 
        SUBNET_TO_USE=${DEFAULT_SUBNET}
    fi

    # first th estatic IP for the services
    export DOCKER_SYSLOG_IP="${SUBNET_TO_USE}.2"
    export DOCKER_REDIS_IP="${SUBNET_TO_USE}.3"
    export DOCKER_PGMASTER_IP="${SUBNET_TO_USE}.4"
    export DOCKER_WEB_1_IP="${SUBNET_TO_USE}.10"
    export DOCKER_WORKER_1_IP="${SUBNET_TO_USE}.20"

    # need to set up the exposed port differently between OSX and Linux.  With OSX the syntax is IP:PORT:PORT where as with
    # linux the only thing needed is just the port number
    if [[ ${OSNAME} == "Darwin" ]]; then
        # web
        export DOCKER_WEB_1_PORT_80="${DOCKER_WEB_1_IP}:80:80"
        export DOCKER_WEB_1_PORT_8000="${DOCKER_WEB_1_IP}:8000:8000"
        export DOCKER_WEB_1_PORT_443="${DOCKER_WEB_1_IP}:443:443"

        # worker
        export DOCKER_WORKER_1_PORT_5555="${DOCKER_WEB_1_IP}:5555:5555"

        # postgres
        export DOCKER_PGMASTER_PORT_5432="${DOCKER_PGMASTER_IP}:5432:5432"

        # redis
        export DOCKER_REDIS_PORT_6379="${DOCKER_REDIS_IP}:6379:6379"

		# need to unalias the ports on lo0
		interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_SYSLOG_IP}")
		if [[ -z ${interfaceOutput} ]]; then
			sudo ifconfig lo0 -alias "${DOCKER_SYSLOG_IP}"
		fi
		interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_IP}")
		if [[ -z ${interfaceOutput} ]]; then
			sudo ifconfig lo0 -alias "${DOCKER_REDIS_IP}"
		fi
		interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_PGMASTER_IP}")
		if [[ -z ${interfaceOutput} ]]; then
			sudo ifconfig lo0 -alias "${DOCKER_PGMASTER_IP}"
		fi
		interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WEB_1_IP}")
		if [[ -z ${interfaceOutput} ]]; then
			sudo ifconfig lo0 -alias "${DOCKER_WEB_1_IP}"
		fi
		interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WORKER_1_IP}")
		if [[ -z ${interfaceOutput} ]]; then
			sudo ifconfig lo0 -alias "${DOCKER_WORKER_1_IP}"
		fi
    else
        # its linux so define the varialbes with just the port
        # web
        export DOCKER_WEB_1_PORT_80="80"
        export DOCKER_WEB_1_PORT_8000="8000"
        export DOCKER_WEB_1_PORT_443="443"

        # worker
        export DOCKER_WORKER_1_PORT_5555="5555"

        # postgres
        export DOCKER_PGMASTER_PORT_5432="5432"

        # redis
        export DOCKER_REDIS_PORT_6379="6379"
    fi

}

#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' ]]; then
    usage
    exit 1
fi

NEW=${@}

envToSource="$(${dcUTILS}/scripts/process_dc_env.py ${NEW})"

if [[ $? -ne 0 ]]; then
    echo $envToSource
    exit 1
else
    eval "$envToSource"
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
dcStartLog "Stopping docker containers for application: ${dcDEFAULT_APP_NAME} env: ${ENV}"

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
#dcLog ${DOCKER_COMPOSE_FILE}

export GENERATED_ENV_FILE="${dcHOME}/${CUSTOMER_APP_UTILS}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-local.env"

#-------------------------------------------------------------------------------
# check to see if the compose file exists
#-------------------------------------------------------------------------------
if [[ ! -f ${DOCKER_COMPOSE_FILE} ]]; then
    dcLog "ERROR: No compose file for the appName: ${dcDEFAULT_APP_NAME}"
    dcLog "so nothing can be started.  You may need to create one manually."
    exit 1
fi

# set up the exported variables and anything else that needs to be cleaned up that we created in start-dc-containers.sh
setupNetwork

# and bring it all down
CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} stop"
#dcLog  ${CMDTORUN}
${CMDTORUN}

dcEndLog "Finished..."
