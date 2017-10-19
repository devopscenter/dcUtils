#!/usr/bin/env bash
#===============================================================================
#
#          FILE: stop.sh
#
#         USAGE: ./reset-dc-containers.sh
#
#   DESCRIPTION:  Stops the containers that were started with docker-compose
#                 and remove the containers.  Or if --hard is given will remove
#                 everything, ie start from scratch.

#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/17/2016 16:27:42
#      REVISION:  ---
#===============================================================================

#set -o nounset                              # Treat unset variables as an error
#set -o errexit      # exit immediately if command exits with a non-zero status
#set -x              # essentially debug mode

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: reset-dc-containers.sh --appName appName [--debug] [--removeAll] "
    echo
    echo -e "This script will stop the docker containers found running that are"
    echo -e "specific to the application and no others.  The containers will be "
    echo -e "stopped and the containers removed. A pull of dcUtils will be done"
    echo -e "to ensure things are up to date.  Also, if the --removeAll is given"
    echo -e "then it will also remove the images and volumes"
    echo 
    echo -e "--appName|-a is the name of the application that you want to"
    echo -e "      stop as the default app for the current session. This is "
    echo -e "      optional if you only have one application defined."
    echo -e "--debug will use the web-debug configuration rather than the normal web one"
    echo -e "--removeAll - remove everything associated with the app to give"
    echo -e "      a clean slate to begin with."
    echo
    exit 1
}

#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' ]] || [[ $1 == '--help' ]]; then
    usage
    exit 1
fi

NEW=${@}

envToSource="$(${dcUTILS}/scripts/process_dc_env.py ${NEW})"

if [[ $? -ne 0 ]]; then
    echo $envToSource
    exit 1
else
    eval "$envToSource"
fi

DEBUG=0
REMOVE_ALL=0
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug|-d )
            DEBUG=1
            ;;
        --removeAll ) shift;
            REMOVE_ALL=1
            ;;
    esac
    shift
done

if [[ -z ${dcDEFAULT_APP_NAME} ]]; then
    echo "ERROR: the app name needs to be provided with the -a option"
    exit 1
fi

#-------------------------------------------------------------------------------
# Draw attention to the appName that is being used by this session!!
#-------------------------------------------------------------------------------
dcStartLog "Removing and reseting docker containers for application: ${dcDEFAULT_APP_NAME}"

dcLog "Stopping the running containers for the app"

CMD_TO_RUN="stop-dc-containers.sh -a ${dcDEFAULT_APP_NAME} --cleanup "

if [[ ${DEBUG} -eq 1 ]]; then
    CMD_TO_RUN="${CMD_TO_RUN} --debug "
fi

${CMD_TO_RUN}
#if [[ ${dcDEFAULT_APP_NAME} ]]; then
#    if [[ ${DEBUG} ]]; then
#        stop-dc-containers.sh -a ${dcDEFAULT_APP_NAME} --cleanup
#    else
#        stop-dc-containers.sh -a ${dcDEFAULT_APP_NAME} --debug --cleanup
#    fi
#else
#    if [[ ${DEBUG} ]]; then
#        stop-dc-containers.sh  --cleanup
#    else
#        stop-dc-containers.sh  --debug --cleanup
#    fi
#fi

dcLog "Updating dcUtils"
cd ${dcUTILS}
git pull origin

dcLog "Removing stopped containers"
docker rm $(docker ps -aqf "name=${dcDEFAULT_APP_NAME}-local-")

if [[ ${REMOVE_ALL} -eq 1 ]]; then
    echo "You are about to remove the image and the volumes which will remove all data (ie, database will be gone)"
    read -i "n" -p "Are you sure you want to do do this: (y or n) " -e wantToRemoveAll
    if [[ ${wantToRemoveAll} == "y" ]]; then
        echo "When removing everything, if there are still references from other containers then an error message will be dispayed and you would have to manually clear them before the images and volumes can be removed."
        dcLog "Removing images"
        echo $dcSTACK_VERSION
        docker rmi $(docker images -q devopscenter/*:${dcSTACK_VERSION})
        dcLog "Removing volumes"
        docker volume prune
    else
        echo "not removed."
        exit 2
    fi
 
fi


dcEndLog "Finished..."
