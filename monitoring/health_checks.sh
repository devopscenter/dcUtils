#!/bin/bash - 
#===============================================================================
#
#          FILE: health_checks.sh
# 
#         USAGE: ./health_checks.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/21/2016 14:01:20
#      REVISION:  ---
#===============================================================================

#set -o nounset                 # Treat unset variables as an error
#set -x                         # set debug mode

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
function usage
{
    echo -e "usage: ./health_checks.sh --customerAppName CUSTOMER_APP_Name\n"
    echo -e "--customerAppDir is the name of the application that you want to"
    echo -e "run as the default app for the current session.  This is optional"
    echo -e "as by default the appName will be set when deployenv.sh is run"
    echo -e "--env theEnv is one of local, dev, staging, prod"
    echo 
    echo -e "Examples:"
    echo -e "Health checks for client1:"
    echo -e "    ./health_checks.sh appName\n"
    echo -e "Notes:"
    echo -e "Requires installation of https://github.com/devopscenter/paws, "
    echo -e "an accompanying .aws/credentials profile, and a config directory and file in the "
    echo -e "customers diretory for a given appName.  The file will need to contain the following"
    echo -e "items to perform the checks:"
    echo -e "  process_check:           PROCESS='<process name>'"
    echo -e "  s3_check:                S3_BUCKETS='<s3 bucket>/<hostname> <s3 bucket>/<hostname>'"
    echo -e "  azure_check:             AZURE_HOSTS=( '<hostname> <azure container>' '<hostname> <azure container>' )"
    echo -e "  primary_secondary_check: PRIMARY_SECONDARIES=( '<master hostname> <follower private ip>' '<master hostname> <follower private ip>' )\n"
}

#-------------------------------------------------------------------------------
# Loop through the arguments and assign input args with the appropriate variables
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

echo "Checking environment..."
if [[ -z ${CUSTOMER_APP_NAME} ]]; then
    if [[ -z ${ENV} ]]; then
        . ./scripts/process-dc-env.sh
    else
        . ./scripts/process-dc-env.sh --env ${ENV}
    fi
else
    if [[ -z ${ENV} ]]; then
        . ./scripts/process-dc-env.sh --customerAppName ${CUSTOMER_APP_NAME}
    else
        . ./scripts/process-dc-env.sh --customerAppName ${CUSTOMER_APP_NAME} --env ${ENV}
    fi
fi

# read the client specific health_checks config file.  Note this is a different file
# than the customer/appName env file.
source "${BASE_CUSTOMER_DIR}/${dcDEFAULT_APP_NAME}/${CUSTOMER_APP_UTILS}/config/health_checks"

# generate string used to search for the timestamps from the past 7 days
for i in $(seq 1 7); do
    DATE_RANGE="${DATE_RANGE}\|$(date -v-${i}d '+%Y-%m-%d')"
done


#-------------------------------------------------------------------------------
# checks file for a reboots required message
#-------------------------------------------------------------------------------
function security_check
{
    SECURITY_COMMAND=$1
    SECURITY_FILTER=$2
    SECURITY_CRITICAL=()

    SECURITY_OUTPUT=$(paws -p "$CUSTOMER_APP_NAME" "$SECURITY_COMMAND" 2>/dev/null)
    while read -r line; do
        if [[ "$(echo -e "$line"|eval "$SECURITY_FILTER")" ]]; then
            SECURITY_CRITICAL=("${SECURITY_CRITICAL[@]}" "$(echo -e "$line")")
        fi
    done < <(echo -e "$SECURITY_OUTPUT")

    printf "Instances needing to be restarted for security updates.\n"
    printf "  %s\n" "${SECURITY_CRITICAL[@]}"|sort
    printf "\n"
}

#-------------------------------------------------------------------------------
# compares results of command to 2 thresholds, critical and warning
#-------------------------------------------------------------------------------
function threshold_check
{
    THRESHOLD_TYPE=$1
    THRESHOLD_COMMAND=$2
    THRESHOLD_FILTER=$3
    CRITICAL_LEVEL=$4
    WARNING_LEVEL=$5
    THRESHOLD_CRITICAL=()
    THRESHOLD_WARNING=()

    CHECK_OUTPUT=$(paws -p "$CUSTOMER_APP_NAME" "$THRESHOLD_COMMAND" 2>/dev/null)
    while read -r line; do
        HOST_VALUE="$(echo "$line"|awk '{ printf $1 }')"
        CHECK_RESULT="$(echo "$line"|eval "$THRESHOLD_FILTER")"
        if [[ $(echo "$CHECK_RESULT > $CRITICAL_LEVEL"|bc 2>/dev/null) -eq 1 ]]; then
            THRESHOLD_CRITICAL=("${THRESHOLD_CRITICAL[@]}" "$(echo "$HOST_VALUE $CHECK_RESULT")")
        elif [[ $(echo "$CHECK_RESULT > $WARNING_LEVEL"|bc 2>/dev/null) -eq 1 ]]; then
            THRESHOLD_WARNING=("${THRESHOLD_WARNING[@]}" "$(echo "$HOST_VALUE $CHECK_RESULT")")
        fi
    done < <(echo -e "$CHECK_OUTPUT")

    printf "Instances with $THRESHOLD_TYPE usage above ${CRITICAL_LEVEL}%%:\n"
    if [[ "${THRESHOLD_CRITICAL}" ]]; then
        printf "  %s\n" "${THRESHOLD_CRITICAL[@]}"|sort
    fi
    printf "Instances with $THRESHOLD_TYPE usage above ${WARNING_LEVEL}%%:\n"
    if [[ "${THRESHOLD_WARNING}" ]]; then
        printf "  %s\n" "${THRESHOLD_WARNING[@]}"|sort
    fi
    printf "\n"
}

