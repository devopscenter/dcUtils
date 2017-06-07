#!/usr/bin/env bash
#===============================================================================
#
#          FILE: setupDataload.sh
# 
#         USAGE: ./setupDataload.sh 
# 
#   DESCRIPTION: This script will take a directory as an argument and setup that
#                directory to be used for a database backup download and restore
#                point.  This means it will create a link between the download.sh
#                and restore.sh in the dcUtils/db directory to that new directory
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 06/06/2017 17:17:08
#      REVISION:  ---
#===============================================================================

#set -o nounset                              # Treat unset variables as an error
#set -x

dcUTILS=$(pwd)
SETTINGS_FILE="$HOME/.dcConfig/settings"

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
usage ()
{
    echo -e "Usage: setupDataload.sh -n new_dataload_directory"
    echo
    echo "This script will take a directory as an argument and setup that"
    echo "directory to be used for a database backup download and restore"
    echo "point.  This means it will create a link between the download.sh"
    echo "and restore.sh in the dcUtils/db directory to that new directory"
    echo

    if [[ -f $HOME/.dcConfig/settings ]]; then
        CUR_DATA_LOAD_DIR=$( grep "DATALOAD_DIR=" ${SETTINGS_FILE})
        echo "Current dataload direcotry is set to:"
        echo "${CUR_DATA_LOAD_DIR}"
    else
        echo "You have not identified a dataload directory yet. Run this script"
        echo "again and provide the option -n with a directory name"
    fi
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
while [[ $# -gt 0 ]]; do
    case ${1} in
      "-n" )   shift
             DATALOAD_DIR=$1
             ;;
      * )    usage
             exit 1
    esac
    shift
done

if [[ ! -d ${DATALOAD_DIR} ]]; then
    mkdir ${DATALOAD_DIR}
fi

#-------------------------------------------------------------------------------
# make the necessary symbolic links between the scripts and the new directory
#-------------------------------------------------------------------------------
if [[ ! -f ${DATALOAD_DIR}/download.sh ]] ; then
    ln -s ${dcUTILS}/db/download.sh ${DATALOAD_DIR}/
fi

if [[ ! -f ${DATALOAD_DIR}/restore.sh ]]; then
    ln -s ${dcUTILS}/db/restore.sh ${DATALOAD_DIR}/
fi

#-------------------------------------------------------------------------------
# Make note of the dataload directory in the ~/.dcConfig/settings
#-------------------------------------------------------------------------------
if [[ ! -f ${SETTINGS_FILE} ]]; then
    echo "DATALOAD_DIR=${DATALOAD_DIR}" > ${SETTINGS_FILE}
else
    # need to escape out all the backslashes in the path
    DATALOAD_DIR="${DATALOAD_DIR//\//\\/}"
    sed -i -e "s/DATALOAD_DIR=.*/DATALOAD_DIR=${DATALOAD_DIR}/" "${SETTINGS_FILE}"
fi

