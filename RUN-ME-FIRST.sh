#!/usr/bin/env bash
#===============================================================================
#
#          FILE: run_me_first.sh
# 
#         USAGE: ./run_me_first.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 07/18/2017 15:17:42
#      REVISION:  ---
#===============================================================================

set -o nounset             # Treat unset variables as an error
#set -x                     # essentially debug mode
unset CDPATH

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  getBasePath
#   DESCRIPTION:  gets the path where this file is executed from...somewhere alone the $PATH
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
getBasePath()
{
    SOURCE="${BASH_SOURCE[0]}"
    while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
      DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
      SOURCE="$(readlink "$SOURCE")"
      [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
    done
    BASE_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  setupIAMUser
#   DESCRIPTION:  creates the IAM user under a specific group which defines the rolse
#                 for this user.  
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
setupIAMUser()
{
    echo "in setupIAMUser"
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  runAWSConfigure
#   DESCRIPTION:  runs the aws configure --profile command with the appropriate informaitno
#                 this constitutes running several aws configure set commands with the required data
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
runAWSConfigure()
{
    echo "in runAWSConfigure"
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  createUserSpecificKeys
#   DESCRIPTION:  creates the private/public keys that will have the public key
#                 sent to devops.center to deploy to the appropriate customer instances
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
createUserSpecificKeys()
{
    echo "in createUserSpecificKeys"
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  sendKeysTodc
#   DESCRIPTION:  sends the public key to devops.center,whom will distribute to the 
#                 customer instances
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
sendKeysTodc()
{
    echo "in sendKeysTodc"
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  getMyIP
#   DESCRIPTION:  sends a request to the devops server requesting to get the IP
#                 of this machine as it will be seen by the instances which are 
#                 outside of the local network.
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
getMyIP()
{
    echo "in getMyIP"
}


#-----  End of Function definittion  -------------------------------------------

# get BASE_DIR from getMyPath
getBasePath

#-------------------------------------------------------------------------------
# set up $HOME/.dcConfig 
#-------------------------------------------------------------------------------

if [[ ! -d $HOME/.dcConfig ]]; then
    mkdir $HOME/.dcConfig
fi


#-------------------------------------------------------------------------------
# need to check what version of bash they have on their machine
# if their machine is OSX they will need to use homebrew to install the lastest bash
# if not on OSX and the version is less then 4, then tell them they need to update bash
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# get some details to go into settings:
#     customer name
#     user name
#     region
#     base directory for application development
#     dcUtils path
#     ??? I don't think so...directory path to common shared directory ... if there is one
#     
#-------------------------------------------------------------------------------
echo "First you will be asked to enter your company name.  This will be used"
echo "as the value for the AWS profile and should be the same for everyone "
echo "within the company.  All lowercase."
echo 
read -p "Enter your customer name and press [ENTER]:"  customerName
if [[ -z ${customerName} ]]; then
    echo "Entering the customer name is required, exiting..."
    exit 1
fi
CUSTOMER_NAME=${customerName,,}

echo 
echo "Next enter your username, one word and no spaces all lowercase.  This value"
echo "will be used to create an IAM user specifically for you."
echo 
read -p "Enter your user name and press [ENTER]: " userName
if [[ -z ${userName} ]]; then
    echo "Entering the user name is required, exiting..."
    exit 1
fi
USER_NAME=${userName,,}

echo 
echo "Next enter the region that the AWS instances will be in when they are created."
echo "This value can be obtained from the main authenticatin user if it is not known."
echo "the value is typically us-west-2 or us-east-1."
echo 
read -i us-west-2  -p "Enter the region and press [ENTER]: " -e region
if [[ -z ${region} ]]; then
    REGION=us-west-2
else
    REGION=${region,,}
fi

echo 
echo "Next enter the directory name that will serve as the basis for you application development"
echo "that the AWS instances will be in when they are created. The devops.center scripts will use"
echo "this directory to put the application development files and the application website."
echo "This can be anywhere within your local machine and named anything you would like.  A suggestion"
echo "might be to put it in your home directory and call it devops: ~/devops/apps"
echo 
read -i "~/devops/apps" -p "Enter the directory and press [ENTER]: "  -e localDevBaseDir
if [[ -z ${localDevBaseDir} ]]; then
    echo "Entering the local development directory is required, exiting..."
    exit 1
fi
DEV_BASE_DIR=${localDevBaseDir}


echo "exporting dcUTILS=${BASE_DIR}"
echo "CUSTOMER_NAME=${CUSTOMER_NAME}"
echo "USER_NAME=${USER_NAME}"
echo "REGION=${REGION}"
echo "DEV_BASE_DIR=${DEV_BASE_DIR}"

#-------------------------------------------------------------------------------
# need to help them run through setting up the IAM user for this user and use 
# the AccessKey and SecretKey that is created specifically for this user to be 
# used in the aws configure setup. 
#-------------------------------------------------------------------------------
setupIAMUser

#-------------------------------------------------------------------------------
# run aws configure with the appropriate information gathered so far
#-------------------------------------------------------------------------------
runAWSConfigure


#-------------------------------------------------------------------------------
# create the personal private access key to authenticate ssh to an instance 
# ... put it in the .ssh/devops.center directory or the ~/.dcConfig/ directory
#-------------------------------------------------------------------------------
createUserSpecificKeys

#-------------------------------------------------------------------------------
# and make the shared key available to devops.center 
#-------------------------------------------------------------------------------
sendKeysTodc


#-------------------------------------------------------------------------------
# need to get the IP of this machine running.  Send a request to the devops.center
# server to the function that will return the IP this machine has.  This is done
# because it could be that this machine is NATted and the real IP is only gotten
# by leaving the local network.
#-------------------------------------------------------------------------------
getMyIP

#-------------------------------------------------------------------------------
# tell the user to add path to dcUtils to the $PATH
#-------------------------------------------------------------------------------
echo
echo "You will need to add the directory for dcUtils (${BASE_DIR}) to your PATH variable"
echo "and export it.  This would go into your shell rc file where the specific rc file is"
echo "what you run when interacting with the the terminal"
echo 

