#!/usr/bin/env bash
#===============================================================================
#
#          FILE: stop-dc-containers.sh
#
#         USAGE: stop-dc-containers.sh
#
#   DESCRIPTION:  Stops the containers that were started with docker-compose
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/17/2016 16:27:42
#      REVISION:  ---
#
# Copyright 2014-2017 devops.center llc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#===============================================================================

#set -o nounset     # Treat unset variables as an error
#set -o errexit      # exit immediately if command exits with a non-zero status
#set -x             # essentially debug mode

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: stop.sh [--appName appName] [--debug]--cleanup"
    echo
    echo -e "This script will stop the docker containers found running that are"
    echo -e "specific to the application and no others.  The containers will be "
    echo -e "stopped so the state will not be lost when they are started again"
    echo 
    echo -e "--appName is the name of the application that you want to"
    echo -e "      stop as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--debug will use the web-debug configuration rather than the normal web one"
    echo -e "--cleanup  will remove networks items that were setup when the"
    echo -e "      start-dc-containers.sh was executed."
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
    export DOCKER_PGMASTER_IP="${SUBNET_TO_USE}.4"
    export DOCKER_MONGODB_IP="${SUBNET_TO_USE}.5"
    export DOCKER_WEB_1_IP="${SUBNET_TO_USE}.10"
    export DOCKER_WEB_2_IP="${SUBNET_TO_USE}.11"
    export DOCKER_WORKER_1_IP="${SUBNET_TO_USE}.20"
    export DOCKER_WORKER_2_IP="${SUBNET_TO_USE}.21"
    export DOCKER_REDIS_IP="${SUBNET_TO_USE}.30"  # reserved for redismaster
    export DOCKER_REDIS_USER_1_IP="${SUBNET_TO_USE}.31"
    export DOCKER_REDIS_USER_2_IP="${SUBNET_TO_USE}.32"
    export DOCKER_REDIS_USER_3_IP="${SUBNET_TO_USE}.33"
    export DOCKER_REDIS_USER_4_IP="${SUBNET_TO_USE}.34"

    # need to set up the exposed port differently between OSX and Linux.  With OSX the syntax is IP:PORT:PORT where as with
    # linux the only thing needed is just the port number
    if [[ ${OSNAME} == "Darwin" ]]; then
        # container web 1
        export DOCKER_WEB_1_PORT_80="${DOCKER_WEB_1_IP}:80:80"
        export DOCKER_WEB_1_PORT_8000="${DOCKER_WEB_1_IP}:8000:8000"
        export DOCKER_WEB_1_PORT_443="${DOCKER_WEB_1_IP}:443:443"
        # container web 2
        export DOCKER_WEB_2_PORT_80="${DOCKER_WEB_2_IP}:80:80"
        export DOCKER_WEB_2_PORT_8000="${DOCKER_WEB_2_IP}:8000:8000"
        export DOCKER_WEB_2_PORT_443="${DOCKER_WEB_2_IP}:443:443"

        # worker 1
        export DOCKER_WORKER_1_PORT_5555="${DOCKER_WEB_1_IP}:5555:5555"
        # worker 2
        export DOCKER_WORKER_2_PORT_5555="${DOCKER_WEB_2_IP}:5555:5555"

        # postgres
        export DOCKER_PGMASTER_PORT_5432="${DOCKER_PGMASTER_IP}:5432:5432"

        # mongodb
        export DOCKER_MONGODB_PORT_27017="${DOCKER_MONGODB_IP}:27017:27017"

        # redis
        export DOCKER_REDIS_PORT_6379="${DOCKER_REDIS_IP}:6379:6379"

    else
        # its linux so define the variables with just the port
        # web
        export DOCKER_WEB_1_PORT_80="80"
        export DOCKER_WEB_1_PORT_8000="8000"
        export DOCKER_WEB_1_PORT_443="443"

        # web 2
        export DOCKER_WEB_2_PORT_80="80"
        export DOCKER_WEB_2_PORT_8000="8000"
        export DOCKER_WEB_2_PORT_443="443"

        # worker
        export DOCKER_WORKER_1_PORT_5555="5555"

        # worker 2
        export DOCKER_WORKER_2_PORT_5555="5555"

        # postgres
        export DOCKER_PGMASTER_PORT_5432="5432"

        # mongodb
        export DOCKER_MONGODB_PORT_27017="27017"

        # redis
        export DOCKER_REDIS_PORT_6379="6379"
    fi

}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  tearDownNetwork
#   DESCRIPTION:  removes any network configs that need to be removed/taken down
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
tearDownNetwork()
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
    export DOCKER_MONGODB_IP="${SUBNET_TO_USE}.5"
    export DOCKER_WEB_1_IP="${SUBNET_TO_USE}.10"
