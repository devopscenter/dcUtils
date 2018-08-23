#!/usr/bin/env bash
#===============================================================================
#
#          FILE: addWorkspace.sh
#
#         USAGE: ./addWorkspace.sh
#
#   DESCRIPTION: This script will add a new separation between applications by
#                adding a new workspace.  This way additional applicaiotns can
#                be associated with this workspace and they are separate from
#                other applications in other workspaces.
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Bob Lozano - bob@devops.center
#                Gregg Jensen - gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 08/23/2018 10:50:48
#      REVISION:  ---
#
# Copyright 2014-2018 devops.center llc
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
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
usage ()
{
    echo -e "Usage: addWorkspace.sh -n newWorkspaceName -d destinationDirectory"
    echo
    echo -e "This script will add a workspace that you can use to separate an"
    echo -e "application from other applications.  This will create a parent"
    echo -e "directory that applications that will be associated with this workspace"
    echo -e "will be placed."
    echo -e "Note: this creates/adds to the baseDirectory file located in ~/.dcConfig"
    echo
    echo -e "Required arguments:"
    echo -e "-n  This is the name of the new workspace that you want to add"
    echo -e "    NOTE: do not put spaces in the name."
    echo -e "-d  [OPTIONAL] This is the base directory where the parent directory with "
    echo -e "    the name of the workspace will be created."
    echo -e "    If not given it will take the value of DEV_BASE_DIR from ~/.dcConfig/settings"

    echo
}


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
}       # ----------  end of function getValueFromSettings  ----------

#-------------------------------------------------------------------------------
# Make sure there are the exact number of arguments
#-------------------------------------------------------------------------------
if [[ $# -lt 2 ]]; then
    usage
    exit 1
fi

#-------------------------------------------------------------------------------
# Loop through the arguments and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
NEW_WORKSPACE_NAME=""

DEST_DIR=''
while [[ $# -gt 0 ]]; do
    case ${1} in
      "-n" )   shift
             A_WORKSPACE_NAME="${1}"
             ;;
      "-d" )   shift
             DEST_DIR="${1}"
             ;;
      * )    usage
             exit 1
    esac
    shift
done

if [[ "${A_WORKSPACE_NAME}" == *[[:space:]]* ]]; then
    echo "Error: The workspace name can not contains spaces: ${A_WORKSPACE_NAME}"
    exit 1
fi

if [[ ! ${DEST_DIR} ]]; then
    DEST_DIR=$(getValueFromSettings "DEV_BASE_DIR")
fi

echo "NOTE: adding workspace ${A_WORKSPACE_NAME} to ${DEST_DIR}"

# make sure the workspace nane is uppercase
WORKSPACE_NAME_UPPERCASE=${A_WORKSPACE_NAME^^}
#echo ${WORKSPACE_NAME_UPPERCASE}
#echo "${DEST_DIR}"

varToAdd="_${WORKSPACE_NAME_UPPERCASE}_BASE_CUSTOMER_DIR="
dirToAdd="${DEST_DIR}/${A_WORKSPACE_NAME}"
lineToAdd="${varToAdd}${dirToAdd}"
theFile=$HOME/.dcConfig/baseDirectory

# see if it exists maybe this is the first time 
if [[ ! -f "${theFile}" ]]; then
    # create it and make sure that this workspace is the current workspace
    echo "CURRENT_WORKSPACE=${WORKSPACE_NAME_UPPERCASE}" > "${theFile}"
    echo "##### WORKSPACES ######" >> "${theFile}"
    echo ${lineToAdd} >> "${theFile}"
    echo "##### BASE DIR CONSTRUCTION NO TOUCH ######" >> "${theFile}"
    echo 'CONSTRUCTED_BASE_DIR=_${CURRENT_WORKSPACE}_BASE_CUSTOMER_DIR' >> "${theFile}"
    echo 'BASE_CUSTOMER_DIR=${!CONSTRUCTED_BASE_DIR}' >> "${theFile}"
else
    # check to see if there is a value by that name already in the file
    if [[ ! $(grep -c ${varToAdd} ${theFile}) ]];then
        echo "A workspace with the same name exists: ${A_WORKSPACE_NAME}"
        exit 1
    fi
    
    # need to add a line into that file and we need to do it in a way that will
    # work for both linux and osx, since we can rely on the verion of sed they have
    cp "${theFile}" "${theFile}.ORIG"
    writeNewEntry="false"
    # we'll put all the new lines into a new file so we don't screw up the file 
    # we are reading
    while read aLine; do
        if [[ $aLine == "CURRENT_WORKSPACE"* ]]; then
            echo "CURRENT_WORKSPACE=${WORKSPACE_NAME_UPPERCASE}" > "${theFile}.NEW"
            continue
        fi
        if [[ ${aLine} == "##### WORKSPACES ####"* ]]; then
            writeNewEntry="true"
        fi 
        echo "${aLine}" >> $HOME/.dcConfig/baseDirectory.NEW
        if [[ ${writeNewEntry} == "true" ]]; then
            echo ${lineToAdd} >> "${theFile}.NEW"
            writeNewEntry="false"
        fi
    done < "${theFile}"
    # and now do some house cleaning
    mv "${theFile}.NEW" "${theFile}"
    rm "${theFile}.ORIG"
fi

# and finally make the new directory in the location specified
if [[ ! -d "${dirToAdd}" ]]; then
    mkdir -p "${dirToAdd}"
fi 
