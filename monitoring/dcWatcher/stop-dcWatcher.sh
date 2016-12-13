#!/bin/bash - 
#===============================================================================
#
#          FILE: stop-dcWatcher.sh
# 
#         USAGE: ./stop-dcWatcher.sh 
# 
#   DESCRIPTION: kill the watchmedo processes that were started by the dcWatcher.py.
#                It will read the dcWatcher.pids file and use the pids found in that 
#                file to kill the processes.  It will then remove the pids file to 
#                be ready for the next time it dcWatcher.py is run
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Gregg Jensen (), gjensen@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/02/2016 09:42:10
#      REVISION:  ---
#===============================================================================

dcWATCHER_PID_FILE="./.dcWatcher.pids"
if [ -f ${dcWATCHER_PID_FILE} ]; then
    kill `cat ${dcWATCHER_PID_FILE}` > /dev/null 2>&1
    rm ${dcWATCHER_PID_FILE}
fi
