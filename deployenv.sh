#!/usr/bin/env bash
#===============================================================================
#
#          FILE: deployenv.sh
#
#         USAGE: ./deployenv.sh  --type TYPE --env ENV --appName CUSTAPPNAME
#
#
#   DESCRIPTION: Establish the ENV vars for the current deployment.
#                  TYPE = { instance | docker }
#                  ENV = { local | dev | staging | prod | ... }
#
#         Assumes that PWD = devops.center utils home directory
#
#         Creates ENV settings in this order:
#           environments/common.env                 <- common for all deployments
#           $BASE_CUSTOMER_DIR/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_UTILS}/environments/$ENV.env       <- per-stage
#           $BASE_CUSTOMER_DIR/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_UTILS}/environments/personal.env   <- local overrides
#
#           For instance deployments, two results:
#             - appends to the instance-wide /etc/environments
#             - appends to /etc/default/supervisor, for everything run via supervisor
#
#           For docker deployments, two results:
#             - creates a docker-appName-env.env, for use by all containers
#             - creates a docker-appName-env.sh, to be sourced by the scripts
#
#       OPTIONS:
#                  TYPE = { instance | docker }
#                  ENV = { local | dev | staging | prod | ... }
#                  BASE_CUSTOMER_DIR = customer specific appName directory
#
#  REQUIREMENTS:
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/15/2016 12:45:11
#      REVISION:  ---
#
# Copyright 2014-2017 devops.center llc
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


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
    echo -e "Usage: deployenv.sh --type TYPE --env ENV --appName CUSTOMER_APP_NAME "
    echo -e "                    [--workspaceName WORKSPACENAME] [--run-as alternateName]"
    echo
    echo -e "This script will set up the environment with the appropriate paths and names"
    echo -e "that will be used by other utilities and scripts within the devops.center"
    echo -e "framework. "
    echo -e "If the option to --type is left off then the default is that the target of"
    echo -e "deploying the environment will be to the file local to the appUtils directory"
    echo -e "and can be used by subsequent utilites and scripts within the devops.center"
    echo -e "framework. If the option to --type is instance (usually only done by another"
    echo -e "script) than the environment will update the appropriate system environment"
    echo -e "files such that when the user re-enters at the login prompt, the environment"
    echo -e "variables for the application will be available."
    echo
    echo -e "--type is either left blank for normal operation or will be given 'instance'"
    echo -e " when called from within another script already in the devops.center framework."
    echo 
    echo -e "--env is one of the environments that is being targeted to execute,"
    echo -e "and corresponds to which environment variable file will be used. "
    echo -e "It is one of: local|dev|staging|prod"
    echo
    echo -e "--appName is the application name that you wish to configure the "
    echo -e "environment for"
    echo
    echo -e "--workspaceName is the optional workspace name that can be used if"
    echo -e "your environment uses alternate workspaces for applications"
    echo 
    echo    "--run-as this option allows the user to run the local containers with variables that "
    echo    "         the user wants to alter to make the environment appear different "
    echo    "         (ie, run it with staging variables rather then dev to see how it would run"
    echo    "         when it is defiined to run as the staging environment.)"
    echo    "         This will look for a personal environment file that has the form:"
    echo    "         personal_alternanteName.env"
    echo    "         and is in the same app-utils/environments/ directory as the personal.env file."
    echo 
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  fixUpFile
#   DESCRIPTION:  function to strip comments and blank lines and then call an
#                 external python script to remove duplicate keys leaving the most
#                 relevent key/value pair as the one in the file
#    PARAMETERS: the tmpFile that will be massaged
#       RETURNS: nothing but will update the original file with no spaces, comments
#                or duplicates
#-------------------------------------------------------------------------------
function fixUpFile
{
    tmpFile=$1
    tmpFile2=$1.2
    if [[ -f ${tmpFile2} ]]; then
        rm ${tmpFile2}
    fi

    # get rid of comments and blank lines
    grep -v '^#' ${tmpFile} | grep -v '^$' > ${tmpFile2}

    # and move the new file to the original file
    if [[ $? -eq 0 ]]; then
        mv ${tmpFile2} ${tmpFile}
    fi

    # execute a python script to remove duplicates.  If there are duplicates it will
    # leave the last key/value as the latest key/value to use
    ${dcUTILS}/scripts/fixUpEnvFile.py --inputFile ${tmpFile} --outputFile ${tmpFile2}

    mv ${tmpFile2} ${tmpFile}

    grep -q "dcDEFAULT_APP_NAME=__DEFAULT__" ${tmpFile}

    if [[ $? -ne 1 ]]; then
        dcLog "... The dcDEFAULT_APP_NAME was still default...changing"
        sed -e "s/dcDEFAULT_APP_NAME=__DEFAULT__/dcDEFAULT_APP_NAME=${CUSTOMER_APP_NAME}/"  ${tmpFile}  > ${tmpFile2}
        mv ${tmpFile2} ${tmpFile}
    fi
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  collectEnvFiles
#   DESCRIPTION:  This will collect all the instance-###.env files found in 
#                 $HOME/.dcConfig and combine them into one instance.env file.
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
collectEnvFiles()
{
    OUTFILE="${HOME}/.dcConfig/instance.env"

    # first remove an old one if it's there
    if [[ -f ${OUTFILE} ]]; then
        rm  ${OUTFILE}
    fi

    # now loop through all the files named instance-*.env and put them into 
    # the one instance.env
    cd $HOME/.dcConfig

    for file in instance-*.env
    do
        while IFS= read -r aLine
        do
            echo ${aLine} >> $OUTFILE
        done < ${file}
    done
}

#-------------------------------------------------------------------------------
# Loop through the arguments and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
if [[ $1 == '-h' ]]; then
    usage
    exit 1
fi

# basic defaults
TYPE="docker"
ENV="local"

# set up the environment
NEW=${@}" --generateEnvFiles"

# now handle the arguemnts for this script
while [[ $# -gt 0 ]]; do
    case $1 in
      --type )    shift
                  TYPE=$1
                  ;;
      --appName|-a )    shift
                        CUSTOMER_APP_NAME=$1
                  ;;
      --env|-e )        shift
                        ENV=$1
                  ;;
      --run-as )         shift
                        RUN_AS=$1 
                  ;;
    esac
    shift