#-------------------------------------------------------------------------------
# checks for a process in the output of the ps command
#-------------------------------------------------------------------------------
function process_check
{
    PROCESS=$1
    PROCESS_HOSTS=$2
    PROCESS_ARRAY=()
    PROCESS_PAWS=''
    PROCESS_CRITICAL=()

    for i in $PROCESS_HOSTS; do
        PROCESS_PAWS="${PROCESS_PAWS}${i},"
        PROCESS_ARRAY=("${PROCESS_ARRAY[@]}" "$i")
    done
    # trim off trailing comma
    PROCESS_PAWS="$(echo $PROCESS_PAWS|sed 's/,$//')"

    PROCESS_OUTPUT=$(paws -p "$CUSTOMER_APP_NAME" -w "$PROCESS_PAWS" "ps aux|grep -i ${PROCESS}|grep -v grep" 2>/dev/null)

    for i in "${PROCESS_ARRAY[@]}"; do
        if ! [[ $(echo "$PROCESS_OUTPUT"|grep "$i") ]]; then
            PROCESS_CRITICAL=("${PROCESS_CRITICAL[@]}" "$(echo -e "${i}")")
        fi
    done

    printf "Instances where $PROCESS is not running:\n"
    if [[ "${PROCESS_CRITICAL}" ]]; then
        printf "  %s\n" "${PROCESS_CRITICAL[@]}"|sort
    fi
    printf "\n"
}

