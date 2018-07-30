#!/usr/bin/env bash
#===============================================================================
#
#          FILE: createIAMUser.sh
# 
#         USAGE: createIAMUser.sh
# 
#   DESCRIPTION: This script is used by the user/developers of the company
#                to create an initial setup for the user to access AWS. 
#                The script assumes that the dcBootstrap/RUN-ME-FIRST.sh 
#                as been run.
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 07/18/2017 15:17:42
#      REVISION:  ---
#
# Copyright 2014-2018 devops.center llc
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
#set -o errexit      # exit immediately if command exits with a non-zero status
#set -x             # essentially debug mode
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
#          NAME:  getValueFromSettings
#   DESCRIPTION:  will get the value of the key passed in from ~/.dcConfig/settings
#    PARAMETERS:  the key to look for
#       RETURNS:  the value of the key once it's found
#-------------------------------------------------------------------------------
getValueFromSettings()
{
    keyToFind=$1
    aKeyValue=$(grep "^${keyToFind}" ~/.dcConfig/settings)
    justTheValue=${aKeyValue#*=}
    # remove any double quotes around the value
    var1=${justTheValue#*\"}
    unquotedVar=${var1%\"}
    echo "${unquotedVar#*=}"
}       # ----------  end of function getValueFromSettings  ----------


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  determineProfile
#   DESCRIPTION:  will check to see if the .aws/config is on the default or a real-profile
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
determineProfile()
{
    aProfile=$(aws configure get region --profile ${PROFILE} 2>&1 > /dev/null)
    if [[ ${aProfile} == *"could not be found"* ]]; then
        anotherProfile=$(aws configure get region --profile default)
        if [[ ${anotherProfile} == "us-west-2" ]] || [[ ${anotherProfile} == "us-east-1" ]]; then
            INITIAL_PROFILE="default"
        fi
    else
        INITIAL_PROFILE=${PROFILE}
    fi
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  copyLoggingScript
#   DESCRIPTION:  copy dcUtils/script/dcEnv.sh to destination directory
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
copyLoggingScript()
{
    if [[ -w /usr/local/bin ]]; then
        cp ${dcUTILS}/scripts/dcEnv.sh /usr/local/bin/dcEnv.sh  > /dev/null 2>&1
    else
        echo 
        echo "We need to put a logging script in /usr/local/bin and it doesn't"
        echo "appear to be writable by you"
        read -i "y" -p "Do you want it use sudo to put it there [y or n]: " -e createdReply
        if [[ ${createdReply} == "y" ]]; then
            sudo cp ${dcUTILS}/scripts/dcEnv.sh /usr/local/bin/dcEnv.sh
        else
            echo
            echo "NOT COPIED. This script just standardizes output from the devops.center"
            echo "scripts. You can put it somewhere else in your path.  The file is: "
            echo "${dcUTILS}/scritps/dcEnv.sh"
            echo
        fi
    fi
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
    echo "Setting up the IAM user"

    # The group name that was set up at customer registration time.  There should be a group that would
    # be named CUSTOMER_NAME-dev and the policy for the group is to have EC2 and S3 full read/write access
    # but not admin priviledge.  That is left to the authenticated user(s)
    IAMUserGroup="${CUSTOMER_NAME}-dev"
        

	IAMUserToCreate=${USER_NAME}
    if [[ $(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam get-user --user-name ${IAMUserToCreate} 2>&1 > /dev/null) == *"cannot be found"* ]]; then
        sleep 2
        createUser=$(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam create-user --user-name  ${IAMUserToCreate} 2>&1 > /dev/null)
        sleep 2

        # create the keys for the user
        accessKeys=$(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam create-access-key --user-name  ${IAMUserToCreate})
        SECRET_ACCESS_KEY=$(jq -r '.AccessKey.SecretAccessKey' <<< "$accessKeys")
        ACCESS_KEY=$(jq -r '.AccessKey.AccessKeyId' <<< "$accessKeys")
        sleep 2

        # add the login to a group so that the policy can be attached to the group rather  than the user
        addToGroup=$(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam add-user-to-group --user-name ${IAMUserToCreate} --group-name ${IAMUserGroup} 2>&1 > /dev/null)
        sleep 2
    else
        # add the login to a group so that the policy can be attached to the group rather than the user
        addToGroup=$(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam add-user-to-group --user-name ${IAMUserToCreate} --group-name ${IAMUserGroup} 2>&1 > /dev/null)
        sleep 2

        # create the keys for the user
        accessKeys=$(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam create-access-key --user-name  ${IAMUserToCreate})
        SECRET_ACCESS_KEY=$(jq -r '.AccessKey.SecretAccessKey' <<< "$accessKeys")
        ACCESS_KEY=$(jq -r '.AccessKey.AccessKeyId' <<< "$accessKeys")
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
    echo "Setting up the AWS configuration"

    if [[ -z ${ACCESS_KEY} ]]; then
        echo
        echo "** NOTE **"
        echo "The keys could not be created so the .aws/credentials could not be updated"
        echo "This will have to be corrected manually before any additional devops.center"
        echo "scripts can be run."
        echo
    else
        aws configure set aws_access_key_id ${ACCESS_KEY} --profile ${PROFILE}
        sleep 2
        aws configure set aws_secret_access_key ${SECRET_ACCESS_KEY} --profile ${PROFILE}
        sleep 2
        aws configure set region ${REGION} --profile ${PROFILE}
        sleep 2
        aws configure set output json --profile ${PROFILE}
        sleep 2
    fi
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
    if [[ ! -d ~/.ssh/devops.center ]]; then
        mkdir -p ~/.ssh/devops.center
    fi

    # call the ssh-keygen to create a private/public set of keys
    echo "Creating ssh access keys (${USER_NAME}-access-key) to be used to access the AWS instances"
    ssh-keygen -t rsa -N "" -f ~/.ssh/devops.center/${USER_NAME}-access-key -q
    mv ~/.ssh/devops.center/${USER_NAME}-access-key ~/.ssh/devops.center/${USER_NAME}-access-key.pem
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
    # TODO: when creating the groups that will be used by the IAM users, need to create
    #       one that has the policies: IAMUserSSHKeys
    #       this group will be used for the script in this function to upload the ssh public
    #       keys to the IAM role
    #       PLACEHOLDER name for the group: public-key-transfer

    echo "And now we need to associate the public key with the new IAM user"
    echo
    # send the public key to the IAM user just created and devops.center will disseminate
    # it to the appropriate instances
    # add group public-key-tranfer to the IAM user
    aws --profile ${INITIAL_PROFILE} --region ${REGION} iam add-user-to-group --user-name ${USER_NAME} --group-name public-key-transfer 2>&1 > /dev/null
    sleep 2

    # upload the public key
    UPLOAD=$(aws --profile ${INITIAL_PROFILE} --region ${REGION} iam upload-ssh-public-key --user-name ${USER_NAME} --ssh-public-key-body "$(cat ~/.ssh/devops.center/${USER_NAME}-access-key.pub) 2>&1 > /dev/null")
    sleep 2

    # remove the group public-key-tranfer from the IAM user
    aws --profile ${INITIAL_PROFILE} --region ${REGION} iam remove-user-from-group --user-name ${USER_NAME} --group-name public-key-transfer 2>&1 > /dev/null
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  writeToSettings
#   DESCRIPTION:  This will update the REGION information in ~/.dcConfig/settings
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
writeToSettings()
{
    sed -i -e "s/^REGION=.*/REGION=${REGION}/" ~/.dcConfig/settings
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  cleanUpAWSConfigs
#   DESCRIPTION:  remove the bootstrap section from the .aws/{config|credentials}
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
cleanUpAWSConfigs()
{
    cd ~/.aws

    # do a diff and grab the lines that are different in the new one
    if [[ $(diff config.OLD config) ]]; then 
        echo "[profile ${PROFILE}]" > config.NEW
        diff config.OLD config | grep '^>' | sed 's/^>\ //' >> config.NEW
    else
        cp config config.NEW
    fi
    echo "[${PROFILE}]" > credentials.NEW
    diff credentials.OLD credentials | grep '^>' | sed 's/^>\ //' >> credentials.NEW

    #-------------------------------------------------------------------------------
    # make the NEW ones the ones to keep
    #-------------------------------------------------------------------------------
    mv config.NEW config
    mv credentials.NEW credentials

    #-------------------------------------------------------------------------------
    # and remove the OLD ones
    #-------------------------------------------------------------------------------
    rm config.OLD credentials.OLD

    if [[ ${ALREADY_HAS_AWS_CONFIGS} == "yes" ]]; then
        # they had an original config and credentials.  Append the new files to the 
        # original ones
        alreadyHasEntry=$(grep $PROFILE ~/.aws/config.ORIGINAL)
        if [[ -z ${alreadyHasEntry} ]]; then
            cat config >> config.ORIGINAL
            cat credentials >> credentials.ORIGINAL
        else
            # they already have a profile by this name so make a second one
            echo 
            echo "There was already an entry in the original .aws/config for the "
            echo "profile (${PROFILE} you are creating.  So, the entry will be marked"
            echo "as ${PROFILE}-2 and you might need to do some manual work to clean"
            echo "this up or work with the new name of the profile."

            sed -i "s/${PROFILE}/${PROFILE}-2/" config
            sed -i "s/${PROFILE}/${PROFILE}-2/" credentials

            # and append them to the original file
            cat config >> config.ORIGINAL
            cat credentials >> credentials.ORIGINAL
        fi

        # and move the original back to the only copy left in the .aws directory.
        mv config.ORIGINAL config
        mv credentials.ORIGINAL credentials
    fi
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  bootstrapAWSConfigs
#   DESCRIPTION:  
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
bootstrapAWSConfigs()
{
    ALREADY_HAS_AWS_CONFIGS="no"

    if [[ -f $HOME/.aws/credentials ]]; then
        # copy the original config and credentials so we don't bother them
        mv ~/.aws/config ~/.aws/config.ORIGINAL
        mv ~/.aws/credentials ~/.aws/credentials.ORIGINAL

        # set this to yes, meaning that they already had a config/credentials file so do NOT
        # clean it up
        ALREADY_HAS_AWS_CONFIGS="yes"
    fi

    if [[ -f "${dcCOMMON_SHARED_DIR}/bootstrap-aws.tar" ]]; then
        cd $HOME
        tar -xf "${dcCOMMON_SHARED_DIR}/bootstrap-aws.tar"
        cp ~/.aws/config ~/.aws/config.OLD
        cp ~/.aws/credentials ~/.aws/credentials.OLD
    else
        echo 
        echo "Could not find the bootstrap-aws tar ball which is required to begin"
        echo "this script.  Contact the devops.center representative to ensure that"
        echo "the file is created and put into the directory: ${dcCOMMON_SHARED_DIR}"
        echo
        exit 1
    fi

    #-------------------------------------------------------------------------------
    # NOTE: Don't forget to remove the bootstrap sections out of the config and credentials
    # when this script is done
    #-------------------------------------------------------------------------------
}


#-----  End of Function definition  -------------------------------------------

#-------------------------------------------------------------------------------
# first make sure they have run dcBootstrap/RUN-ME-FIRST.sh
#-------------------------------------------------------------------------------

if [[ ! -d $HOME/.dcConfig ]]; then
    echo "ERROR: It does not look like you have run the initial bootstrap script."
    echo "       Contact a devops.center engineer to learn how to correct this."
    exit 1
fi

#-------------------------------------------------------------------------------
# get some basic values that have already been set name from ~/.dcConfig/settings
#-------------------------------------------------------------------------------
CUSTOMER_NAME=$(getValueFromSettings "CUSTOMER_NAME")
PROFILE=$(getValueFromSettings "PROFILE")
USER_NAME=$(getValueFromSettings "USER_NAME")
dcCOMMON_SHARED_DIR=$(dcCOMMON_SHARED_DIR)

# get the aws configure stuff from the bootstrap location in the shared directory
if [[ -z "${dcCOMMON_SHARED_DIR}" ]]; then
    if [[ ! -d "${dcCOMMON_SHARED_DIR}" ]]; then
        # It is not there so give  an exit message as we can't go on from here
        echo "ERROR: It does not look like you have run the initial bootstrap script."
        echo "       Contact a devops.center engineer to learn how to correct this."
        exit 1
    fi
fi

CUR_DIR=$(pwd)

#-------------------------------------------------------------------------------
# need to check to see if aws and jq have been loaded and if not install them
#-------------------------------------------------------------------------------
CHECK_AWS=$(which aws)
if [[ ! ${CHECK_AWS} ]]; then
    echo 
    echo "The devops.center scripts will use the AWS cli commands to access AWS."
    echo "The command 'aws' does not appear to be installed on your machine."
    echo "Note that the aws cli is installed via the python installation process"
    echo "called: pip.  This requires python to be installed with version 2.7+."
    echo "(python version 2.7+ is what the devops.center scripts use)"
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
# if using AWS get the region for the instances
#-------------------------------------------------------------------------------
echo 
echo "Enter the region that the cloud instances will be in when they are created."
echo "This value can be obtained from the main authentication user if it is not known. "
echo "(The value is typically us-west-2 or us-east-1.)"
echo 

# check to see if we have a default value
if [[ ${REGION} ]]; then
    read -i ${REGION} -p "Enter the region and press [ENTER]: " -e region
else
    read -i us-west-2  -p "Enter the region and press [ENTER]: " -e region
fi

if [[ -z ${region} ]]; then
    REGION=us-west-2
else
    REGION=${region,,}
fi

#-------------------------------------------------------------------------------
# now we need to get the bootstrap aws config and credentials to be able to set
# up the IAM user
#-------------------------------------------------------------------------------
bootstrapAWSConfigs

#-------------------------------------------------------------------------------
# need to help them run through setting up the IAM user for this user and use 
# the AccessKey and SecretKey that is created specifically for this user to be 
# used in the aws configure setup. 
#-------------------------------------------------------------------------------
determineProfile
setupIAMUser

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
# run aws configure with the appropriate information gathered so far
#-------------------------------------------------------------------------------
runAWSConfigure

#-------------------------------------------------------------------------------
# we have collected all the information we need now write it out to .dcConfig/settings
#-------------------------------------------------------------------------------
writeToSettings

#-------------------------------------------------------------------------------
# Now is the time to remove the bootstrap section from the .aws/{config|credentials}
# this will leave the config and credentials with the PROFILE specifc information and
# their specific credentials in the ~/.aws/ config files.
#-------------------------------------------------------------------------------
cleanUpAWSConfigs

#-------------------------------------------------------------------------------
# and now move back to the original directory this script was started in
#-------------------------------------------------------------------------------
cd ${CUR_DIR}
