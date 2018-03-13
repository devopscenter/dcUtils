#!/usr/bin/env bash
#===============================================================================
#
#          FILE: start-dc-containers.sh
#
#         USAGE: ./start-dc-containers.sh
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
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/17/2016 11:07:36
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

DEFAULT_SUBNET="172.36.4.0/24"

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: start-dc-containers.sh [--appName appName] [--debug] [--service nameOfService]"
    echo
    echo -e "This script will start the docker containers for the application"
    echo -e "to be able to set up a local devlopment environment."
    echo 
    echo -e "--appName|-a  is the name of the application that you want to"
    echo -e "      run as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--debug|-d    will start the web-debug configuration rather than the web one"
    echo -e "--service|-s  takes the name of the service to start.  The name of the service"
    echo -e "      can be found inside the docker-compose.yml file that is used to start"
    echo -e "      all of the services.  The service name is the defining name of a service"
    echo -e "      section and is not the name of the container as seen by docker ps -a."
    echo -e "      This may be something like: web, worker, pgmaster-1 etc."
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

        # redis
        export DOCKER_REDIS_PORT_6379="${DOCKER_REDIS_IP}:6379:6379"

        # since this operating system is OSX then we have to set up an alias on lo0 (the interface
        # that docker talks on) to set up a connection to the container
        # in linux the bridge is created with an interface that the host can access
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_SYSLOG_IP}")
        if [[ -z ${interfaceOutput} ]]; then
            sudo ifconfig lo0 alias "${DOCKER_SYSLOG_IP}"
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_IP}")
        if [[ -z ${interfaceOutput} ]]; then
            sudo ifconfig lo0 alias "${DOCKER_REDIS_IP}"
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_USER_1_IP}")
        if [[ -z ${interfaceOutput} ]]; then
            sudo ifconfig lo0 alias "${DOCKER_REDIS_USER_1_IP}"
        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_USER_2_IP}")
#        if [[ -z ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 alias "${DOCKER_REDIS_USER_2_IP}"
#        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_USER_3_IP}")
#        if [[ -z ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 alias "${DOCKER_REDIS_USER_3_IP}"
#        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_REDIS_USER_4_IP}")
#        if [[ -z ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 alias "${DOCKER_REDIS_USER_4_IP}"
#        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_PGMASTER_IP}")
        if [[ -z ${interfaceOutput} ]]; then
            sudo ifconfig lo0 alias "${DOCKER_PGMASTER_IP}"
        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WEB_1_IP}")
        if [[ -z ${interfaceOutput} ]]; then
            sudo ifconfig lo0 alias "${DOCKER_WEB_1_IP}"
        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WEB_2_IP}")
#        if [[ -z ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 alias "${DOCKER_WEB_2_IP}"
#        fi
        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WORKER_1_IP}")
        if [[ -z ${interfaceOutput} ]]; then
            sudo ifconfig lo0 alias "${DOCKER_WORKER_1_IP}"
        fi
#        interfaceOutput=$(ifconfig lo0 | grep "${DOCKER_WORKER_2_IP}")
#        if [[ -z ${interfaceOutput} ]]; then
#            sudo ifconfig lo0 alias "${DOCKER_WORKER_2_IP}"
#        fi

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

        # redis
        export DOCKER_REDIS_PORT_6379="6379"
    fi

}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  findContainerName
#   DESCRIPTION:  loops through the compose config and searchs for a container
#                 name that is associated with service name
#    PARAMETERS:
#       RETURNS:  container_name value
#-------------------------------------------------------------------------------
findContainerName()
{
    local serviceName=$1

    ALL_CONFIG=($(docker-compose -f ${DOCKER_COMPOSE_FILE} config))
    NUM_LINES=${#ALL_CONFIG[@]}
    c=0
    while [[ ${c} -lt ${NUM_LINES} ]]
    do
        if [[ ${ALL_CONFIG[$c]} == "services:" ]]; then
            # now contiue until the current service is found
            while [[ ${c} -lt ${NUM_LINES} ]]
            do
                c=$(($c + 1))
                if [[ ${ALL_CONFIG[$c]} == "${serviceName}:" ]]; then
                    while [[ ${c} -lt ${NUM_LINES} ]]
                    do
                        c=$(($c + 1))
                        if [[ ${ALL_CONFIG[$c]} == "container_name:" ]]; then
                            # its the next one
                            c=$(($c + 1))
                            echo ${ALL_CONFIG[${c}]}
                            return
                        fi
                    done
                fi
            done
        fi
        c=$(($c + 1))
    done
}


#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' ]] || [[ $1 == '--help' ]]; then
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
        --service|-s ) shift;
            SERVICE_TO_START=$1
            ;;
    esac
    shift
