#!/usr/bin/env bash
#===============================================================================
#
#          FILE: cross-join-containers.sh
#
#         USAGE: ./cross-join-containers.sh
#
#   DESCRIPTION: This script has a very specific purpose and that is to take
#                a container from one network and add it to a other network 
#                and then do the same for a container in the other network.
#                This is for the scenario that there are two app stacks with
#                two sets of docker containers each with their own network.
#                This is used when there needs to be two containers that need
#                to talk to each other while sitting in their separate network.
#                Effectively the same type of container in each network will be
#                cross joined to the others network, so each container will be
#                part of two networks.
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Bob Lozano - bob@devops.center
#                Gregg Jensen - gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 04/29/2018 17:37:19
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
#set -o errexit     # exit immediately if command exits with a non-zero status
#set -o verbose     # print the shell lines as they are executed
#set -x             # essentially debug mode

usage()
{
cat << EOF

USAGE: cross-join-containers.sh --app1 appName1 --app2 appName2 --type containerType

    --app1|-a1 appName1 is the application name for one of the app stacks that is 
              running in it's own network.

    --app2|-a2 appName2 is the application name for one of the app stacks that is 
              running in it's own network.

    --type|-t containerType take the word from the name of the container that describes
              the type.
              Example: f1-local-web-1 and f2-local-web-1 need to cross joined in the
              others network.  The type is: web  so:

              cross-join-containres.sh -t web


EOF
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  checkForTwoRunningContainers
#   DESCRIPTION:  checks for two containers that have the given type are running
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
checkForTwoRunningContainers ()
{
    local A1=$1
    local A2=$2
    local ATYPE=$3
    local RET=0

    # need to run the docker command to see the running contianers
    c=0
    NAME_LIST=$(docker ps --format '{{.Names}}')
    if [[ ${NAME_LIST} == *"${A1}-local-${ATYPE}"* ]]; then
        c=$((c+1))
    fi

    if [[ ${NAME_LIST} == *"${A2}-local-${ATYPE}"* ]]; then
        c=$((c+1))
    fi

    if [[ $c -ne 2 ]]; then
        RET=1
    fi

    echo ${RET}
}	# ----------  end of function checkForTwoRunningContainers  ----------

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  checkForTwoNetworks
#   DESCRIPTION:  check to see if the network for each app has been set up
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
checkForTwoNetworks ()
{
    local A1=$1
    local A2=$2
    local RET=0
    # need to check for both app stacks network has been set up
    c=0
    NETWORK_LIST=$(docker network ls --format '{{.Name}}')
    if [[ ${NETWORK_LIST} == *"${A1}_local_network"* ]]; then
        c=$((c+1))
    fi

    if [[ ${NETWORK_LIST} == *"${A2}_local_network"* ]]; then
        c=$((c+1))
    fi

    if [[ $c -ne 2 ]]; then
        RET=1
    fi

    echo ${RET}
}	# ----------  end of function checkForTwoNetworks  ----------
#-------------------------------------------------------------------------------
# Make sure there are the exact number of arguments
#-------------------------------------------------------------------------------
if [[ $# -le 1 ]]; then
    usage
    exit 1
fi

#-------------------------------------------------------------------------------
# Loop through the arguments and assign input args with the appropriate variables
#-------------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case ${1} in
      --app1|-a1 )   shift
             APP_1=$1
             ;;
      --app2|-a2 )   shift
             APP_2=$1
             ;;
      --type|-t )   shift
             CONTAINER_TYPE=$1
             ;;
      * )    usage
             exit 1
    esac
    shift
done


#-------------------------------------------------------------------------------
# Now see if there are two containers running with that type 
#-------------------------------------------------------------------------------
RET_VAL=$(checkForTwoRunningContainers ${APP_1} ${APP_2} ${CONTAINER_TYPE})

if [[ ${RET_VAL} -eq 1 ]]; then
    exit 1
fi


#-------------------------------------------------------------------------------
# OK, there must be two running so lets continue.
# now check for the two networks
#-------------------------------------------------------------------------------
RET_VAL=$(checkForTwoNetworks ${APP_1} ${APP_2})

if [[ ${RET_VAL} -eq 1 ]]; then
    exit 1
fi


#-------------------------------------------------------------------------------
# And if we get here, then the containers are running and the two networks are
# setup.  So, now we need to see if the containers are already cross joined 
#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------
# OK, lets join each container to the others network
#-------------------------------------------------------------------------------
APP1_NAME=$(docker ps  --filter name="$APP_1-local-${CONTAINER_TYPE}*" --format '{{.Names}}')
NETWORK1_NAME=${APP_1}_local_network
APP2_NAME=$(docker ps  --filter name="$APP_2-local-${CONTAINER_TYPE}*" --format '{{.Names}}')
NETWORK2_NAME=${APP_2}_local_network

# to to cross
docker network connect ${NETWORK2_NAME} ${APP1_NAME} >/dev/null 2>&1 
docker network connect ${NETWORK1_NAME} ${APP2_NAME} >/dev/null 2>&1 
