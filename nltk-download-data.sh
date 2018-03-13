#!/usr/bin/env bash
#===============================================================================
#
#          FILE: nltk-download-data.sh
#
#         USAGE: ./nltk-download-data.sh
#
#   DESCRIPTION: Script to download the items found in the nltk.txt file
#                as defined by the user.
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Bob Lozano - bob@devops.center
#                Gregg Jensen - gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 02/23/2018 10:47:02
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
#   DESCRIPTION:  prints out the usage for this script
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
usage ()
{
    cat <<EOF
    Usage: nltk-download-data.sh [-f /path/to/nltk.txt]

    Option:
        -c /path/to/nltk.txt  This optional argument will allow the user to define
        the path and the name of the file that contains the list of items to be
        downloaded by the nltk.downlder.
        Default is to use the name nltk.txt and look in the current directory

EOF
}	# ----------  end of function usage  ----------


#-------------------------------------------------------------------------------
# check to see if they want help or if there is the optional filename and path
#-------------------------------------------------------------------------------
NLTK_TXT_FILE="./nltk.txt"
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h ) shift
                    usage
                    exit 1
                ;;
        --fileName|-f ) shift
                    NLTK_TXT_FILE=$1
                ;;
    esac
    shift
done

#-------------------------------------------------------------------------------
# This will read the nltk.txt file located in the /usr/share/nltk_data directory
# and do the necessary download using the nltk.downloader.  It will make the 
# appropriate changes where it needs to such that nltk will utilize it properly.
#-------------------------------------------------------------------------------
if [[ -f ${NLTK_TXT_FILE} ]]; then 
    mkdir -p /usr/share/nltk_data/
    cat ${NLTK_TXT_FILE} | while read -r line
        do 
            python -m nltk.downloader -d /usr/share/nltk_data ${line}
        done
else
    echo "NOTE: Can not find the nltk text file: ${NLTK_TXT_FILE}"
    echo "      Make sure the file is in this location and has this name and then run"
    echo "      this script again."
    exit 1
fi

