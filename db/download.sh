#!/usr/bin/env bash
#===============================================================================
#
#          FILE: download.sh
# 
#         USAGE: ./download.sh 
# 
#   DESCRIPTION: This script will allow the user to download a database backup
#                from AWS S3 storage.  You can get a list of the backups by
#                providing the --list option and it will display a list of the
#                backups with the most recent one last. There are four columes
#                to the list output, date, time, size of backup, and the name.
#                you can copy the name and add it as the --s3backupfile option
#                or you can leave off that option and just provide the s3bucket
#                and database name.  This will go through that list and automatically
#                get the lastest one and down load it.
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 04/20/2017 11:33:18
#      REVISION:  ---
#===============================================================================

#set -o nounset       # Treat unset variables as an error
#set -x               # essentially debug mode


BACKUP_DIR='.'

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  prints out the options for the script
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
function usage
{
  echo "usage: ./download.sh [--s3backupfile s3-backup-file] [--list] [-n] [--profile theProfile] s3bucket database"
  echo
  echo "you might need to use the --profile option if you do not have the AWS credentials set up in either your"
  echo "environment or the standard aws config and credentials files."
  echo
  echo "By running with the --list option it is easier to see the existing backup files along with their size and date"
  echo "and then selecting from the list."
}

if [[ -z $1 ]]; then
  usage
  exit 1
fi


while [[ $# -gt 0 ]]; do
  case $1 in
    --s3backupfile ) shift
                     S3_BACKUP_FILE=$1
                     ;;
    --list )         LIST=1
                     ;;
    --profile|-p )   shift
                     PROFILE=$1
                     ;;
    -n )             NO_OVERWRITE=1
                     ;;
    [!-]* )          if [[ $# -eq 2 ]]; then
                       S3_BUCKET=$1
                       DB_NAME=$2
                       shift;
                     else
                       echo "Too many/few of the 2 required parameters."
                       usage
                       exit 1
                     fi
                     ;;
    * )              usage
                     exit 1
  esac
  shift
done

#-------------------------------------------------------------------------------
# store list of backups from s3 bucket
#-------------------------------------------------------------------------------
if [[ -z ${PROFILE} ]]; then
    S3_AS_STRING=$(aws s3 ls --recursive s3://"${S3_BUCKET}"/|grep "${DB_NAME}".sql.gz)
else
    S3_AS_STRING=$(aws --profile ${PROFILE} s3 ls --recursive s3://"${S3_BUCKET}"/|grep "${DB_NAME}".sql.gz)
fi
S3_SORTED_AS_STRING=$(echo "${S3_AS_STRING}" | sort)
IFS=$'\n'; S3_LIST=($S3_SORTED_AS_STRING); unset IFS;

# make sure there is something found, otherwise exit
if [[ ${#S3_LIST[@]} -eq 0 ]]; then
    echo "NOTE: There were no backups found...exiting"
    exit
fi


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  convertSize
#   DESCRIPTION:  takes a raw file size and gives a more human readable output
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
convertSize() {
    b=${1:-0}; d=''; s=0; S=(Bytes {K,M,G,T,E,P,Y,Z}iB)
    while ((b > 1024)); do
        d="$(printf ".%02d" $((b % 1024 * 100 / 1024)))"
        b=$((b / 1024))
        let s++
    done
    echo "$b$d ${S[$s]}"
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  showNumberedList
#   DESCRIPTION:  shows the list as a numbered list and asks the user if they 
#                 want to choose one from the list to download
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
showNumberedList() {
    echo "S3 backups, with most recent listed last"
    i=1
    for line in "${S3_LIST[@]}"
    do
        dbLine=${line##* }
        aSize=$(echo $line | cut -d " " -f 3)
        theSize=$(convertSize aSize)
        echo "{$i}.[$theSize] ${dbLine}"
        i=$((i+1))
    done
}
#-------------------------------------------------------------------------------
# if --list is specified, print list and exit
#-------------------------------------------------------------------------------
if ! [[ -z "$LIST" ]]; then

    showNumberedList
    echo -n "Enter the number of the backup you want to download or press return to quit "
    read -r number

    if [[ -z ${number} ]]; then
        exit
    else
        indexNum=$((number-1))
        selectedLine=${S3_LIST[$indexNum]}
        S3_BACKUP_FILE=${selectedLine##* }
    fi
fi

#-------------------------------------------------------------------------------
# if the backup file name is given, download the specified file otherwise get it 
# from the list as the latest one 
#-------------------------------------------------------------------------------
if [[ -z "$S3_BACKUP_FILE" ]]; then
    # download the most recent
    selectedLine=${S3_LIST[-1]}
    S3_BACKUP_FILE=${selectedLine##* }
fi

#-------------------------------------------------------------------------------
# save off, from the end, everything up the last slash to get just the database backup name
#-------------------------------------------------------------------------------
JUST_THE_BACKUP_NAME=${S3_BACKUP_FILE##*/}
LOCAL_BACKUP_FILE="${BACKUP_DIR}/${JUST_THE_BACKUP_NAME}"

if [[ -f "$LOCAL_BACKUP_FILE" ]] && ! [[ -z "$NO_OVERWRITE" ]]; then
    echo -e "\nFile $LOCAL_BACKUP_FILE already exists and -n option was given. Skipping."
else
    echo "Getting the backup file: ${S3_BACKUP_FILE} from the s3bucket: ${S3_BUCKET}"
    sudo -u postgres aws s3 cp "s3://${S3_BUCKET}/${S3_BACKUP_FILE}" "$LOCAL_BACKUP_FILE"
fi
export LOCAL_BACKUP_FILE

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
