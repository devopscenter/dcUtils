#!/bin/bash -
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
#                Assumes that PWD = devops.center utils home directory
#
#                Creates ENV settings in this order:
#                  environments/common.env                 <- common for all deployments
#                  $BASE_CUSTOMER_DIR/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_UTILS}/environments/$ENV.env       <- per-stage
#                  $BASE_CUSTOMER_DIR/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_UTILS}/environments/personal.env   <- local overrides
#
#                For instance deployments, two results:
#                  - appends to the instance-wide /etc/environments
#                  - appends to /etc/default/supervisor, for everything run via supervisor
#
#                For docker deployments, two results:
#                  - creates a docker-appName-env.env, for use by all containers
#                  - creates a docker-appName-env.sh, to be sourced by the scripts
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
#  ORGANIZATION: devops.center
#       CREATED: 11/15/2016 12:45:11
#      REVISION:  ---
#===============================================================================

#set -o nounset     # Treat unset variables as an error
#set -o errexit      # exit immediately if command exits with a non-zero status
#set -x             # essentially debug mode

# set up the dcUTILS to point to this directory
dcUTILS="."

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:
#       RETURNS:
#-------------------------------------------------------------------------------
function usage
{
#    dcProcessEnv=$(${dcUTILS}/scripts/process_dc_env.py -h)
#    echo ${dcProcessEnv}
    echo -e "Usage: deployenv.sh --type TYPE --env ENV --appName CUSTOMER_APP_NAME [--workspaceName WORKSPACENAME]"
    echo
    echo -e "--type is one of: instance|docker. Where instance implies that the code will"
    echo -e "run in an AWS instance and docker implies it will run on a local docker "
    echo -e "container probably used for local development"
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
    ./scripts/fixUpEnvFile.py --inputFile ${tmpFile} --outputFile ${tmpFile2}

    mv ${tmpFile2} ${tmpFile}

    grep -q "dcDEFAULT_APP_NAME=__DEFAULT__" ${tmpFile}

    if [[ $? -ne 1 ]]; then
        echo "It was still default...changing"
        sed -e "s/dcDEFAULT_APP_NAME=__DEFAULT__/dcDEFAULT_APP_NAME=${CUSTOMER_APP_NAME}/"  ${tmpFile}  > ${tmpFile2}
        mv ${tmpFile2} ${tmpFile}
    fi
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
      --env )     shift
                  ENV=$1
                  ;;
    esac
    shift
done

if [[ $TYPE != "instance" ]]; then
    #-------------------------------------------------------------------------------

    envToSource=$(${dcUTILS}/scripts/process_dc_env.py ${NEW})

    if [[ $? -ne 0 ]]; then
        echo $envToSource
        exit 1
    else
        eval $envToSource
    fi
fi

#-------------------------------------------------------------------------------
# handle the case where the type is an instance
#-------------------------------------------------------------------------------
if [[ $TYPE = "instance" ]]; then

    echo "Deploying for type: instance"
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

    echo -n "combining common.env"
    # Add common env vars to instance environment file
    cat environments/common.env | sudo tee -a  /etc/environment

    # TODO determine if this is required and/or would it need to be put in some other file
    # get the Customer specific utils and web dir and put it in the file
    # or is this just needed for running the application in a docker container
    #echo "BASE_CUSTOMER_DIR=${BASE_CUSTOMER_DIR}"  >> ${TEMP_FILE}
    #echo "CUSTOMER_APP_UTILS=${CUSTOMER_APP_UTILS}"  >> ${TEMP_FILE}
    #echo "CUSTOMER_APP_WEB=${CUSTOMER_APP_WEB}" >> ${TEMP_FILE}

    echo -n "...${ENV}.env"
    # Add env vars for this environment, if it exists
    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env ]]; then
        cat ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env | sudo tee -a /etc/environment
    fi

    echo -n "...personal.env into global environment file"
    # only bring in the personal.env if one exists for the environment and if not there
    # check the base environments directory as a last resort (in case they have only one)
    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/personal.env ]]; then
        cat ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/personal.env | sudo tee -a /etc/environment
    fi

    echo "...and configuring supervisor config file"
    # Add the environment variables to the Supervisor, when started by init.d
    if [[ -e "/etc/default/supervisor" ]]; then
        sed -e 's/^/export /'  environments/common.env | sudo tee -a /etc/default/supervisor
    else
        sed -e 's/^/export /'  environments/common.env | sudo tee  /etc/default/supervisor
    fi

    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env ]]; then
        sed -e 's/^/export /' ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/${ENV}.env | sudo tee -a /etc/default/supervisor
    fi

    if [[ -e ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/personal.env ]]; then
        sed -e 's/^/export /' ${HOME}/${CUSTOMER_APP_NAME}/${CUSTOMER_APP_NAME}-utils/environments/personal.env | sudo tee -a /etc/default/supervisor
    fi

    # put the /etc/environment in the current env for this session...normally would have to log out and log in to get it.
    while IFS='' read -r line || [[ -n "${line}" ]]
    do
        if [[ "${line}" && "${line}" != "#"* ]]; then
            export "${line}"
        fi
    done < /etc/environment

    echo "ENV vars for '${ENV}' added to /etc/environment and /etc/default/supervisor"
    echo "Completed successfully"


