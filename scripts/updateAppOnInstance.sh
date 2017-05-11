#!/usr/bin/env bash
#===============================================================================
#
#          FILE: updateAppOnComponent.sh
#
#         USAGE: ./updateAppOnComponent.sh
#
#   DESCRIPTION: This script will be run on an instance and will do an update
#                on the application (given on the command line) utiliies and
#                then run deployenv.sh on the instance.
#
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 03/22/2017 10:59:15
#      REVISION:  ---
#===============================================================================

#set -o nounset          # Treat unset variables as an error
#set -o errexit          # exit immediately if a command exits unsuccessfully
set -x                   # essentially debug mode

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: deployenv.sh --env ENVIRONMENT --appName CUSTOMER_APP_NAME --branch GIT_BRANCH"
    echo -e "                    --deployKey DEPLOYKEY"
    echo
    echo -e "--env is one of the environments that is being targeted to execute,"
    echo -e "and corresponds to which environment variable file will be used. "
    echo -e "It is one of: local|dev|staging|prod"
    echo
    echo -e "--appName is the application name that you wish to configure the "
    echo -e "environment for"
    echo
    echo -e "--branch is the application branch name that you want to use to update"
    echo
    echo -e "--deployKey is the access key that the instance will use to access the"
    echo -e "repository for the appication utilities to pull from"
    echo
}



#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  getUpdate
#   DESCRIPTION:  moves the tarball over to the host and extract it.  Then removes
#                 all but the env keys directory (no reason to have those).  And 
#                 finally run deployenv.sh on the instance
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
doTheUpdate() {

    #-------------------------------------------------------------------------------
    # the local tarbal isn't needed any more so go ahead and remove it
    #-------------------------------------------------------------------------------

    cd $HOME
    echo ${CUST_APP_NAME}
    echo "${HOME}"'/'"${APP_UTILS_TARBALL}"

    echo ${INSTANCE_ID}
    echo ${ENVIRONMENT}
    # make the base directory
    if [[ ! -d ${CUST_APP_NAME} ]]; then
        mkdir ${CUST_APP_NAME}
    fi

    # untar the ball
    cd ${CUST_APP_NAME}
    #tar -xf "${HOME}/${APP_UTILS_TARBALL}"
#
#    # and clean up
#    cd $HOME
#    rm ${APP_UTILS_TARBALL}
#
#    # need to clean out the other env "key" directories except the one that is needed for
#    # this instance
#    cd "${HOME}/${CUST_APP_NAME}/${CUSTOMER_UTILS}/keys"
#    RM_ALL_ENV_DIRS_BUT_ONE=$(find . ! -name "${ENVIRONMENT}" -type d -exec rm -rf {} +)
#
#    # and now do the deployenv.sh
#    cd ${HOME}/dcUtils
#    ./deployenv.sh --type instance --env $ENVIRONMENT --appName ${CUST_APP_NAME}

}

#-------------------------------------------------------------------------------
# Loop through the arguments and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' ]]; then
    usage
    exit 1
fi

# set sane defaults
GIT_BRANCH=""
DEPLOYKEY=""

# now handle the arguemnts for this script
while [[ $# -gt 0 ]]; do
    case $1 in
      --branch )        shift
                        GIT_BRANCH=$1
                  ;;
      --deployKey )     shift
                        DEPLOYKEY=$1
                  ;;
      --appName|-a )    shift
                        CUST_APP_NAME=$1
                  ;;
      --env|-e )        shift
                        ENVIRONMENT=$1
                  ;;
      --instanceID|-i )        shift
                        INSTANCE_ID=$1
                  ;;
      --updateTarBall|-g )        shift
                        APP_UTILS_TARBALL=$1
                  ;;
    esac
    shift
done


doTheUpdate

