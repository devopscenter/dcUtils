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
#NEW=${@}" --initialCreate"

# normal call ..the way it is meant to be for all shell scripts ...hopefully
NEW=${@}

dcUTILS=".."

envToSource=$(${dcUTILS}/scripts/process_dc_env.py ${NEW})

if [[ $? -ne 0 ]]; then
    echo $envToSource
else
    eval $envToSource
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


#env
echo "CUSTOMER_APP_NAME = ${CUSTOMER_APP_NAME}"
echo "FOO = ${FOO}"
