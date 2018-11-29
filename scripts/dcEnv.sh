#!/usr/bin/env bash
#===============================================================================
#
#          FILE: dcEnv.sh
# 
#         USAGE: ./dcEnv.sh 
# 
#   DESCRIPTION: script to include in other scripts that set up the environment
#                and provides some basic utility functions
#                NOTE: this script differs than the one that is put on the 
#                instances as the one on the instance doesn't know about the 
#                shared drive.  This one will use the dcCOMMON_SHARED_DIR found
#                in the .dcConfig/settings file that was set up with RUN_ME_FIRST.sh
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 03/21/2017 12:02:46
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

driveName=$(grep dcCOMMON_SHARED_DIR ~/.dcConfig/settings)
var1=${driveName#*\"}
dcCOMMON_SHARED_DIR=${var1%\"}

dcLog()
{
    msg=$1
    state=$2

    scriptName=$(basename -- "$0")
    TIMESTAMP=$(date +%F_%T)

    if [[ ! -z ${state} ]]; then
        echo "[${TIMESTAMP}]:${scriptName}:${state}:${msg}"
    else
        echo "[${TIMESTAMP}]:${scriptName}::${msg}"
    fi
}

dcStartLog()
{
    msg=$1
    dcLog "${msg}" "START"
}

dcEndLog()
{
    msg=$1
    dcLog "${msg}" "END"
}

dcTrackEvent()
{
    CUSTOMER_NAME=$1
    CUSTOMER_APP_NAME=$2
    EVENT=$3
    MSG=$4
    if [[ -n ${dcCOMMON_SHARED_DIR} ]]; then
        TRACKING_FILE="${dcCOMMON_SHARED_DIR}/devops.center/monitoring/dcEventTracking.txt"

        if [[ ! -f "${TRACKING_FILE}" ]]; then
            dcLog "ERROR: ${TRACKING_FILE} not found, the event will not be written"
        else
            TIMESTAMP=$(date +%F_%T)
            JSONTOWRITE="{\"date\": \"${TIMESTAMP}\", \"customer\": \"${CUSTOMER_NAME}\", \"instancename\": \"${CUSTOMER_APP_NAME}\", \"event\": \"${EVENT}\", \"msg\": \"${MSG}\"} "
            echo "${JSONTOWRITE}" >> "${TRACKING_FILE}"
        fi
    else
        echo "Could not save event, file not available"
    fi
}