#-------------------------------------------------------------------------------
# checks for a secondary host list in the output of a specified command run on the primary hosts and verify a specified status
#-------------------------------------------------------------------------------
function primary_secondary_check
{
    PRIMARY_SECONDARY_TYPE=$1
    PRIMARY_SECONDARY_COMMAND=$2
    PRIMARY_SECONDARY_FILTER=$3
    PRIMARY_SECONDARY_COMPARISON=$4
    PRIMARY_SECONDARY_CONTEXT=$5
    PRIMARY_SECONDARY_PAWS=''
    PRIMARY_SECONDARY_CRITICAL=()
    PRIMARY_HOST=''
    SECONDARY_HOSTS=''
    PRIMARY_ARRAY=()
    SECONDARY_ARRAY=()

    for i in "${PRIMARY_SECONDARY_PAIRS[@]}"; do
        PRIMARY_HOST=$(echo "$i"|awk '{print $1}')
        SECONDARY_HOSTS=$(echo "$i"|awk '{for (j=2; j<NF; j++) printf $j " "; print $NF}')

        PRIMARY_ARRAY=("${PRIMARY_ARRAY[@]}" "$PRIMARY_HOST")
        for i in "$SECONDARY_HOSTS"; do
            SECONDARY_ARRAY=("${SECONDARY_ARRAY[@]}" "$i")
        done

        PRIMARY_SECONDARY_PAWS="${PRIMARY_SECONDARY_PAWS}${PRIMARY_HOST},"
    done

    # trim off trailing comma
    PRIMARY_SECONDARY_PAWS="$(echo $PRIMARY_SECONDARY_PAWS|sed 's/,$//')"

    PRIMARY_SECONDARY_OUTPUT=$(paws -p "$CUSTOMER_APP_NAME" -w "$PRIMARY_SECONDARY_PAWS" "$PRIMARY_SECONDARY_COMMAND" 2>/dev/null)

    # check for primary array having a matching secondary array
    if [[ "${#PRIMARY_ARRAY[@]}" != "${#SECONDARY_ARRAY[@]}" ]]; then
        PRIMARY_SECONDARY_CRITICAL=("${PRIMARY_SECONDARY_CRITICAL[@]}"
            "$(echo "Error: Primary and secondary arrays must be the same size.")")
    else
        for (( i=0; i<"${#PRIMARY_ARRAY[@]}"; i++ )); do
            # check for output from the primary instance
            if ! [[ $(echo "$PRIMARY_SECONDARY_OUTPUT"|grep "${PRIMARY_ARRAY[$i]}") ]]; then
                PRIMARY_SECONDARY_CRITICAL=("${PRIMARY_SECONDARY_CRITICAL[@]}" "$(echo "${i}: $PRIMARY_SECONDARY_COMMAND has failed!")")
            else
                for j in ${SECONDARY_ARRAY[$i]}; do
                    # check for the secondary IP from output on the primary
                    if ! [[ $(echo "$PRIMARY_SECONDARY_OUTPUT"|grep "${PRIMARY_ARRAY[$i]}"|grep "$j") ]]; then
                        PRIMARY_SECONDARY_CRITICAL=("${PRIMARY_SECONDARY_CRITICAL[@]}" 
                            "$(echo "${PRIMARY_ARRAY[$i]}: $PRIMARY_SECONDARY_COMMAND shows no ${j}!")")
                    else
                        # check for the proper status for the secondary on the primary
                        #if [[ $(echo "$PRIMARY_SECONDARY_OUTPUT"|grep "${PRIMARY_ARRAY[$i]}"|grep "$j"|eval "$PRIMARY_SECONDARY_FILTER") != "$PRIMARY_SECONDARY_COMPARISON" ]]; then
                        PRIMARY_FILTER=$(echo "$PRIMARY_SECONDARY_OUTPUT"|grep "${PRIMARY_ARRAY[$i]}"|grep "$j"|eval "$PRIMARY_SECONDARY_FILTER")
                        if [[ ${PRIMARY_FILTER} != "$PRIMARY_SECONDARY_COMPARISON" ]]; then
                            PRIMARY_SECONDARY_CRITICAL=("${PRIMARY_SECONDARY_CRITICAL[@]}"
                                 "$(echo "${PRIMARY_ARRAY[$i]}: $PRIMARY_SECONDARY_COMMAND shows defective ${j}!")")
                            if [[ "$PRIMARY_SECONDARY_CONTEXT" ]]; then
                                PRIMARY_SECONDARY_CRITICAL=("${PRIMARY_SECONDARY_CRITICAL[@]}"
                                    "$(echo "${PRIMARY_SECONDARY_OUTPUT}"|grep "${PRIMARY_ARRAY[$i]}"|grep "$PRIMARY_SECONDARY_CONTEXT")")
                            fi
                            PRIMARY_SECONDARY_CRITICAL=("${PRIMARY_SECONDARY_CRITICAL[@]}" "$(echo "${PRIMARY_SECONDARY_OUTPUT}"|grep "${PRIMARY_ARRAY[$i]}"|grep "$j")")
                        fi
                    fi
                done
            fi
        done
    fi

    printf "Instances with missing or non-working ${PRIMARY_SECONDARY_TYPE}:\n"
    if [[ "${PRIMARY_SECONDARY_CRITICAL}" ]]; then
        printf "  %s\n" "${PRIMARY_SECONDARY_CRITICAL[@]}"|sort
    fi
    printf "\n"
}

#-------------------------------------------------------------------------------
# check s3 buckets for files from the last 7 days
#-------------------------------------------------------------------------------
function s3_check
{
    S3_BUCKETS=$1
    S3_ARRAY=()
    S3_CRITICAL=()

    for i in $S3_BUCKETS; do
        S3_ARRAY=("${S3_ARRAY[@]}" "$i")
    done

    for i in ${S3_ARRAY[@]}; do
        S3_OUTPUT=$(aws --profile "$CUSTOMER_APP_NAME" s3 ls --recursive "$i" 2>/dev/null)
        if ! [[ $(echo -e "$S3_OUTPUT"|grep "$DATE_RANGE") ]]; then
            S3_CRITICAL=("${S3_CRITICAL[@]}" "$(echo -e "$i")")
        fi
    done

    printf "Instances without recent backups:\n"
    if [[ "${S3_CRITICAL}" ]]; then
        printf "  %s\n" "${S3_CRITICAL[@]}"|sort
    fi
    printf "\n"
}

#-------------------------------------------------------------------------------
# check azure containers for files from the last 7 days
#-------------------------------------------------------------------------------
function azure_check
{
    AZURE_HOST=''
    AZURE_CONTAINER=''
    AZURE_OUTPUT=''
    AZURE_CRITICAL=()

    for i in "${AZURE_PAIRS[@]}"; do
        AZURE_HOST=$(echo "$i"|awk '{print $1}')
        AZURE_CONTAINER=$(echo "$i"|awk '{print $2}')

        AZURE_OUTPUT=$(paws -p "$CUSTOMER_APP_NAME" -w "$AZURE_HOST" "cd ~/azure-tools && ./azure-download.sh -l ${AZURE_CONTAINER}" 2>/dev/null)

        if ! [[ $(echo -e "$AZURE_OUTPUT"|grep "$DATE_RANGE") ]]; then
            AZURE_CRITICAL=("${AZURE_CRITICAL[@]}" "$(echo -e "$AZURE_HOST")")
        fi
    done

    printf "Instances without recent backups:\n"
    if [[ "${AZURE_CRITICAL}" ]]; then
        printf "  %s\n" "${AZURE_CRITICAL[@]}"|sort
    fi
    printf "\n"
}


