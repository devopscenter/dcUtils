#!/usr/bin/env bash
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
#                Bob Lozano (), bob@devops.center
#  ORGANIZATION: devops.center
#       CREATED: 11/02/2016 09:42:10
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

dcWATCHER_PID_FILE="./.dcWatcher.pids"
if [ -f ${dcWATCHER_PID_FILE} ]; then
    kill `cat ${dcWATCHER_PID_FILE}` > /dev/null 2>&1
    rm ${dcWATCHER_PID_FILE}
fi
