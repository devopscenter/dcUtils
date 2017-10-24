#!/usr/bin/env bash
#===============================================================================
#
#          FILE: main.sh
#
#         USAGE: ./main.sh
#
#   DESCRIPTION: This script provides an example of how to use the process_dc_env.py in a shell
#                script.   In a shell script, the  process_dc_env.py is envoked like it would be
#                from the command line.  As such, you would either set the ${dcUTILS} or hardcode
#                the path to where the ${dcUTILS}/scripts is relative to your script's location.
#                The python program will handle the options that are needed to determine the 
#                environment and read in the appropriate set of environment variables.  You would
#                then provide all the necessary arguments for the environemnt as well as what
#                you need for your script.  The options passed in can be scanned for you script
#                specific arguments after the process_dc_env culls what it needs.  An example is
#                below
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 01/26/2017 10:51:37
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
set -x             # essentially debug mode

# NOT USUAL to call the initialCreate from a shell script.  It was really meant
# to be used with manageApp.py as it creates the things that process_dc_env 
# reads
#NEW=${@}" --initialCreate"

# normal call ..the way it is meant to be for all shell scripts ...hopefully
NEW=${@}

dcUTILS=".."

envToSource="$(${dcUTILS}/scripts/process_dc_env.py ${NEW})"

if [[ $? -ne 0 ]]; then
    echo $envToSource
    exit 1
else
    eval "$envToSource"
fi

# EXAMPLE: add the arument --foo "something here" and see that it comes out below
while [[ $# -gt 0 ]]; do
    case $1 in 
        --foo ) shift
                FOO=$1
                ;;
    esac
    shift
done


dcStartLog "Begin tests"
#env
dcLog "CUSTOMER_APP_NAME = ${CUSTOMER_APP_NAME}"
dcLog "FOO = ${FOO}"

CUSTOMER_NAME="rmsa"
CUSTOMER_APP_NAME="f2-prod-web1"
EVENT="volume added"
MSG="TEST TEST TEST 100GB disk volume added"
dcTrackEvent "${CUSTOMER_NAME}" "${CUSTOMER_APP_NAME}" "${EVENT}" "${MSG}"

dcEndLog "Finished..."
