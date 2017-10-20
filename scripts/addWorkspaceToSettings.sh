#!/usr/bin/env bash
#===============================================================================
#
#          FILE: addWorkspaceToSettings.sh
# 
#         USAGE: ./addWorkspaceToSettings.sh 
# 
#   DESCRIPTION: This script will go through the ~/dcConfig/baseDirectory file that
#                contains all the mapping of directory to workspace.  This script will
#                make a variable for each workspace that can be used to refer to that
#                base location.  For example, using it in a cd command rather then typing
#                a potentially long path
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 06/07/2017 10:49:09
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

BASE_CONFIG_FILE=$HOME/.dcConfig/baseDirectory
SETTINGS_FILE=$HOME/.dcConfig/settings

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  updateSettings
#   DESCRIPTION:  Takes a line and either adds or updates the line in the settings file
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
updateSettings()
{
    ENVITEM=$1
    THEDIR=$2
    LINETOADD="${ENVITEM}=${THEDIR}"
    echo ${LINETOADD}
    set -x
    if [[ $(grep ${ENVITEM} ${SETTINGS_FILE}) ]]; then
        # it was in the file so update it
        THEDIR="${THEDIR//\//\\/}"
        sed -i -e "s/${ENVITEM}=.*/${ENVITEM}=${THEDIR}/" "${SETTINGS_FILE}"
    else
        # it was not in the file so add it 
        echo ${LINETOADD} >> ${SETTINGS_FILE}
    fi
    set +x
}

#-------------------------------------------------------------------------------
# read the baseDirectory file and for each specific workspace found create an export variable
#-------------------------------------------------------------------------------
if [[ ! -f ${BASE_CONFIG_FILE} ]]; then
    echo "ERROR: The base directory file does not exist or not accessible: ${BASE_CONFIG_FILE}"
    echo "This gets created the first time you run through manageApp.py when an application is created"
    exit
fi

while IFS= read -r aLine
do
    if [[ ${aLine} == *"_BASE_CUSTOMER_DIR="* ]]; then
        ENVSTR=${aLine%%=*}
        ENVITEM=$(echo ${ENVSTR} | cut -d "_" -f2)"_DIR"
        THEDIR=${aLine##*=}

        updateSettings ${ENVITEM} ${THEDIR}
    fi
done < "${BASE_CONFIG_FILE}"



