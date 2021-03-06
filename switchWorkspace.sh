#!/usr/bin/env bash
#===============================================================================
#
#          FILE: switchWorkspace.sh
#
#         USAGE: ./switchWorkspace.sh newWorkspaceName
#
#   DESCRIPTION: This script will switch the workspace to the new workspacename
#                if it exists in the .dcConfig/basedirectory
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 01/25/2017 16:54:43
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
usage ()
{
    echo -e "Usage: switchWorkspace.sh -n newWorkspaceName"
    echo
    echo -e "This script will switch the workspace to the new workspacename"
    echo -e "    if it exists in the $HOME/.dcConfig/baseDirectory"
    echo -e "NOTE: use 'default' if the workspace is unknown.  This can be "
    echo -e "    checked by looking at the $HOME/.dcConfig/baseDirectory file"
    echo
    CURRENT=$(grep "CURRENT_WORKSPACE=" ${HOME}/.dcConfig/baseDirectory)
    echo -e "Current workspace is: ${CURRENT#CURRENT_WORKSPACE=}"
    echo
    echo -e "Possible workspaces (NOTE: will be lowercased which may not exactly match the name):"
    grep "_BASE_CUSTOMER_DIR=" ~/.dcConfig/baseDirectory | while read line
    do
        # get the keyword on the left side of the equal sign
        worksspaceLeftSide=${line%=*}
        # remove off the backend part
        workspaceAlmost=${worksspaceLeftSide/%_BASE_CUSTOMER_DIR/}
        workspaceName=${workspaceAlmost/_/}
        echo "${workspaceName,,}"
    done
    echo

}

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
NEW_WORKSPACE_NAME=""

while [[ $# -gt 0 ]]; do
    case ${1} in
      "-n" )   shift
             A_WORKSPACE_NAME=$1
             ;;
      * )    usage
             exit 1
    esac
    shift
done

# make sure it is uppercase
NEW_WORKSPACE_NAME=$(echo "${A_WORKSPACE_NAME}" | tr "[a-z]" "[A-Z]")
#echo ${NEW_WORKSPACE_NAME}

#-------------------------------------------------------------------------------
# check for the existance of the devops.center config (.dcConfig) directory in
# the users home directory. Also, check for the baseDirectory file
#-------------------------------------------------------------------------------
if [[ ! -d ${HOME}/.dcConfig ]]; then
    echo "The .dcConfig directory doesn't exist.  Have you run manageApp.py first?"
    exit 1
fi

CONFIG_FILE="${HOME}/.dcConfig/baseDirectory"

if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "The ${CONFIG_FILE} file doesn't exist.  Have you run manageApp.py first?"
    exit 1
fi

#-------------------------------------------------------------------------------
#  search through the .dcConfig for the new workspacename.  if it's not found
#  than need to throw an error and exit
#-------------------------------------------------------------------------------
FILE_EXISTS=$(cat "${CONFIG_FILE}" | grep "^_${NEW_WORKSPACE_NAME}")
if [[ -z ${FILE_EXISTS} ]] ; then
    echo "The new worksspace name: ${NEW_WORKSPACE_NAME} does not exists in ${CONFIG_FILE}"
    echo "You will need to run manageApp.py with the --workspaceName to provide a unique name for the "
    echo "workspace when creating the application, before you can utilize this script to change workspaces."
    exit 1
fi

#-------------------------------------------------------------------------------
# change the CURRENT_WORKSPACE to be equal to the NEW_WORKSPACE_NAME
#-------------------------------------------------------------------------------
sed -i -e "s/CURRENT_WORKSPACE=.*/CURRENT_WORKSPACE=${NEW_WORKSPACE_NAME}/" "${CONFIG_FILE}"


#-------------------------------------------------------------------------------
# Since they are using workspaces there a couple other places that will need to be changed in the ~/.dcConfig/settings
#-------------------------------------------------------------------------------
newCustomerName=${FILE_EXISTS##*/}
sed -i -e "s/CUSTOMER_NAME=.*/CUSTOMER_NAME=${newCustomerName,,}/" ~/.dcConfig/settings
sed -i -e "s/PROFILE=.*/PROFILE=${newCustomerName,,}/" ~/.dcConfig/settings
sed -i -e "s/CURRENT_WORKSPACE=.*/CURRENT_WORKSPACE=${newCustomerName,,}/" ~/.dcConfig/settings
if [[ $(grep -c "dcCOMMON_SHARED_DIR=\"" ~/.dcConfig/settings) -eq 0 ]]; then
    # and this one is for when there are no quotes
    sed -i -e "/dcCOMMON_SHARED_DIR/s/=\(.*\/\).*/=\1${newCustomerName,,}/" ~/.dcConfig/settings
else
    # this one is if there are quotes around the directory
    sed -i -e "/dcCOMMON_SHARED_DIR/s/=\"\(.*\/\).*\"/=\"\1${newCustomerName,,}\"/" ~/.dcConfig/settings
fi
