#!/usr/bin/env bash
#===============================================================================
#
#          FILE: run_me_first.sh
# 
#         USAGE: ./run_me_first.sh 
# 
#   DESCRIPTION: This script will be used by the customer's users and will be executed
#                from a shared drive.  
#                The steps that the script will do is:
#                   - check for and install bash version 4
#                   - check for and install aws cli
#                   - check for and install jq
#                   - ask where they want dcUtils
#                   - create the directory if it doesn't exists
#                   - cd to that directory 
#                   - clone dcUtils
#                   - then 
#           
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

#set -o nounset             # Treat unset variables as an error
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
    echo "Setting up this user as an IAM user"

	IAMUserToCreate=${USER_NAME}
    if [[ $(aws --profile "default" --region ${REGION} iam get-user --user-name ${IAMUserToCreate} 2>&1 > /dev/null) == *"cannot be found"* ]]; then
        sleep 2
        aws --profile "default" --region ${REGION} iam create-user --user-name  ${IAMUserToCreate}
        sleep 2

        # create the keys for the user
        accessKeys=$(aws --profile "default" --region ${REGION} iam create-access-key --user-name  ${IAMUserToCreate})
        SECRET_ACCESS_KEY=$(jq -r '.AccessKey.SecretAccessKey' <<< "$accessKeys")
        ACCESS_KEY=$(jq -r '.AccessKey.AccessKeyId' <<< "$accessKeys")
        sleep 2

		# The group name that was set up at customer registration time.  There should be a group that would
        # be named CUSTOMER_NAME-dev and the policy for the group is to have EC2 and S3 full read/write access
        # but not admin priviledge.  That is left to the authenticated user(s)
		IAMUserGroup="${CUSTOMER_NAME}-dev"
        
        # add the login to a group so that the policy can be attached to the group rather
        # than the user
        aws --profile "default" --region ${REGION} iam add-user-to-group --user-name ${IAMUserToCreate} --group-name ${IAMUserGroup}
        sleep 2
    fi
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
    echo "Setting up this users AWS configuration"

    aws configure set aws_access_key_id ${ACCESS_KEY} --profile ${PROFILE}
    sleep 2
    aws configure set aws_secret_access_key ${SECRET_ACCESS_KEY} --profile ${PROFILE}
    sleep 2
    aws configure set region ${REGION} --profile ${PROFILE}
    sleep 2
    aws configure set output json --profile ${PROFILE}
    sleep 2
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


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  writeToSettings
#   DESCRIPTION:  this function will write the necessary key/value pairs out to
#                 ~/dcConfig/settings
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
writeToSettings()
{
    echo "dcUTILS=${dcUTILS}" > ~/.dcConfig/settings
    echo "CUSTOMER_NAME=${CUSTOMER_NAME}" >> ~/.dcConfig/settings
    echo "PROFILE=${PROFILE}" >> ~/.dcConfig/settings
    echo "USER_NAME=${USER_NAME}" >> ~/.dcConfig/settings
    echo "REGION=${REGION}" >> ~/.dcConfig/settings
    echo "DEV_BASE_DIR=${DEV_BASE_DIR}" >> ~/.dcConfig/settings
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
OSNAME=$(uname -s)

BV=$(/usr/bin/env bash -c 'echo $BASH_VERSION')
if [[ $BV != "4"* ]]; then
    if [[ ${OSNAME} == "Linux" ]]; then
        echo "The devops.center scripts all run with Bash version 4+.  It doesn't have"
        echo "to be the shell that you use, but the scripts will look specifically for bash."
        echo "You will need to update your version of bash to the major revison 4.  The"
        echo "devops.center scripts work with the latest bash version 4."
        exit 1
    elif [[ ${OSNAME} == "Darwin" ]]; then
        echo "The devops.center scripts all run with Bash version 4+.  It doesn't have"
        echo "to be the shell that you use, but the scripts will look specifically for bash."
        echo "You will need to update your version of bash to the major revison 4.  The"
        echo "devops.center scripts work with the latest bash version 4."
        echo "For OSX it is suggested to get bash via Homebrew and then make sure that the"
        echo "path to the installation of bash is first on your PATH environment variable."
        exit 1
    else
        echo "Please report the name of the OS that you are running to devops.center. "
        echo "This is accomplished echo by running the command 'uname -s' on the command line."
        exit 1
    fi
fi

#-------------------------------------------------------------------------------
# need to check to see if aws and jq have been loaded and if not install them
#-------------------------------------------------------------------------------
CHECK_AWS=$(which aws)
if [[ ! ${CHECK_AWS} ]]; then
    echo 
    echo "The devops.center scripts will use the aws cli commands to access AWS."
    echo "The command 'aws' does not appear to be installed on your machine."
    echo "Please use your normal installation method for installing new"
    echo "software to install the command 'aws'."
    echo 
    exit 1
fi

CHECK_JQ=$(which jq)
if [[ ! ${CHECK_JQ} ]]; then
    echo 
    echo "The devops.center scripts will use the aws cli commands to access AWS"
    echo "and then the jq command (jq is a json output interpreter) to cull"
    echo "additional information from the results that come from the aws command."
    echo "The command 'jq' does not appear to be installed on your machine."
    echo "Please use your normal installation method for intalling new"
    echo "software to install the command 'jq'."
    echo 
    exit 1
fi



#-------------------------------------------------------------------------------
# clone dcUtils where the user wants it
#-------------------------------------------------------------------------------
set -x
echo 
echo "First we need to grab a clone of the devops.center utilitities: dcUtils"
echo "And for that, we need a directory location on your machine.  It can go"
echo "anywhere.  Once this is cloned the path to the dcUtils directory will"
echo "need to go into your PATH variable and then exported."
echo 
read -p "Enter your directory location and press [ENTER]: "  aBaseDir
if [[ ${aBaseDir} == "~"* || ${aBaseDir} == "\$HOME"* ]]; then
    homePath=$(echo $HOME)
    partialBaseDir=${aBaseDir#*/}
    dcUtilsBaseDir="${homePath}/${partialBaseDir}"
else
    dcUtilsBaseDir=${aBaseDir}
fi

if [[ ! -d ${dcUtilsBaseDir} ]]; then
    echo "That directory ${dcUtilsBaseDir} doesn't exists"
    read -i "y" -p "Do you want it created [y or n]: " -e createdReply
    if [[ ${createdReply} == "y" ]]; then
        mkdir -p ${dcUtilsBaseDir}
    else
        echo "not created."
        exit 1
    fi
fi

cd ${dcUtilsBaseDir}
echo "cloning dcUtils in directory: ${dcUtilsBaseDir}"
git clone https://github.com/devopscenter/dcUtils.git
dcUTILS=${dcUtilsBaseDir}/dcUtils

#-------------------------------------------------------------------------------
# now we need to get the bootstrap aws config and credentials
#-------------------------------------------------------------------------------

exit

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
echo 
echo "Next, you will be asked to enter your company name.  This will be used"
echo "as the value for the AWS profile and should be the same for everyone "
echo "within the company.  One word and not spaces all lowercase letters."
echo 
read -p "Enter your customer name and press [ENTER]: "  customerName
if [[ -z ${customerName} ]]; then
    echo "Entering the customer name is required, exiting..."
    exit 1
fi

CUSTOMER_NAME=${customerName,,}
PROFILE=${CUSTOMER_NAME}

echo 
echo "Enter your username, one word and no spaces all lowercase letters."
echo "This value will be used to create an IAM user specifically for you."
echo 
read -p "Enter your user name and press [ENTER]: " userName
if [[ -z ${userName} ]]; then
    echo "Entering the user name is required, exiting..."
    exit 1
fi
USER_NAME=${userName,,}

echo 
echo "Enter the region that the AWS instances will be in when they are created."
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
echo  "Enter the directory name that will serve as the basis for you application development"
echo  "that the AWS instances will be in when they are created. The devops.center scripts will use"
echo  "this directory to put the application development files and the application website."
echo  "This can be anywhere within your local machine and named anything you would like.  A suggestion"
echo  "might be to put it in your home directory and call it devops: ~/devops/apps"
echo  
read -i "~/devops/apps" -p "Enter the directory and press [ENTER]: "  -e localDevBaseDir
if [[ -z ${localDevBaseDir} ]]; then
    echo "Entering the local development directory is required, exiting..."
    exit 1
fi
DEV_BASE_DIR=${localDevBaseDir}


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
# we have collected all the information we need now write it out to .dcConfig/settings
#-------------------------------------------------------------------------------
writeToSettings

#-------------------------------------------------------------------------------
# tell the user to add path to dcUtils to the $PATH
#-------------------------------------------------------------------------------
echo
echo "**NOTE**"
echo "You will need to add the directory for dcUtils (${dcUTILS}) to your PATH variable"
echo "and export it.  This would go into your shell rc file where the specific rc file is"
echo "dependent on what shell (ie bash, zsh, csh,...) you run when interacting with the the terminal"
echo