done

if [[ $TYPE != "instance" ]]; then
    #-------------------------------------------------------------------------------

    envToSource="$(${dcUTILS}/scripts/process_dc_env.py ${NEW})"

    if [[ $? -ne 0 ]]; then
        echo $envToSource
        exit 1
    else
        eval "$envToSource"
    fi
else
    source /usr/local/bin/dcEnv.sh
fi

dcStartLog "Deploying for application: ${CUSTOMER_APP_NAME} env: ${ENV}"
#-------------------------------------------------------------------------------
# handle the case where the type is an instance
#-------------------------------------------------------------------------------
if [[ $TYPE == "instance" ]]; then

    dcLog "Deploying for type: instance"
    # TODO look into the destination files below and see what would need to be done about
    # duplicate key/value pairs.  See if this would benefit from the same kind of
    # processing that the docker (ie, the else of the TYPE if check) section has.


    # backup the /etc/environment so that we don't keep duplicating items past the very first time
    # that we run deployenv.sh on an instance.  That is, the very first time we run this on a 
    # newly created instance it will take whatever is in file and save it, so that can be the
    # first thing put in after we remove it.
    if [[ ! -f /etc/environment.ORIG ]]; then
        sudo cp /etc/environment /etc/environment.ORIG
    fi

    # remove the /etc/environment file so we start from a known point each time
    sudo rm /etc/environment
    cat /etc/environment.ORIG | sudo tee -a  /etc/environment

    # first thing is to put the dcUTILS variable/path into the /etc/environment before we continue
    dcUTILS=~/dcUtils
    echo "dcUTILS=~/dcUtils" | sudo tee -a /etc/environment

    dcLog "combining common.env"
    # Add common env vars to instance environment file
    cat ${dcUTILS}/environments/common.env | sudo tee -a  /etc/environment

    # TODO determine if this is required and/or would it need to be put in some other file
    # get the Customer specific utils and web dir and put it in the file
    # or is this just needed for running the application in a docker container
    #dcLog "BASE_CUSTOMER_DIR=${BASE_CUSTOMER_DIR}"  >> ${TEMP_FILE}
    #dcLog "CUSTOMER_APP_UTILS=${CUSTOMER_APP_UTILS}"  >> ${TEMP_FILE}
    #dcLog "CUSTOMER_APP_WEB=${CUSTOMER_APP_WEB}" >> ${TEMP_FILE}

    dcLog "... instance.env into global environment file if available"
    # instance.env has the tags for this instance that will be made to be environment variables
    if [[ -e ${HOME}/.dcConfig/instance.env ]]; then
        collectEnvFiles
        cat ${HOME}/.dcConfig/instance.env | sudo tee -a /etc/environment
    fi

    dcLog "... common.env into global environment file"
    # only bring in the common.env if one exists for the environment and if not there
    # check the base environments directory as a last resort (in case they have only one)
    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/common.env ]]; then
        cat ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/common.env | sudo tee -a /etc/environment
    fi

    dcLog "... ${ENV}.env"
    # Add env vars for this environment, if it exists
    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env ]]; then
        cat ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env | sudo tee -a /etc/environment
    fi

    dcLog "... and configuring supervisor config file"
    # Add the environment variables to the Supervisor, when started by init.d
    if [[ -e "/etc/default/supervisor" ]]; then
        # if it exists it needs to be removed so that we don't keep adding to it.
        # TODO if there is something in this file after the install and before we run this then we need to do the
        # same steps for this file as was done by environment above
        sed -e 's/^/export /'  ${dcUTILS}/environments/common.env | sudo tee  /etc/default/supervisor
    else
        sed -e 's/^/export /'  ${dcUTILS}/environments/common.env | sudo tee -a /etc/default/supervisor
    fi

    if [[ -e ${HOME}/.dcConfig/instance.env ]]; then
        sed -e 's/^/export /' ${HOME}/.dcConfig/instance.env | sudo tee -a /etc/default/supervisor
    fi

    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/common.env ]]; then
        sed -e 's/^/export /' ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/common.env | sudo tee -a /etc/default/supervisor
    fi

    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env ]]; then
        sed -e 's/^/export /' ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env | sudo tee -a /etc/default/supervisor
    fi

    # put the /etc/environment in the current env for this session...normally would have to log out and log in to get it.
    while IFS='' read -r line || [[ -n "${line}" ]]
    do
        if [[ "${line}" && "${line}" != "#"* ]]; then
            export "${line}"
        fi
    done < /etc/environment

    dcLog "ENV vars for '${ENV}' added to /etc/environment and /etc/default/supervisor"
    dcLog "Completed successfully"


