#!/bin/bash - 
#===============================================================================
#
#          FILE: updateAppOnComponent.sh
# 
#         USAGE: ./updateAppOnComponent.sh 
# 
#   DESCRIPTION: 
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

getUpdate()
{
    eval `ssh-agent`
    ssh-add ~/.ssh/${DEPLOYKEY}
    mkdir ~/${CUST_APP_NAME}
    cd ~/${CUST_APP_NAME} && git clone ${CUSTOMER_UTILS}

    # and change to the desired branch if set
    if [[ ${CUSTUTILSGITBRANCH} != 'master' ]]; then
        cd ~/${CUST_APP_NAME}/${CUST_APP_NAME}-utils && git checkout ${CUSTOMER_UTILS}
    fi
}
