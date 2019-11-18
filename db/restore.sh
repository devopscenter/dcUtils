#!/usr/bin/env bash
#===============================================================================
#
#          FILE: restore.sh
# 
#         USAGE: ./restore.sh 
# 
#   DESCRIPTION: This script will put the postgresql database in a state that will
#                allow it to receive the restore of data from a backup of the prod
#                database. It is expected that the backup file is already downloaded
#                and ready to be restored.  See the download.sh to pull an existing
#                backup from S3.  By default it will look for the backup file to be
#                in the current directory or it can be identified by using the
#                --backup option.  There is one argument that is required and that 
#                is the database name.
#
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Original author unknown
#       AUTHOR2: Gregg Jensen (), gjensen@devops.center
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 09/20/2016 12:48:37
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

BACKUP_DIR='.'

function usage
{
  echo "usage: ./restore.sh [--schema-only] [--backup local-backup-filename] [--num num-concurrent-ops] database-name"
}

if [[ -z $1 ]]; then
  usage
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    --schema-only ) SCHEMA_ONLY=1
                    ;;
    --backup )      shift
                    LOCAL_BACKUP_FILE=$1
                    ;;
    --num )         shift
                    NUM_CONCURRENT=$1
                    ;;
    [!-]* )         if [[ $# -eq 1 ]]; then
                      DB_NAME=$1
                    else
                      echo "Too many/few of the 1 required parameters."
                      usage
                      exit 1
                    fi
                    ;;
    * )             usage
                    exit 1
  esac
  shift
done


#-------------------------------------------------------------------------------
# First check to see if the database exists
#-------------------------------------------------------------------------------
DB_EXISTS=$(sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -c ${DB_NAME} )

if [[ ${DB_EXISTS} -ne 0 ]]; then
    #-------------------------------------------------------------------------------
    # kill any existing connections, then drop and recreate the db
    # note for the following sections, due to an issue with the database not being ready
    # at various times after the dropdb, there is a loop around each of the commands. 
    # This loop will ensure the action takes place at least one and if the return value
    # is an error than try again after a brief pause.
    #-------------------------------------------------------------------------------
    for value in {1..3}
    do
        sudo -u postgres psql -U postgres -d "$DB_NAME" -c "select pg_terminate_backend(pg_stat_activity.pid) from pg_stat_activity where pg_stat_activity.datname = '${DB_NAME}' and pid <> pg_backend_pid();"
        if [ $? -gt 0 ]
        then 
            if [ $value -eq 3 ] 
            then
                echo "Terminating because pg_terminate_backend failed to execute properly"
                exit 1
            else 
                sleep 1
            fi
        else
            break
        fi
    done

    for value in {1..3}
    do
        echo "Dropping database ${DB_NAME}"
        #sudo -u postgres dropdb -U postgres "${DB_NAME}" --if-exists
        sudo -u postgres dropdb -U postgres "${DB_NAME}"
        if [ $? -gt 0 ]
        then 
            if [ $value -eq 3 ] 
            then
                echo "Terminating because dropdb failed to execute properly"
                exit 1
            else 
                sleep 1
            fi
        else
            break
        fi
    done
fi # end if database exists check

for value in {1..3}
do
    sudo -u postgres psql -U postgres postgres -c "create database $DB_NAME"
    if [ $? -gt 0 ]
    then 
        if [ $value -eq 3 ] 
        then
            echo "Terminating because the create database failed to execute properly"
            exit 1
        else 
            sleep 1
        fi
    else
        break
    fi
done

# turn off archive_mode for the restore and restart postgres
sudo sed -i "s/^\barchive_mode\b[[:blank:]]\+=[[:blank:]]\+\bon\b/archive_mode = off/g" /media/data/postgres/db/pgdata/postgresql.conf
sleep 2
sudo supervisorctl restart postgres

# now lets ensure that the database is up before continuing
IS_READY=1
for tryAttempt in {1..3}
do
    pg_isready -q
    if [ $? -gt 0 ]
    then 
        if [[ ${tryAttempt} -eq 3 ]]; then
            echo "Will try one last time in 5 seconds."
        else
            echo "postgresql does not appear to be up and ready, will try again in 5 seconds "
        fi
        sleep 5
    else
        IS_READY=0
        break
    fi
done

if [[ ${IS_READY} -eq 1 ]]; then
    echo "postgres didn't come up in the time allowed, exitting.  Try this again in a minute or two."
    exit 1
fi

# if no backup file is provided, look for the most recent pgdump file in the backup dir
if [[ -z "$LOCAL_BACKUP_FILE" ]]; then

    echo "Looking for backupfile: ${DB_NAME}* in $(pwd)"
    LOCAL_BACKUP_FILE="$(ls -t ${DB_NAME}*| head -n 1)"
    if [[ -z "$LOCAL_BACKUP_FILE" ]]; then
        echo "No local backup found, exiting."
        exit 1
    fi
fi

# schema-only restore if --schema-only is passed, otherwise do full restore
echo "Postgresql restore of backup: ${LOCAL_BACKUP_FILE} started at " && date
if ! [[ -z "$SCHEMA_ONLY" ]]; then
    sudo -u postgres pg_restore -U postgres -s -j $NUM_CONCURRENT -Fc --dbname="$DB_NAME" "$LOCAL_BACKUP_FILE" || exit 1
    sudo -u postgres pg_restore -U postgres --data-only -t django_migrations -j $NUM_CONCURRENT -Fc --dbname="$DB_NAME" "$LOCAL_BACKUP_FILE"
    sudo psql -U postgres -d "$DB_NAME" -c "SELECT setval('django_migrations_id_seq', COALESCE((SELECT MAX(id)+1 FROM django_migrations), 1), false);"
else
    sudo -u postgres pg_restore -U postgres -j $NUM_CONCURRENT -Fc --dbname="$DB_NAME" "$LOCAL_BACKUP_FILE"
fi

# turn on archive_mode after restore is complete and restart postgres
sudo sed -i "s/^\barchive_mode\b[[:blank:]]\+=[[:blank:]]\+\boff\b/archive_mode = on/g" /media/data/postgres/db/pgdata/postgresql.conf
sleep 2
sudo supervisorctl restart postgres
echo "Postgresql restore completed at " && date
