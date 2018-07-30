#!/usr/bin/env bash
#===============================================================================
#
#          FILE: dcInstanceAccess.sh
#
#         USAGE: ./dcInstanceAccess.sh
#
#   DESCRIPTION: script to either create or remove access from a users machine to a target instance
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Bob Lozano - bob@devops.center
#                Gregg Jensen - gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/27/2017 12:10:12
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

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  usage output
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
usage()
{
cat << EOF

This script will allow secure access to a cloud based server via ssh or via an application
using a specific port. 

Usage: $0 -c create|delete [-p PROFILE] [-r REGION] [-t timeToUseConnection] 
                           [-i authenticationServerName] targetInstanceName [port]

    -c create|delete  - This is the command to perform to either create the port opening or delete it   
    -p PROFILE  - optional option allows one to override the value in the devops.center settings
    -r REGION   - optional option allows one to override the value in the devops.center settings
    -t timeToUseConnection - This is the amount of time you plan to use the connection (in seconds)
                             This might be good if you know you only need the connection for a few
                             minutes rather then the default block of time which is customer dependent.
    -i authenticationServerName - This is an override of the default devops.center authentication
                             server name (dcAuthorization).  This option shouldn't have to be used.
    targetInstanceName  - is the name of the instance you want to access
    port        - if you want to access a specific port for applition access - defaults to 22

EOF
}	# ----------  end of function usage  ----------


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  getValueFromSettings
#   DESCRIPTION:  will get the value of the key passed in from ~/.dcConfig/settings
#    PARAMETERS:  the key to look for
#       RETURNS:  the value of the key once it's found
#-------------------------------------------------------------------------------
getValueFromSettings()
{
    keyToFind=$1
    aKeyValue=$(grep "^${keyToFind}" ~/.dcConfig/settings)
    justTheValue=${aKeyValue#*=}
    # remove any double quotes around the value
    var1=${justTheValue#*\"}
    unquotedVar=${var1%\"}
    echo "${unquotedVar#*=}"
}	# ----------  end of function getValueFromSettings  ----------


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  getAddressForAuthorizationServer
#   DESCRIPTION:  get the public IP of the dcAuthorization server
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
getAddressForAuthorizationServer ()
{
    AUTHENTICATION_SERVER_NAME=${1:-"dcAuthorization"}

    AUTHENTICATION_SERVER_IP=$(aws ec2 --profile "${PROFILE}" --region ${REGION} describe-instances --filter "Name=tag-value,Values=${AUTHENTICATION_SERVER_NAME}" "Name=tag-value,Values=service" "Name=instance-state-name,Values=running" | jq -r '.Reservations[].Instances[].PublicIpAddress')
    # now check to make sure we have an IP
    # TODO probably need to see if there is more then one returned...at some point...maybe
    if [[ -z ${AUTHENTICATION_SERVER_IP} ]]; then
        echo "ERROR: your dcAuthorization server does not appear to be available, contact your devops.center representative."
        exit 1
    fi
}	# ----------  end of function getAddressForAuthorizationServer  ----------



############################################################# end of function definitions


#-------------------------------------------------------------------------------
# process command line arguments
#-------------------------------------------------------------------------------
if [[ $# -eq 0 ]] || [[ $1 == "-h" ]] || [[ $1 == "-?" ]]; then
    usage
    exit 1
fi

# by default if they don't provide a port, then we assume they want ssh access
PORT=22
DEBUG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -c ) shift
                # lowercase the string
                COMMAND=${1,,}
                ;;
        -p ) shift
                PROFILE=$1
                ;;
        -r ) shift
                REGION=$1
                ;;
        -s ) shift
                SERVER_NAME=$1
                ;;
        -u ) shift
                USER_NAME=$1
                ;;
        -t ) shift
                REQUESTED_TIME=$1
                ;;
        -i ) shift
                AUTHENTICATION_SERVER_NAME=$1
                ;;
