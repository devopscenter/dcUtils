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
#  ORGANIZATION: devops.center
#       CREATED: 01/25/2017 16:54:43
#      REVISION:  ---
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
    echo -e "    if it exists in the .dcConfig/basedirectory"
    echo
}

#-------------------------------------------------------------------------------
# Make sure there are the exact number of arguments
#-------------------------------------------------------------------------------
if [[ $# -ne 2 ]]; then
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
             NEW_WORKSPACE_NAME=$1
             ;;
      * )    usage
             exit 1
    esac
    shift
done

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
