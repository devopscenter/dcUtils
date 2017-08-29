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
    echo -e "Usage: start.sh [--appName appName] [--env theEnv] [-d]"
    echo
    echo -e "This script will start the docker containers for the application"
    echo -e "to be able to set up a local devlopment environment."
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

    SERVICES=($(docker-compose -f ${DOCKER_COMPOSE_FILE} config --services 2>&1 > /dev/null))
    NUM_SERVICES=${#SERVICES[@]}
    count=0
    
    for number in {2..9}
    do
        if [[ ${count} -ge ${NUM_SERVICES} ]]; then
            break
        fi

        # set up the statis ip
        export DOCKER_STATIC_IP_$((${number}-1))="${SUBNET_TO_USE}.${number}"
        count=$((${count}+1))

        # if the os is OSX then we have to set up an alias on lo0 (the interface
        # that docker talks on) to set up a connection to the container
        # in linux the bridge is created with an interface that the host can access
        if [[ ${OSNAME} == "Darwin" ]]; then
            interfaceOutput=$(ifconfig lo0 | grep "${SUBNET_TO_USE}.${number}")
            if [[ -z ${interfaceOutput} ]]; then
                sudo ifconfig lo0 alias "${SUBNET_TO_USE}.${number}"
            fi
        fi
    done
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
    set +x
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


dcStartLog "Docker containers for application: ${dcDEFAULT_APP_NAME} env: ${ENV}"

#-------------------------------------------------------------------------------
# first we need to see if postgresql is running locally, and if so stop and
# let the user know that we can't run the db containers and the local postgresql
# at the same time.  The ports will collide and the db container will not start.
#-------------------------------------------------------------------------------

postgres=$(ps -ef|grep postgres | grep -v grep)
set -e
if [ -n "$postgres" ]; then
    dcLog "*** courtesy warning ***"
    dcLog "postgres running, please exit postgres and try starting again."
    return 1 2> /dev/null || exit 1
fi
set +e

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

CMDTORUN="docker-compose -f ${DOCKER_COMPOSE_FILE} -p ${dcDEFAULT_APP_NAME} up -d"
dcLog  ${CMDTORUN}
${CMDTORUN}


SERVICES=($(docker-compose -f ${DOCKER_COMPOSE_FILE} config --services))
for service in ${SERVICES[@]}
do
    CONTAINER_NAME=$(findContainerName $service)
        set -x
    serviceIP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${CONTAINER_NAME})
    hostEntry=$(grep ${CONTAINER_NAME} /etc/hosts)

    if [[ ${hostEntry} ]]; then
        # it was there so we need to see if the IP is different
        tmpArray=(${hostEntry})
        if [[ ${tmpArray[0]} != ${serviceIP} ]]; then
            # the entry was there but the IP is different
            #sudo sed -i.bak "/$CONTAINER_NAME/ s/.*/${tmpIP}    $CONTAINER_NAME/" /etc/hosts
            sudo sed -i.bak "/$CONTAINER_NAME/ s/.*/${serviceIP}    $CONTAINER_NAME/" /etc/hosts
            #sudo sed -i.bak "s/.*${CONTAINER_NAME}/${tmpIP}    $CONTAINER_NAME/" /etc/hosts
        fi
    else
        # it wasn't there so append it
        echo "${serviceIP}    ${CONTAINER_NAME} " | sudo tee -a /etc/hosts > /dev/null
    fi
        set +x
done

dcEndLog "Finished..."
exit
