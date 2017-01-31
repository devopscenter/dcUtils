#!/usr/bin/env bash
#===============================================================================
#
#          FILE: main.sh
#
#         USAGE: ./main.sh
#
#   DESCRIPTION:
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 01/26/2017 10:51:37
#      REVISION:  ---
#===============================================================================

#set -o nounset                              # Treat unset variables as an error
#set -e
set -x

# NOT USUAL to call the initialCreate from a shell script.  It was really meant
# to be used with manageApp.py as it creates the things that process_dc_env 
# reads
NEW=${@}" --initialCreate"
# normal call ..the way it is meant to be for all shell scripts ...hopefully
#NEW=${@}

envToSource=$(./process_dc_env.py ${NEW})

if [[ $? -ne 0 ]]; then
    echo $envToSource
else
    eval $envToSource
fi

#env
#echo ${CUSTOMER_APP_NAME}

