#!/bin/bash -
#===============================================================================
#
#          FILE: checkForDevopsCenterEnv.sh
#
#         USAGE: ./checkForDevopsCenterEnv.sh
#
#   DESCRIPTION: This script will ensure that there is an environment file that
#                is set and can be utilized for the running of this session.  The
#                intent of this script is that it would be put at the top of all
#                devops.center scripts to ensure that the environment variables
#                that are needed will be available to the script.  This is done
#                to help avoid polluting the users environment. Another main
#                purpose of this is to be able to isolate sessions such that a
#                user could run one app in terminal session and a second one in
#                parallel in a separate terminal session while using the same
#                code.
#
#       OPTIONS: --customerAppName appName
#                Where appName is the current app that the user wants to use
#                This is optional and if not given will take the appName from
#                the DEFAULT_APP_NAME from the environment file.
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/17/2016 09:43:52
#      REVISION:  ---
#===============================================================================

#set -o nounset      # Treat unset variables as an error
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
    echo -e "Usage: process-dc-env.sh [--customerAppName appName] [--env theEnv]"
    echo
    echo -e "--customerAppName is the name of the application that you want to"
    echo -e "run as the default app for the current session.  This is optional"
    echo -e "as by default the appName will be set when deployenv.sh is run"
    echo -e "--env theEnv is one of local, dev, staging, prod"
    echo 
    exit 1
}


#-------------------------------------------------------------------------------
# lets check to see if dcUtils has been set already if not then we are probably
# the first time through and it hasn't been set in the environment, so we assume
# we are in the directory
#-------------------------------------------------------------------------------
dcUTILS=${dcUTILS:-"."}

#-------------------------------------------------------------------------------
# Loop through the argument(s) and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
CUSTOMER_APP_NAME=""
ENV=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --customerAppName|--customerappname )    shift
                  CUSTOMER_APP_NAME=$1
                  ;;
    --env )    shift
                  ENV=$1
                    ;;
    * )           usage
                  exit 1
  esac
  shift
done



#-------------------------------------------------------------------------------
# First we need to get the base location of the customers files.  This was created
# when the manageApp.py was run as one of the arguments is the directory and it 
# should be an absolute path
#-------------------------------------------------------------------------------
if [[ -f ~/.devops.center/config ]]; then
    source ~/.devops.center/config
else
    echo -e "Can not read the config file in ~/.devops.center, have you run manageApp.py"
    echo -e "yet? "
    exit 1
fi


#-------------------------------------------------------------------------------
# now we need to get the appName(s) that are in the base directory.  If there is just
# one, than we use it and move on.  If there is only one and it doesn't match the
# customerAppName (if one is passed in) then stop and tell them they need to re-run
# manageApp.py because the appName doesn't exist.
# If there is more than one, and none of them match the customerAppName passed in then
# we have to print out the fact and then exit forcing the user to choose one or they
# have to run manageApp.py creating the app they want
#-------------------------------------------------------------------------------
declare -a appArray
FILES_TO_FIND="${BASE_CUSTOMER_DIR}"
a=0
while read line
do
    appArray[ $a ]="$line"
    a=$((a+1))
done < <(ls ${FILES_TO_FIND} 2>/dev/null)