#-------------------------------------------------------------------------------
#  The else case is that the type is docker for a local docker deploy
#-------------------------------------------------------------------------------
else
    dcLog "Deploying for type: docker"
    #-------------------------------------------------------------------------------
    # the flow of what will happen is that each of the env files will be pulled together
    # in one file (ie, ./.tmp-local.env).  Then the next step is to read that file, ignore
    # comments and blank lines and create a hash of key/value pairs.  By going in order
    # through the file and duplicate keys will overwrite the value with the latest value.
    # Effectively getting rid of any duplicates.  Next take this file and generate the
    # two docker-appname-env.{env|sh} files.  And then with the last step all that is left
    # is to create a symbolic link to the docker-current.{env|sh} files.
    # The docker-current.env file will be used by the docker-compose up script and any
    # devops.center script will read in the docker-current.sh
    #-------------------------------------------------------------------------------
    BASE_CUSTOMER_APP_UTILS_DIR="${BASE_CUSTOMER_DIR}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_UTILS}"

    #-------------------------------------------------------------------------------
    # copy the health_checks template to the appropriate place for the  application
    # if it doesn't already exist
    #-------------------------------------------------------------------------------
    if [[ ! -f ${BASE_CUSTOMER_APP_UTILS_DIR}/config/health_checks ]]; then
        cp ${dcUTILS}/templates/health_checks ${BASE_CUSTOMER_APP_UTILS_DIR}/config/health_checks
    fi

    # next set up the devops.center common env.
    dcLog "combining global common.env"
    TEMP_FILE="${dcUTILS}/.tmp-local.env"
    cp ${dcUTILS}/environments/common.env ${TEMP_FILE}

    # get the Customer specific utils and web dir and put it in the file
    echo "BASE_CUSTOMER_DIR=${BASE_CUSTOMER_DIR}"  >> ${TEMP_FILE}
    echo "CUSTOMER_APP_UTILS=${CUSTOMER_APP_UTILS}"  >> ${TEMP_FILE}
    echo "CUSTOMER_APP_WEB=${CUSTOMER_APP_WEB}" >> ${TEMP_FILE}
    echo "CUSTOMER_APP_ENV=${ENV}" >> ${TEMP_FILE}

    dcLog "... application common.env "
    # only bring in the personal.env if one exists for the environment and if not there
    # check the base environments directory as a last resort (in case they have only one)
    if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/common.env ]]; then
        cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/common.env >> ${TEMP_FILE}
    fi

    if [[ "${ENV}" == "local" ]]; then
        dcLog "... ${ENV}.env"
        if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/${ENV}.env ]]; then
            cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/${ENV}.env >> ${TEMP_FILE}
        fi

        dcLog "... personal.env into a single file"
        # only bring in the personal.env if one exists for the environment and if not there
        # check the base environments directory as a last resort (in case they have only one)
        #
        # An add on here is the ability to run the local containers with environment variables
        # that you want to be different then the default local enviornment.  This will allow
        # the user to test out variables like they may be set as in different environments.
        # This is specific to the personal.env file in that whatever string the person provides
        # for the option of runAs will be in the structure: personal_FLOOBAR.env (ie an underscore
        # in front followed by the standard .env at the end)
        if [[ -z ${RUN_AS} ]]; then
            # it is run as normal
            if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal.env ]]; then
                cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal.env >> ${TEMP_FILE}
            fi
        else
            # it is run with the extra tag they provided so use that file
            if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal_${RUN_AS}.env ]]; then
                cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal_${RUN_AS}.env >> ${TEMP_FILE}
            else
                dcLog "NOTE: Looking for ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal_${RUN_AS}.env "
                dcLog " and it does NOT exist!! Exiting."
                exit 1
            fi
        fi
    else
        dcLog "... ${ENV}.env into a single file"
        if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/${ENV}.env ]]; then
            cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/${ENV}.env >> ${TEMP_FILE}
        fi
    fi

    dcLog "... cleaning file to get rid of duplicates"
    # only bring in the personal.env if one exists for the environment and if not there
    # now read in the ./.tmp-local.env file and remove comments/spaces and duplicates
    # and create the new files with appname and env.  Then create the links and finally
    # remove the temporary working file
    fixUpFile ${TEMP_FILE}

    # Now create the links
    dcLog "... creating final files"
    if [[ -f ${TEMP_FILE} ]]; then
        TARGET_ENV_FILE="${BASE_CUSTOMER_APP_UTILS_DIR}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-${ENV}.env"
        mv ${TEMP_FILE} ${TARGET_ENV_FILE}
    else
        dcLog -e "ERROR: the creation of the environments file was not successful."
        dcLog -e "       Uncomment the "set -x" at the top of the file and re-run."
        dcLog -e "       Capture the output and send to devops.center via slack or"
        dcLog -e "       email."
        exit 1
    fi

    # Create a script to initialize the local shell
    TARGET_SH_FILE="${BASE_CUSTOMER_APP_UTILS_DIR}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-${ENV}.sh"
    sed -e 's/^/export /'  ${TARGET_ENV_FILE} > ${TARGET_SH_FILE}

    dcLog "Completed successfully"
    # TODO need to figure out how to get the users keys so that "paws" will work
    # probably need another script to manage them (ie, manageKeys.py)

    #dcLog "ENV vars for '${ENV}' added to docker-current.env for use by docker compose"
    #dcLog "ENV vars for '${ENV}' used to create docker-current.sh for use in local shell"
fi
dcEndLog "Finished..."
