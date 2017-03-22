#!/bin/bash -
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
#   DESCRIPTION:  the function to actually do the update
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
getUpdate()
{
    # from the notes
    # - ssh into the instance
    # - eval `ssh-agent`
    # - ssh-add the deploy-key (may have to get this from the command line and
    #      it needs to be in ~/.ssh)
    # - cd app/app-utils
    # - git pull origin
    #  - cd ~/dcUtils
    # - ./deployenv.sh --type instance --env $ENV --appName ${CUST_APP_NAME}
    # - logout to ensure it takes effect (ie, it may be exported by
    #      deployenv.sh which would negate the need to logout and logon)

    CUSTOMER_UTILS="${CUST_APP_NAME}-utils"

    # set up ssh  for this session
    eval `ssh-agent`
    ssh-add ~/.ssh/${DEPLOYKEY}

    if [[ ! -d  ${CUST_APP_NAME} ]]; then
        echo "ERROR: directory does not exist: ${CUST_APP_NAME}"
        echo "       Has the code been deployed to the instance"
        echo "       or is the name of the application incorrect?"
        exit 1
    else
        if [[ ! -d "${CUST_APP_NAME}/${CUSTOMER_UTILS}" ]]; then
            echo "ERROR: directory does not exist: ${CUST_APP_NAME}/${CUSTOMER_UTILS}"
            echo "       Has the code been deployed to the instance or is the name "
            echo "       of the application utilities directory incorrect?"
            exit 1
        else
            # finally do the work
            cd "~/${CUST_APP_NAME}/${CUSTOMER_UTILS}"

            if [[ ${GIT_BRANCH} ]]; then
                git checkout ${GIT_BRANCH}
            fi

            # pull from the remote on this branch
            git pull origin

            # and now do the deployenv.sh
            cd ~/dcUtils
            ./deployenv.sh --type instance --env $ENVIRONMENT --appName ${CUST_APP_NAME}
        fi
    fi
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
    esac
    shift
done

if [[ -z ${CUST_APP_NAME


getUpdate

