#!/bin/bash - 
#===============================================================================
#
#          FILE: drop-index.sh
# 
#         USAGE: ./drop-index.sh 
# 
#   DESCRIPTION: customer appName specific that will drop the indexes identified
#                by the CREATE INDEX lines in the customer appname .sql file
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/21/2016 15:13:37
#      REVISION:  ---
#===============================================================================

#set -o nounset                              # Treat unset variables as an error

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  usage
#   DESCRIPTION:  function that gets called to show the user how this script should
#                 be called and what the arguments mean
#    PARAMETERS:  
#       RETURNS:  
#-------------------------------------------------------------------------------
function usage
{
    echo -e "usage: ./drop-index.sh --customerAppDir CUSTOMER_APP_DIR\n"
    echo -e "--customerAppDir is the path to the customer specific directory including"
    echo -e "the appName that contains the config directory where the health_checks"
    echo -e "config file resides."
    echo 
}
#-------------------------------------------------------------------------------
# Loop through the arguments and assign input args with the appropriate variables
#-------------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case $1 in
      --customerAppDir|--customerappdir )    shift
                  CUSTOMER_APP_DIR=$1
                  ;;
      * )           usage
                  exit 1
    esac
    shift
done

if [[ -d ${CUSTOMER_APP_DIR} ]]; then
    CUSTOMER_APP_NAME=$(basename ${CUSTOMER_APP_DIR})
else
    CUSTOMER_APP_NAME="default"
fi

# TODO determine if this script needs to be updated for further inclusion
# in this utils repository
cd /topopps/web/topopps-web
python manage.py sqlall api > topopps.sql
rm dropindex.sql
grep 'CREATE INDEX' topopps.sql | grep like | awk '{print $3}' |
while read line; do
echo "DROP INDEX $line;" >> dropindex.sql
done

psql -U postgres -f dropindex.sql topopps