#        -k ) shift
#                AUTH_SERVER_KEY=$1
#                ;;
        --debug )
                DEBUG=true
                ;;
        -h ) usage
             exit 1
                 ;;
        [!-]* ) if [[ $# -eq 2 ]]; then
                    SERVER_NAME=$1
                    PORT=$2
                    shift; shift
                else
                    if [[ $# -eq 1 ]]; then
                        SERVER_NAME=$1
                        shift
                    else
                        echo "No server provided...no where to go, exiting..."
                        usage
                        exit 1
                    fi
                fi
                ;;
    esac
    shift
done

if [[ -z ${SERVER_NAME} ]]; then
    echo "You must provide a server name to go to...."
    echo
    usage
    exit 1
fi


#-------------------------------------------------------------------------------
# main process
#-------------------------------------------------------------------------------

# get the PROFILE REGION CUSTOMER_NAME USER_NAME from the ~/.dcConfig/settings
if [[ -z ${PROFILE} ]]; then
    PROFILE=$(getValueFromSettings "PROFILE")
fi
if [[ -z ${REGION} ]]; then
    REGION=$(getValueFromSettings "REGION")
fi

# get the public IP of the dcAuthorization server
getAddressForAuthorizationServer ${AUTHENTICATION_SERVER_NAME}

#CUSTOMER_NAME=$(getValueFromSettings "CUSTOMER_NAME")
if [[ -z ${USER_NAME} ]]; then
    USER_NAME=$(getValueFromSettings "USER_NAME")
fi

if [[ -z ${AUTH_SERVER_KEY} ]]; then
    AUTH_SERVER_KEY="~/.ssh/devops.center/dcauthor-${USER_NAME}-key.pem"
fi

# use these credentials to authenticate to devops.center
#echo "PROFILE=${PROFILE}"
#echo "REGION=${REGION}"
##echo "CUSTOMER_NAME=${CUSTOMER_NAME}"
#echo "USER_NAME=${USER_NAME}"

# get the access IP that this machine is coming from 
ACCESS_IP=$(curl -s -4 icanhazip.com)
#echo ${ACCESS_IP}

# check all arguments ... terminate if any are missing
if [[ -z ${PROFILE} ]]; then
    echo "PROFILE does not appear to be set and is required, exiting..."
    exit 1
fi
if [[ -z ${REGION} ]]; then
    echo "REGION does not appear to be set and is required, exiting..."
    exit 1
fi
if [[ -z ${USER_NAME} ]]; then
    echo "USER_NAME does not appear to be set and is required, exiting..."
    exit 1
fi
#if [[ -z ${USERS_TFA_TOKEN} ]]; then
#    echo "USERS_TFA_TOKEN does not appear to be set and is required, exiting..."
#    exit 1
#fi
if [[ -z ${ACCESS_IP} ]]; then
    echo "We can not determine the IP of your local machine, exiting..."
    exit 1
fi
if [[ -z ${PORT} ]]; then
    echo "PORT does not appear to be set and is required"
    exit 1
fi

# get this device's name
DEVICE_FOR_ACCESS=$(hostname)

#-------------------------------------------------------------------------------
# now we need to do an ssh into the authenication server to have it open the 
# the security group 
#-------------------------------------------------------------------------------

if [[ ${DEBUG} == "true" ]]; then
    set -x
fi

echo "Checking ${COMMAND} access for user: ${USER_NAME}"

# need to make a call to the ssh-agent and ssh-add 
#eval `ssh-agent`
#ssh-add ${AUTH_SERVER_KEY}

if [[ ${COMMAND} == "create" ]]; then
    # using port 62422 is what was used for containers...doesn't work for instances
    #SSH_RESULTS=$(ssh -o PasswordAuthentication=no -p 62422 -i ${AUTH_SERVER_KEY} ${USER_NAME}@${AUTHENTICATION_SERVER_IP} "create-access -p ${PROFILE} -r ${REGION} -a ${ACCESS_IP} -u ${USER_NAME} -s ${SERVER_NAME} --port ${PORT} -d ${DEVICE_FOR_ACCESS} -t ${REQUESTED_TIME}" 2>&1 >>/dev/null)
    SSH_RESULTS=$(ssh -o PasswordAuthentication=no -p 22 -i ${AUTH_SERVER_KEY} ${USER_NAME}@${AUTHENTICATION_SERVER_IP} "create-access -p ${PROFILE} -r ${REGION} -a ${ACCESS_IP} -u ${USER_NAME} -s ${SERVER_NAME} --port ${PORT} -d ${DEVICE_FOR_ACCESS} -t ${REQUESTED_TIME}" 2>&1 >>/dev/null)
else
    # using port 62422 is what was used for containers...doesn't work for instances
    #SSH_RESULTS=$(ssh -o PasswordAuthentication=no -p 62422 -i ${AUTH_SERVER_KEY} ${USER_NAME}@${AUTHENTICATION_SERVER_IP} "delete-access -p ${PROFILE} -r ${REGION} -a ${ACCESS_IP} -u ${USER_NAME} -s ${SERVER_NAME} --port ${PORT} -d ${DEVICE_FOR_ACCESS} -t ${REQUESTED_TIME}" 2>&1 >>/dev/null)
    SSH_RESULTS=$(ssh -o PasswordAuthentication=no -p 22 -i ${AUTH_SERVER_KEY} ${USER_NAME}@${AUTHENTICATION_SERVER_IP} "delete-access -p ${PROFILE} -r ${REGION} -a ${ACCESS_IP} -u ${USER_NAME} -s ${SERVER_NAME} --port ${PORT} -d ${DEVICE_FOR_ACCESS} -t ${REQUESTED_TIME}" 2>&1 >>/dev/null)
fi

if [[ "${SSH_RESULTS}" == *"success" ]]; then
    echo "success"
else
    echo "not successful"   
fi