#    export DOCKER_WEB_2_IP="${SUBNET_TO_USE}.11"     # if needed
    export DOCKER_WORKER_1_IP="${SUBNET_TO_USE}.20"
#    export DOCKER_WORKER_2_IP="${SUBNET_TO_USE}.21"  # if needed

    # need to set up the exposed port differently between OSX and Linux.  With OSX the syntax is IP:PORT:PORT where as with
    # linux the only thing needed is just the port number
    if [[ ${OSNAME} == "Darwin" ]]; then
        # since this operating system is OSX then we have to set up an alias on lo0 (the interface
        # that docker talks on) to set up a connection to the container
        # in linux the bridge is created with an interface that the host can access
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_SYSLOG_IP} ")
        if [[ ${interfaceOutput} ]]; then
            sudo ifconfig lo0 -alias "${DOCKER_SYSLOG_IP}"
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_IP} ")
        if [[ ${interfaceOutput} ]]; then
            sudo ifconfig lo0 -alias "${DOCKER_REDIS_IP}"
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_PGMASTER_IP} ")
        if [[ ${interfaceOutput} ]]; then
            sudo ifconfig lo0 -alias "${DOCKER_PGMASTER_IP}"
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_MONGODB_IP} ")
        if [[ ${interfaceOutput} ]]; then
            sudo ifconfig lo0 -alias "${DOCKER_MONGODB_IP} "
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WEB_1_IP} ")
        if [[ ${interfaceOutput} ]]; then
            sudo ifconfig lo0 -alias "${DOCKER_WEB_1_IP}"
        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WEB_2_IP} ")
#        if [[ ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 -alias "${DOCKER_WEB_2_IP}"
#        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WORKER_1_IP} ")
        if [[ ${interfaceOutput} ]]; then
            sudo ifconfig lo0 -alias "${DOCKER_WORKER_1_IP}"
        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WORKER_2_IP} ")
#        if [[ -z ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 alias "${DOCKER_WORKER_2_IP}"
#        fi

    else
        # TODO need to remove the network element also
        # docker network rm NETWORK_BRIDGE_NAME
        docker network prune
    fi

}

#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' ]] || [[ $1 == '--help' ]]; then
    usage
    exit 1
fi

# defaults
CLEAN_UP_NETWORK=0

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
        --service|-s ) shift;
            SERVICE_TO_STOP=$1
            ;;
        --cleanup|-c )
            CLEAN_UP_NETWORK=1
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
OSNAME=$(uname -s)
setupNetwork

# check to see if we are running a multiple apps stacks and if they are on MacOS we need to remove the containers before
# stopping the containers.
if [[ ${OSNAME} == "Darwin" ]]; then
    if [[ ${MULTI_DOCKER_STACK_COMMUNICATION} ]]; then
        ${dcUTILS}/cross-join-networks.sh -c disconnect -a1 ${dcDEFAULT_APP_NAME}  -a2 ${MULTI_DOCKER_STACK_COMMUNICATION} -t web
    fi
fi

if [[ ${SERVICE_TO_STOP} ]]; then
    CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} stop ${SERVICE_TO_STOP}"
else
    CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} stop"
fi
# and bring it all down
dcLog  "${CMDTORUN}"
${CMDTORUN}

if [[ ${CLEAN_UP_NETWORK} -eq 1 ]]; then
    tearDownNetwork
fi

dcEndLog "Finished..."