done


dcStartLog "Docker containers for application: ${dcDEFAULT_APP_NAME} env: ${ENV}"

#-------------------------------------------------------------------------------
# first we need to see if postgresql is running locally, and if so stop and
# let the user know that we can't run the db containers and the local postgresql
# at the same time.  The ports will collide and the db container will not start.
#-------------------------------------------------------------------------------

if [[ -z $SERVICE_TO_START} ]]; then
    postgres=$(ps -ef|grep postgres | grep -v grep)
    set -e
    if [ -n "$postgres" ]; then
        dcLog "*** courtesy warning ***"
        dcLog "postgres running, please exit postgres and try starting again."
        return 1 2> /dev/null || exit 1
    fi
    set +e
fi

#-------------------------------------------------------------------------------
# We have all the information for this so lets run the docker-compose up with
# the appropriate appName
#-------------------------------------------------------------------------------

# TODO - determine if we want to run in the customers directory
#cd ${dcUTILS}

if [[ ${DEBUG} -eq 1 ]]; then
    DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose-debug.yml"
else
    DOCKER_COMPOSE_FILE="${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/${CUSTOMER_APP_ENV}/docker-compose.yml"
fi
# echo ${DOCKER_COMPOSE_FILE}

export GENERATED_ENV_FILE="${dcHOME}/${CUSTOMER_APP_UTILS}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-local.env"

#-------------------------------------------------------------------------------
# check to see if the compose file exists
#-------------------------------------------------------------------------------
if [[ ! -f ${DOCKER_COMPOSE_FILE} ]]; then
    dcLog "ERROR: No compose file for the appName: ${dcDEFAULT_APP_NAME}"
    dcLog "so nothing can be started.  You may need to create one manually."
    exit 1
fi

OSNAME=$(uname -s)
setupNetwork


if [[ ${SERVICE_TO_START} ]]; then
    CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} start ${SERVICE_TO_START}"
else
    CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} up -d"
fi

dcLog  "${CMDTORUN}"
${CMDTORUN}

# allow multiple docker containers networks to talk to each other, but needs to do it after the containers are up
if [[ ${OSNAME} != "Darwin" ]]; then
    if [[ ${MULTI_DOCKER_STACK_COMMUNICATION} == "yes" ]]; then
        echo 
        echo "We need to update the local iptables so that the multiple stacks can talk to each other"
        echo "So, you may be asked to enter your password to do this"
        sudo iptables --flush DOCKER-ISOLATION
    fi
fi

echo 
echo "The IPs for each container will be put in /etc/hosts which requires sudo access."
echo "So, you may be asked to enter your password to write these entries, if they do not already exist."

dockerSeparator="################## docker containers"
separator=$(grep "${dockerSeparator}" /etc/hosts)
if [[ -z ${separator} ]]; then
    echo | sudo tee -a /etc/hosts > /dev/null
    echo | sudo tee -a /etc/hosts > /dev/null
    echo "${dockerSeparator}" | sudo tee -a /etc/hosts > /dev/null
fi

SERVICES=($(docker-compose -f ${DOCKER_COMPOSE_FILE} config --services))
for service in ${SERVICES[@]}
do
    CONTAINER_NAME=$(findContainerName $service)
    serviceIP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${CONTAINER_NAME})
    hostEntry=$(grep ${CONTAINER_NAME} /etc/hosts)

    echo "${CONTAINER_NAME} => ${serviceIP}"
    if [[ ${hostEntry} ]]; then
        # it was there so we need to see if the IP is different
        tmpArray=(${hostEntry})
        if [[ ${tmpArray[0]} != ${serviceIP} ]]; then
            # the entry was there but the IP is different
            sudo sed -i.bak "/$CONTAINER_NAME/ s/.*/${serviceIP}    $CONTAINER_NAME/" /etc/hosts
        fi
    else
        # it wasn't there so append it
        if [[ ${serviceIP} ]]; then 
            echo "${serviceIP}    ${CONTAINER_NAME} " | sudo tee -a /etc/hosts > /dev/null
        fi
    fi
        set +x
done

dcEndLog "Finished..."
exit