#-------------------------------------------------------------------------------
# Checks run for all instances, no entries in the customer specific config files are necessary.
#-------------------------------------------------------------------------------
echo -e "##### ALL INSTANCES #####"

#-------------------------------------------------------------------------------
# Takes 2 arguments, the check command and a filter that it gets piped to.
#-------------------------------------------------------------------------------
security_check 'cat /var/run/reboot-required' 'grep required'


#-------------------------------------------------------------------------------
# Takes 5 arguments, the type of check (purely for output display), the check command, 
# a filter the command is piped to, a critical threshold, and a warning threshold.
#-------------------------------------------------------------------------------
threshold_check 'CPU' 'uptime' "awk '{ for (i=NF; i>0; i--) printf(\"%s \", \$i); printf (\"\n\") }'|awk '{print \$2}'|tr -d ," '90' '80'
threshold_check 'MEMORY' 'free' 'grep "buffers/cache"|awk '"'"'{print $4/($4+$5)*100}'"'"'' '90' '80'
threshold_check 'INODE' 'df -ih' 'grep "/dev/xvd"|awk '"'"'{print $6}'"'"'|tr -d %' '90' '80'
threshold_check 'DISK' 'df -h' 'grep "/dev/xvd"|awk '"'"'{print $6}'"'"'|tr -d %' '90' '80'

# set the PRIMARY_SECONDARY_PAIRS variable to one in the customer specific config file, if it exists
if [[ "$PGPOOL_BACKENDS_HOSTS" ]]; then
    echo -e "##### PGPOOL-BACKENDS #####"
    PRIMARY_SECONDARY_PAIRS=("${PGPOOL_BACKENDS_HOSTS[@]}")
    # Takes 5 arguments, the type of check (purely for output display), the check command, 
    # a filter the command is piped to, the expected value to compare the filtered output against,
    # and a value to grep for when the check fails that can be added to displayed output for additional context. 
    primary_secondary_check 'pgpool backends' '/usr/bin/psql -h "/var/run/postgresql/" -p 5432 -U postgres -c "show pool_nodes"' 'awk '"'"'{print $8}'"'"'' '2' 'node'
fi

# set the PRIMARY_SECONDARY_PAIRS variable to one in the customer specific config file, if it exists
if [[ "$MASTER_FOLLOWERS_HOSTS" ]]; then
    echo -e "##### MASTER-FOLLOWERS #####"
    PRIMARY_SECONDARY_PAIRS=("${MASTER_FOLLOWERS_HOSTS[@]}")
    # Takes 5 arguments, the type of check (purely for output display), the check command,
    # a filter the command is piped to, the expected value to compare the filtered output against,
    # and a value to grep for when the check fails that can be added to displayed output for additional context.
    primary_secondary_check 'postgres followers' 'psql -U postgres -c "SELECT client_addr,state FROM pg_stat_replication;"' 'awk -F\\\| '"'"'{print $2}'"'"'|sed '"'"'s/[[:blank:]]//g'"'"'' 'streaming' 'streaming'
fi


if [[ "$S3_BUCKETS" ]]; then
    echo -e "##### S3 BACKUPS #####"
    # Takes 1 argument, the variable name in a customer specific config file that is a string
    # with space separated bucket names to check for backups from the past 7 days
    s3_check "$S3_BUCKETS"
fi

if [[ "$AZURE_PAIRS" ]]; then
    echo -e "##### AZURE BACKUPS #####"
    # Takes no arguments, runs if a customer specific config file contains the AZURE_PAIRS variable
    # that is an array of strings, which themselves are hostnames, a space, and then the azure container name
    azure_check
fi

if [[ "$DROPBOX_HOSTS" ]]; then
    echo -e "##### DROPBOX #####"
    # Takes 2 arguments, the type of check (purely for output display), the variable name in a
    # customer specific config file that is a string with space separated hostnames to check for the
    # running process
    process_check 'dropbox' "$DROPBOX_HOSTS"
fi

if [[ "$FLOWER_HOSTS" ]]; then
    echo -e "##### FLOWER #####"
    # Takes 2 arguments, the type of check (purely for output display), the variable name in a
    # customer specific config file that is a string with space separated hostnames to check for the
    # running process
    process_check 'flower' "$FLOWER_HOSTS"
fi