#-------------------------------------------------------------------------------
#  The else case is that the type is docker for a local docker deploy
#-------------------------------------------------------------------------------
else
    echo "Deploying for type: docker"
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
        cp templates/health_checks ${BASE_CUSTOMER_APP_UTILS_DIR}/config/health_checks
    fi

    # next set up the devops.center common env.
    echo -n "combining common.env"
    TEMP_FILE="./.tmp-local.env"
    cp environments/common.env ${TEMP_FILE}

    # get the Customer specific utils and web dir and put it in the file
    echo "BASE_CUSTOMER_DIR=${BASE_CUSTOMER_DIR}"  >> ${TEMP_FILE}
    echo "CUSTOMER_APP_UTILS=${CUSTOMER_APP_UTILS}"  >> ${TEMP_FILE}
    echo "CUSTOMER_APP_WEB=${CUSTOMER_APP_WEB}" >> ${TEMP_FILE}
    echo "CUSTOMER_APP_ENV=${ENV}" >> ${TEMP_FILE}

    echo -n "...${ENV}.env"
    if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/${ENV}.env ]]; then
        cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/${ENV}.env >> ${TEMP_FILE}
    fi

    echo -n "...personal.env into a single file"
    # only bring in the personal.env if one exists for the environment and if not there
    # check the base environments directory as a last resort (in case they have only one)
    if [[ -e ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal.env ]]; then
        cat ${BASE_CUSTOMER_APP_UTILS_DIR}/environments/personal.env >> ${TEMP_FILE}
    fi

    echo -n "...cleaning file to get rid of duplicates"
    # only bring in the personal.env if one exists for the environment and if not there
    # now read in the ./.tmp-local.env file and remove comments/spaces and duplicates
    # and create the new files with appname and env.  Then create the links and finally
    # remove the temporary working file
    fixUpFile ${TEMP_FILE}

    # Now create the links
    echo "...creating final files"
    if [[ -f ${TEMP_FILE} ]]; then
        TARGET_ENV_FILE="${BASE_CUSTOMER_APP_UTILS_DIR}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-${ENV}.env"
        mv ${TEMP_FILE} ${TARGET_ENV_FILE}
    else
        echo -e "ERROR: the creation of the environments file was not successful."
        echo -e "       Uncomment the "set -x" at the top of the file and re-run."
        echo -e "       Capture the output and send to devops.center via slack or"
        echo -e "       email."
        exit 1
    fi

    # Create a script to initialize the local shell
    TARGET_SH_FILE="${BASE_CUSTOMER_APP_UTILS_DIR}/environments/.generatedEnvFiles/dcEnv-${CUSTOMER_APP_NAME}-${ENV}.sh"
    sed -e 's/^/export /'  ${TARGET_ENV_FILE} > ${TARGET_SH_FILE}

    echo "Completed successfully"
    # TODO need to figure out how to get the users keys so that "paws" will work
    # probably need another script to manage them (ie, manageKeys.py)

    #echo "ENV vars for '${ENV}' added to docker-current.env for use by docker compose"
    #echo "ENV vars for '${ENV}' used to create docker-current.sh for use in local shell"
fi