if [[ ${#appArray[@]} -eq 0 ]]; then
    echo -e "There are no applications defined in the base directory: ${BASE_CUSTOMER_DIR}"
    echo -e "This would be defined in the ~/devops.center/config file and points to the"
    echo -e "base directory where the applications to be used with the devops.center"
    echo -e "framework are located.  This is initialized by running manageApp.py."
    echo -e "See the documentation for further initialization instructions."
    exit 1
fi

if [[ ${#appArray[@]} -eq 1 ]]; then
    BASE_APP_NAME=${appArray[0]}
    if [[ ! -z ${CUSTOMER_APP_NAME} ]]; then
        if [[ ${CUSTOMER_APP_NAME} != ${appArray[0]} ]]; then
            echo -e "The appName you provided: ${CUSTOMER_APP_NAME} was not been found"
            echo -e "in the base directory: ${BASE_CUSTOMER_DIR}"
            exit 1
        fi
    fi

fi

if [[ ${#appArray[@]} -gt 1 ]]; then
    if [[ ! -z ${CUSTOMER_APP_NAME} ]]; then
        flag=0
        for filename in ${appArray[@]} ; do
            if [[ ${filename} == ${CUSTOMER_APP_NAME} ]]; then
                flag=1
                BASE_APP_NAME=${CUSTOMER_APP_NAME}
                break
            fi
        done
        if [[ $flag -eq 0 ]]; then
            echo -e "The appName you provided: ${CUSTOMER_APP_NAME} was not been found"
            echo -e "in the base directory: ${BASE_CUSTOMER_DIR}"
            exit 1
        fi
    else
        echo -e "found multiple applications so you will need to provide the appropriate"
        echo -e "option (usually --customerAppName) for this script to be able to pass"
        echo -e "the application name."
        echo -e "The applications found are:"
        echo
        for filename in ${appArray[@]} ; do
            echo ${filename}
        done
        echo
        exit 1
    fi
fi

BASE_APP_UTILS="${BASE_CUSTOMER_DIR}/${BASE_APP_NAME}/$BASE_APP_NAME-utils"
#echo ${BASE_CUSTOMER_DIR}
#echo ${BASE_APP_NAME}
#echo ${BASE_APP_UTILS}

#-------------------------------------------------------------------------------
# Need to find what dcEnv files that are in the directory.  We need to get the
# possible appNames if there is more than one.  And then get any environment
# (ie, dev, staging, prod, local) files if there are more than one.
# If it doesn't exist exit and instruct the user to run deployenv.sh
#-------------------------------------------------------------------------------
# check for a dcEnv-${CUSTOMER_APP_NAME}-*.sh file
FILES_TO_FIND="${BASE_APP_UTILS}/environments/.generatedEnvFiles/dcEnv-*.sh"
declare -a array
i=0
while read line
do
    array[ $i ]="$line"
    i=$((i+1))
done < <(ls ${FILES_TO_FIND} 2>/dev/null)

# if one doesn't exist instruct the user to run deployenv.sh with that app
# name and try this again and then exit
if [[ ${#array[@]} -eq 0 ]]; then
    echo -e "There does not appear to be any env files available."
    echo -e "You will need to create one by executing the deployenv.sh"
    echo -e "with the appName"
    echo
    exit 1
fi

if [[ ! -z  ${CUSTOMER_APP_NAME} ]]; then
    # check for a dcEnv-${CUSTOMER_APP_NAME}-*.sh file
    FILES_TO_FIND="${BASE_APP_UTILS}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-*.sh"
    declare -a array
    i=0
    while read line
    do
        array[ $i ]="$line"
        i=$((i+1))
    done < <(ls ${FILES_TO_FIND} 2>/dev/null)

    # if one doesn't exist instruct the user to run deployenv.sh with that app
    # name and try this again and then exit
    if [[ ${#array[@]} -eq 0 ]]; then
        echo -e "There does not appear to be any env files available with the."
        echo -e "given appName: ${CUSTOMER_APP_NAME}"
        echo -e "You will need to create it by executing the deployenv.sh"
        echo -e "with the appName"
        echo
        exit 1
    fi

    if [[  ${#array[@]} -gt 1 ]]; then
        if [[ ! -z $ENV ]]; then
            # go through the loop of files and see if one is has the ENV
            i=1
            for filename in ${array[@]} ; do
                FILE_TO_COMPARE=$(basename ${filename})
                if [[ ${FILE_TO_COMPARE} == *$ENV* ]]; then
                    ENV_FILE_TO_READ="${filename}"
                    NEW_ENV_APP_FILE_TO_USE=${filename/%.sh/.env}
                    break
                fi
                i=$((i+1))
            done
        else
            # if there is more than one file (ie, different ENVs) then display the list
            # and ask for the user to select one.
            echo -e "There are multiple sets of environment files with that appName."
            echo -e "The difference between the files is the environment portion.  This"
            echo -e "is one of local, dev, staging or prod.  Look at the list below and"
            echo -e "you will need to know the environment that you want to run in."
            echo -e "Re-run this script and give the appropriate option to desiginate"
            echo -e "the env (usually --env) and provide the environment string."
            echo -e "The env files found are:"
            echo
            for filename in ${array[@]} ; do
                FILE_TO_DISPLAY=$(basename ${filename})
                echo "${FILE_TO_DISPLAY}"
            done
            exit 1
        fi
    else
        NEW_ENV_APP_FILE_TO_USE=${array[0]/%.sh/.env}
        ENV_FILE_TO_READ=${array[0]}
    fi
else
    if [[  ${#array[@]} -gt 1 ]]; then
        if [[ ! -z $ENV ]]; then
            # go through the loop of files and see if one is has the ENV
            i=1
            for filename in ${array[@]} ; do
                FILE_TO_COMPARE=$(basename ${filename})
                if [[ ${FILE_TO_COMPARE} == *$ENV* ]]; then
                    ENV_FILE_TO_READ=${filename}
                    NEW_ENV_APP_FILE_TO_USE=${filename/%.sh/.env}
                    break
                fi
                i=$((i+1))
            done
        else
            # if there is more than one file (ie, different ENVs) then display the list
            # and ask for the user to select one.
            echo -e "There are multiple sets of environment files with that appName."
            echo -e "The difference between the files is the environment portion.  This"
            echo -e "is one of local, dev, staging or prod.  Look at the list below and"
            echo -e "you will need to know the environment that you want to run in."
            echo -e "Re-run this script and give the appropriate option to desiginate"
            echo -e "the env (usually --env) and provide the environment string."
            echo -e "The env files found are:"
            echo
            for filename in ${array[@]} ; do
                FILE_TO_DISPLAY=$(basename ${filename})
                echo "${FILE_TO_DISPLAY}"
            done
            exit 1
        fi
    else
        # replace the .sh with .env at the end of the string
        NEW_ENV_APP_FILE_TO_USE=${array[0]/%.sh/.env}
        ENV_FILE_TO_READ="${array[0]}"
    fi
fi


#-------------------------------------------------------------------------------
# source the environment variables
#-------------------------------------------------------------------------------
source ${ENV_FILE_TO_READ}

#-------------------------------------------------------------------------------
# check for the DEFAULT_APP_NAME. If not given set it to the appname from the
# input.  If the --customerAppName is not given then check the one from the
# env and make sure it is not the __DEFAULT__ one.
#-------------------------------------------------------------------------------
if [[ ${dcDEFAULT_APP_NAME} == "__DEFAULT__" ]]; then
    echo -e "The dcDEFAULT_APP_NAME environment variable has not been set and has"
    echo -e "not been made available. This should be identified when running"
    echo -e "deployenv.sh by utilizing the option: "
    echo -e "--customerAppDir customerUtilsDir/appname"
    exit 1
fi
